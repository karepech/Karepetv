import requests
import re
import concurrent.futures
import random
import urllib3
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Matikan peringatan SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ====================================================================
# I. KONFIGURASI GLOBAL
# ====================================================================

MASTER_URLS = [
    "https://gist.githubusercontent.com/zentral-qtrung/531720c17d089702dd7ac4b96db6e1ce/raw/91a8ccd82ef831df356bc53b6a7f621a9ba913f4/sports.m3u",
    "https://raw.githubusercontent.com/jrpahe-del/IPTV/refs/heads/main/RafaDervian.m3u", 
    "https://raw.githubusercontent.com/Bluestraveller13/super-duper-spork/refs/heads/main/KITKATJOSS", 
    "https://deccotech.online/tv/tvstream.html",
    "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25",
    "https://semar25.short.gy",
    "https://freeiptv2026.tsender57.workers.dev",
    "https://raw.githubusercontent.com/tsender57-dotcom/iptv-rox-playlist/refs/heads/main/rakettv.m3u8",
    "https://bit.ly/KPL203"
]

# Kata kunci untuk membaca group-title dari penyedia asli (Metode Top-Down)
GROUP_KEYWORDS = {
    "SPORTS": ["SPORT", "SPORTS", "OLAHRAGA", "MATCH", "LIGA", "BEIN", "LIVE EVENT", "BALL"],
    "KIDS": ["KIDS", "ANAK", "CARTOON", "KARTUN", "ANIMATION"],
    "RELIGI": ["RELIGI", "ISLAM", "MUSLIM", "ROHANI", "DAKWAH", "NGAJI", "SUNNAH"],
    "NEWS": ["NEWS", "BERITA", "INFORMASI"],
    "KNOWLEDGE": ["KNOWLEDGE", "EDUCATION", "EDUKASI", "DISCOVERY", "HISTORY", "SCIENCE", "WILD"],
    "INDONESIA": ["INDONESIA", "NASIONAL", "LOKAL", "DAERAH", "TV NASIONAL"]
}

GLOBAL_BLACKLIST_URLS = {
    "https://bit.ly/428RaFW",
    "https://iili.io/KfT7PJ2.jpg",
    "https://drive.google.com/uc?export=download&id=12slpj4XW5B5SlR9lruuZ77_NPtTHKKw8&usp",
    "https://shorter.me/SNozg",
    "https://mimipipi22.github.io/logo/offline.m3u8",
    "https://dn720407.ca.archive.org/0/items/warkop-dki-mana-tahan/Warkop%20DKI%20-%20Mana%20Tahan.mp4",
}

# Mapping output ke nama file M3U awal (agar tetap sama)
OUTPUT_FILE_MAPPING = {
    "event_combined.m3u": ["SEDANG TAYANG", "AKAN TAYANG"],
    "sports_combined.m3u": ["SPORTS"],
    "indonesia_combined.m3u": ["INDONESIA", "LOKAL TV"],
    "kids_combined.m3u": ["KIDS"],
    "knowledge_combined.m3u": ["KNOWLEDGE"],
    "news_combined.m3u": ["NEWS"],
    "religi_combined.m3u": ["RELIGI"]
}

# Regex
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)
CLEANING_REGEX = re.compile(r'[^a-zA-Z0-9\s]+')
TIME_PATTERN_REGEX = re.compile(r'\b(?:[01]?[0-9]|2[0-3])[:.][0-5][0-9]\s*(?:WIB|WITA|WIT)?\b', re.IGNORECASE)
SPAM_KEYWORDS = ['EXTVLCOPT', 'USER-AGENT', 'GECKO', 'CHROME', 'SAFARI', 'WINK', 'MOZILLA', 'APPLEWEBKIT', 'HTTP']

# ====================================================================
# II. FUNGSI UTAMA MESIN SEDOT & PENGELOMPOKAN
# ====================================================================

def get_ott_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "VLC/3.0.18 LibVLC/3.0.18",
        "TiviMate/4.7.0 (Android)"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "*/*",
        "Connection": "keep-alive"
    }

def download_playlist(args):
    idx, url = args
    print(f"  > Sedang menyedot dari: {url}")
    channels = []
    try:
        session = requests.Session()
        retry_strategy = Retry(total=2, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        response = session.get(url, headers=get_ott_headers(), timeout=(15, 60), verify=False)
        response.raise_for_status()
        
        text_data = response.text.replace('<br>', '\n').replace('<br/>', '\n')
        
        # Ganti logo lama ke logo baru
        url_logo_lama = "https://raw.githubusercontent.com/tsender57-dotcom/offline/refs/heads/main/logo/Logo%20OGI%20Bone.png"
        url_logo_baru = "https://raw.githubusercontent.com/karepech/bakul/refs/heads/main/bw.png" 
        text_data = text_data.replace(url_logo_lama, url_logo_baru)
        
        current_buffer = []  
        current_extinf = ""  
        
        for line in text_data.splitlines():
            line = line.strip()
            if not line: continue
            if line.startswith("#EXTM3U"): continue
            
            if line.startswith("#"):
                current_buffer.append(line)
                if line.startswith("#EXTINF"):
                    current_extinf = line
                    
            elif len(line) > 5 and line.lower().startswith("http"): 
                if current_buffer and current_extinf:
                    channels.append({
                        "buffer": current_buffer,
                        "extinf": current_extinf,
                        "url": line
                    })
                current_buffer = []
                current_extinf = ""
                
        return idx, url, channels
    except Exception as e:
        print(f"  > WARNING: Gagal memproses {url}.")
        return idx, url, []

def process_and_categorize(super_clean_channels):
    print("\n[+] Memulai proses Klasifikasi Cerdas (Top-Down by Group Title)...")
    
    categorized_data = {
        "SEDANG TAYANG": [],
        "AKAN TAYANG": [],
        "SPORTS": [],
        "LOKAL TV": [],
        "INDONESIA": [],
        "KIDS": [],
        "KNOWLEDGE": [],
        "NEWS": [],
        "RELIGI": [],
        "LAINNYA": []
    }
    
    seen_urls = set()

    for ch in super_clean_channels:
        stream_url = ch["url"]
        if stream_url in seen_urls: continue
        
        current_extinf = ch["extinf"]
        current_buffer = list(ch["buffer"])
        
        group_match = GROUP_TITLE_REGEX.search(current_extinf)
        raw_group_title = group_match.group(1).upper() if group_match else "UNGROUPED"
        
        if "," in current_extinf:
            raw_channel_name = current_extinf.split(',', 1)[1].strip()
        else:
            raw_channel_name = current_extinf.strip()
            
        clean_channel_name = CLEANING_REGEX.sub(' ', raw_channel_name).upper()
        
        if any(spam in clean_channel_name for spam in SPAM_KEYWORDS):
            continue

        # ====================================================================
        # ATURAN 1: PENGKODEAN NAMA (beIN Sports Varian)
        # ====================================================================
        if "BEIN" in clean_channel_name:
            if "AU" in clean_channel_name or "AUSTRALIA" in clean_channel_name:
                raw_channel_name = raw_channel_name.replace("beIN", "beIN AU")
            elif "ID" in clean_channel_name or "INDONESIA" in clean_channel_name:
                raw_channel_name = raw_channel_name.replace("beIN", "beIN ID")

        # ====================================================================
        # ATURAN 2: IDENTIFIKASI KATEGORI DASAR DARI PROVIDER
        # ====================================================================
        base_category = "LAINNYA"
        for cat, keywords in GROUP_KEYWORDS.items():
            if any(kw in raw_group_title for kw in keywords):
                base_category = cat
                break
                
        # Fallback jika grup-title tidak jelas tapi nama channel spesifik
        if base_category == "LAINNYA":
            if any(kw in clean_channel_name for kw in GROUP_KEYWORDS["SPORTS"]): base_category = "SPORTS"
            elif any(kw in clean_channel_name for kw in GROUP_KEYWORDS["INDONESIA"]): base_category = "INDONESIA"

        final_category = base_category
        
        # ====================================================================
        # ATURAN 3: LOGIKA LIVE EVENT & JADWAL (Lokal TV vs Sports)
        # ====================================================================
        has_time = bool(TIME_PATTERN_REGEX.search(raw_channel_name))
        is_live_indicator = "LIVE" in raw_group_title or "SEDANG TAYANG" in raw_group_title or "(LIVE)" in raw_channel_name.upper() or "[LIVE]" in raw_channel_name.upper()
        
        sports_event_kws = ["VS", "GRAND PRIX", "LIGA", "MATCH", "SPORT", "CUP", "CHAMPION", "RACE", "MOTOGP", "BADMINTON"]

        if has_time or any(kw in clean_channel_name for kw in ["VS", "GRAND PRIX"]):
            if is_live_indicator:
                final_category = "SEDANG TAYANG"
            else:
                if any(kw in clean_channel_name for kw in sports_event_kws) or base_category == "SPORTS":
                    final_category = "AKAN TAYANG"
                else:
                    final_category = "LOKAL TV"

        # Update `#EXTINF` buffer dengan group-title yang baru & nama channel
        for idx in range(len(current_buffer)):
            b_line = current_buffer[idx]
            if b_line.startswith("#EXTINF"):
                if 'group-title="' in b_line:
                    b_line = re.sub(r'group-title="[^"]*"', f'group-title="{final_category}"', b_line, flags=re.IGNORECASE)
                else:
                    if ',' in b_line:
                        parts = b_line.split(',', 1)
                        b_line = f'{parts[0]} group-title="{final_category}",{parts[1]}'
                    else:
                        b_line = f'{b_line} group-title="{final_category}"'
                
                parts = b_line.split(',', 1)
                if len(parts) == 2:
                    b_line = f"{parts[0]},{raw_channel_name}"
                        
                current_buffer[idx] = b_line
                
            elif b_line.upper().startswith("#EXTGRP:"):
                current_buffer[idx] = f"#EXTGRP:{final_category}"

        categorized_data[final_category].append({
            "buffer": current_buffer,
            "url": stream_url,
            "name": raw_channel_name.upper() # Disimpan untuk sorting
        })
        seen_urls.add(stream_url)

    return categorized_data

# ====================================================================
# III. EKSEKUSI UTAMA
# ====================================================================

if __name__ == "__main__":
    print("=====================================================")
    print("MEMULAI MESIN PENYEDOT IPTV (METODE TOP-DOWN FOLDER)")
    print("=====================================================")
    
    all_providers_data = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(download_playlist, enumerate(MASTER_URLS))
        for idx, url, channels in results:
            if channels:
                all_providers_data.append(channels)
                
    print("\n[+] Membuat Daftar Saluran Super Bersih...")
    
    super_clean_channels = []
    for provider_channels in all_providers_data:
        for ch in provider_channels:
            if ch["url"] not in GLOBAL_BLACKLIST_URLS:
                super_clean_channels.append(ch)
                
    print(f"Total saluran kotor (awal): {len(super_clean_channels)}")
    
    # Memproses semua rules & kategori
    categorized_data = process_and_categorize(super_clean_channels)
    
    print("\n[+] Menyimpan Playlist ke Format File M3U Awal...")
    
    # Proses pencetakan file berdasarkan mapping lama
    for filename, internal_categories in OUTPUT_FILE_MAPPING.items():
        combined_items = []
        for cat in internal_categories:
            combined_items.extend(categorized_data.get(cat, []))
            
        if not combined_items: 
            continue
            
        # Urutkan secara alfabet berdasarkan nama channel
        combined_items.sort(key=lambda x: x["name"])
        
        filtered_lines = ["#EXTM3U"]
        for ch in combined_items:
            filtered_lines.extend(ch["buffer"])
            filtered_lines.append(ch["url"])
            
        with open(filename, "w", encoding="utf-8") as f:
            f.write('\n'.join(filtered_lines) + '\n')
            
        print(f"  -> {filename} berhasil dibuat. (Total: {len(combined_items)} channel)")

    print("\n✅ PROSES SELESAI! Struktur file output M3U sudah kembali seperti format awal Anda.")
