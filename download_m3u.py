import requests
import re
import concurrent.futures
from datetime import datetime

# ====================================================================
# I. KONFIGURASI GLOBAL
# ====================================================================

MASTER_URLS = [
    "https://aspaltvpasti.top/xxx/merah.php",
    "https://deccotech.online/tv/tvstream.html", 
    "https://freeiptv2026.tsender57.workers.dev", 
    "https://raw.githubusercontent.com/tvplaylist/T2/refs/heads/main/tv1",
    "http://sauridigital.my.id/kerbaunakal/2026TVGNS.html",
    "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25",
    "https://semar25.short.gy",
    "https://bit.ly/TVKITKAT",
    "https://liveevent.iptvbonekoe.workers.dev",
    "https://tvg.short.gy/GEULISALLOTT26",
    "https://bit.ly/KPL203"
]

ALL_POSITIVE_KEYWORDS = {
    "EVENT_ONLY": ["EVENT", "SEA GAMES", "PREMIER LEAGUE", "LA LIGA", "SERIE A", "BUNDESLIGA", "LIGUE 1", "EREDIVISIE", "LIGA 1 INDONESIA", "LIGA PRO SAUDI"],
    "SPORTS_LIVE": ["SPORT", "SPORTS", "LIVE", "LANGSUNG", "OLAHRAGA", "MATCH", "LIGA", "FOOTBALL", "BEIN", "SPOTV", "BE IN"],
    "INDONESIA": [
        "INDONESIA", "NASIONAL", "LOKAL", "DAERAH",
        "RCTI", "SCTV", "INDOSIAR", "TRANS", "MNC", "GTV", "GLOBAL TV", 
        "TVRI", "BTV", "JAK TV", "JTV", "RTV", "NET TV", "DAAI"
    ],
    "KIDS": [
        "KIDS", "ANAK", "CARTOON", "KARTUN", "NICKELODEON", "NICK JR", 
        "DISNEY", "CARTOON NETWORK", "BOOMERANG", "BABY", 
        "ANIMATION", "ANIMASI", "TOON", "CERIA", "MENTARI", "YEYA"
    ],
    "KNOWLEDGE": [
        "KNOWLEDGE", "EDUCATION", "EDUKASI", "PENGETAHUAN", "DISCOVERY", 
        "NATIONAL GEOGRAPHIC", "NAT GEO", "NATGEO", "HISTORY", 
        "ANIMAL PLANET", "SCIENCE", "SAINS", "DOCUMENTARY", "DOKUMENTER", "WILD"
    ],
    "NEWS": [
        "NEWS", "BERITA", "INFORMASI", "CNN", "CNBC", "INEWS", 
        "TVONE", "TV ONE", "METRO", "KOMPAS", "AL JAZEERA", "BBC", "CNA", "BLOOMBERG", "CCTV"
    ],
    "RELIGI": [
        "RELIGI", "ISLAM", "MUSLIM", "ROHANI", "DAKWAH", "NGAJI", 
        "SUNNAH", "QURAN", "RODJA", "WESAL", "INSAN", "SURAU", 
        "TVMU", "MTA", "KHAZANAH", "MADINAH", "MAKKAH", "NABAWI", "UMMAT"
    ]
}

GLOBAL_BLACKLIST_URLS = {
    "https://bit.ly/428RaFW",
    "https://iili.io/KfT7PJ2.jpg",
    "https://drive.google.com/uc?export=download&id=12slpj4XW5B5SlR9lruuZ77_NPtTHKKw8&usp",
    "https://shorter.me/SNozg",
    "https://mimipipi22.github.io/logo/offline.m3u8",
    "https://dn720407.ca.archive.org/0/items/warkop-dki-mana-tahan/Warkop%20DKI%20-%20Mana%20Tahan.mp4",
    "https://mantul.biz.id:443/inetwork/gayanet12/19132.ts",
    "http://sauridigital.my.id/infogeulis/JOIN%20GROUP.mp4",
    "https://sauridigital.my.id/infogeulis/DONASI%20DANA.mp4",
    "https://kuk1.modprimus.cfd/kuk3/usergendx0slfk9QssDx9lgxlsdmqrnd.m3u8",
    "https://kuk1.modprimus.cfd/kuk2/usergendx0ul2J8tsDx9lgcddwqrnd.m3u8",
    "https://kudos111.terranovax1.cfd/kuk4/usergendx0thc60skrdnnd.m3u8",
    "https://pulse1.zalmora.cfd/kuk1/usergendx472snx93kdgwqrnd.m3u8",
}

CONFIGURATIONS = [
    {
        "output_file": "event_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"], 
        "category_name": "LIVE EVENT SPORTS", 
        "force_category": True, 
        "require_time": True, 
        "description": "EVENT: Gabungan Event Olahraga (Wajib Berjadwal)"
    },
    {
        "output_file": "sports_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"],
        "category_name": "SPORTS",
        "force_category": True,  
        "require_time": False, 
        "description": "SPORTS: Gabungan Live"
    },
    {
        "output_file": "indonesia_combined.m3u", 
        "keywords": ALL_POSITIVE_KEYWORDS["INDONESIA"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "INDONESIA",
        "force_category": True,
        "require_time": False,
        "description": "INDONESIA: Gabungan TV Indonesia Murni"
    },
    {
        "output_file": "kids_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["KIDS"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "KIDS",
        "force_category": True,
        "require_time": False,
        "description": "KIDS: Gabungan Saluran Anak"
    },
    {
        "output_file": "knowledge_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["KNOWLEDGE"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "KNOWLEDGE",
        "force_category": True,
        "require_time": False,
        "description": "KNOWLEDGE: Gabungan Saluran Edukasi"
    },
    {
        "output_file": "news_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["NEWS"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "NEWS",
        "force_category": True,
        "require_time": False,
        "description": "NEWS: Gabungan Saluran Berita & CCTV"
    },
    {
        "output_file": "religi_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["RELIGI"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "RELIGI",
        "force_category": True,
        "require_time": False,
        "description": "RELIGI: Gabungan Saluran Dakwah & Rohani"
    },
]

# Regex
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)
CLEANING_REGEX = re.compile(r'[^a-zA-Z0-9\s]+')
TIME_PATTERN_REGEX = re.compile(r'\b(?:[01]?[0-9]|2[0-3])[:.][0-5][0-9]\s*WIB\b', re.IGNORECASE)
QUALITY_CLEANER_REGEX = re.compile(r'\b(hd|fhd|uhd|sd|4k|8k|tv|ind|indo|id|my|sg|ch|channel|network|plus|max|raw|hevc|hq)\b', re.IGNORECASE)
SPAM_KEYWORDS = ['EXTVLCOPT', 'USER-AGENT', 'GECKO', 'CHROME', 'SAFARI', 'WINK', 'MOZILLA', 'APPLEWEBKIT', 'HTTP']

CATEGORIZED_URLS = set()

# ====================================================================
# II. FUNGSI UTAMA MESIN SEDOT & FILTERING
# ====================================================================

def contains_time_pattern(text):
    return bool(TIME_PATTERN_REGEX.search(text))

def get_ott_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://www.google.com",
        "Referer": "https://www.google.com/"
    }

def extract_date_from_group(group_title):
    if not group_title:
        return None
    months = {
        'januari': '01', 'jan': '01', 'februari': '02', 'feb': '02',
        'maret': '03', 'mar': '03', 'april': '04', 'apr': '04',
        'mei': '05', 'juni': '06', 'jun': '06',
        'juli': '07', 'jul': '07', 'agustus': '08', 'agu': '08', 'agus': '08',
        'september': '09', 'sep': '09', 'oktober': '10', 'okt': '10',
        'november': '11', 'nov': '11', 'desember': '12', 'des': '12'
    }
    pattern = r'(\d{1,2})\s*(' + '|'.join(months.keys()) + r')'
    match = re.search(pattern, group_title, re.IGNORECASE)
    
    if match:
        day = match.group(1).zfill(2)
        month_str = match.group(2).lower()
        month = months[month_str]
        year = datetime.now().strftime("%y") 
        return f"{day}-{month}-{year}"
    return None

def get_channel_priority(channel_name):
    """
    Fungsi untuk menentukan 'Kasta' channel. 
    Semakin kecil angkanya, semakin tinggi posisinya di daftar.
    """
    n = channel_name.upper()
    if "BEIN" in n: return 1
    if "SPOTV" in n: return 2
    if "DAZN" in n or "ELEVEN" in n: return 3
    if "SUPER" in n and "SPORT" in n or re.search(r'\bSS\b', n): return 4
    if "SKY" in n and "SPORT" in n: return 5
    if "TNT" in n or "BT SPORT" in n: return 6
    if "MNC" in n and "SPORT" in n: return 7
    if "SOCCER CHANNEL" in n or "SPORTSTARS" in n: return 8
    if "CHAMPIONS" in n or "VIDIO" in n: return 9
    if "SSC" in n: return 10
    if "ABU DHABI" in n or "DUBAI" in n: return 11
    if "ASTRO" in n: return 12
    if "TRUE" in n: return 13
    if any(k in n for k in ["EUROSPORT", "FOX", "OPTUS", "SETANTA"]): return 14
    return 99 # Kasta terendah (diurutkan sesuai abjad di bawah)

def download_playlist(url):
    print(f"  > Sedang menyedot dari: {url}")
    channels = []
    try:
        response = requests.get(url, headers=get_ott_headers(), timeout=15, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        current_buffer = []  
        current_extinf = ""  
        
        for raw_line in response.iter_lines():
            if not raw_line: continue
            line = raw_line.decode('utf-8', errors='ignore').strip()
            
            if line.startswith("#EXTM3U"): continue
            
            if line.startswith("#"):
                current_buffer.append(line)
                if line.startswith("#EXTINF"):
                    current_extinf = line
                    
            elif len(line) > 5 and line.lower().startswith("http"): 
                stream_url = line
                if current_buffer and current_extinf:
                    channels.append({
                        "buffer": current_buffer,
                        "extinf": current_extinf,
                        "url": stream_url
                    })
                current_buffer = []
                current_extinf = ""
                
        return url, channels
    except Exception as e:
        print(f"  > WARNING: Gagal memproses {url}. Error: {e}")
        return url, []

def filter_m3u_by_config(config, super_clean_channels):
    output_file = config["output_file"]
    keywords = config["keywords"]
    exclude_keywords = config["exclude_keywords"] 
    target_category = config["category_name"] 
    force_category = config["force_category"]
    require_time = config.get("require_time", False) 
    description = config["description"]

    is_event_category = (target_category == "LIVE EVENT SPORTS")

    print(f"\n--- Memproses [{description}] ---")
    
    channels_data = [] 
    
    for ch in super_clean_channels:
        stream_url = ch["url"]
        
        if stream_url in CATEGORIZED_URLS:
            continue

        current_extinf = ch["extinf"]
        current_buffer = list(ch["buffer"]) 

        group_match = GROUP_TITLE_REGEX.search(current_extinf)
        raw_group_title = group_match.group(1) if group_match else ""
        
        if "," in current_extinf:
            raw_channel_name = current_extinf.split(',', 1)[1].strip()
        else:
            raw_channel_name = current_extinf.strip()
        
        has_time_pattern = contains_time_pattern(raw_channel_name)
        new_channel_name = raw_channel_name
        extracted_date = None
        
        # MUTASI NAMA ELEVEN -> DAZN Khusus di Kategori SPORTS
        if target_category == "SPORTS":
            new_channel_name = re.sub(r'(?i)\beleven\b', 'DAZN', new_channel_name)
        
        clean_group_title = CLEANING_REGEX.sub(' ', raw_group_title).upper()
        clean_channel_name = CLEANING_REGEX.sub(' ', raw_channel_name).upper()
        
        # PENGHANCUR SPAM
        if any(spam in clean_channel_name for spam in SPAM_KEYWORDS):
            continue

        # Pengecualian mutlak untuk RADIO
        if "RADIO" in clean_channel_name or "RADIO" in clean_group_title:
            continue

        match_found = False

        if is_event_category:
            if has_time_pattern:
                match_found = True
                extracted_date = extract_date_from_group(raw_group_title)
                if extracted_date and not re.match(r'^\d{2}-\d{2}-\d{2,4}', raw_channel_name.strip()):
                    new_channel_name = f"{extracted_date} {raw_channel_name.strip()}"
        else:
            is_match = any(k in clean_group_title or k in clean_channel_name for k in keywords)
            is_excluded = any(k in clean_group_title or k in clean_channel_name for k in exclude_keywords)
            
            if is_match and not is_excluded:
                if require_time and not has_time_pattern:
                    match_found = False
                else:
                    match_found = True

        if match_found:
            if force_category:
                for idx in range(len(current_buffer)):
                    b_line = current_buffer[idx]
                    
                    if b_line.startswith("#EXTINF"):
                        if 'group-title="' in b_line:
                            b_line = re.sub(r'group-title="[^"]*"', f'group-title="{target_category}"', b_line, flags=re.IGNORECASE)
                        else:
                            if ',' in b_line:
                                parts = b_line.split(',', 1)
                                b_line = f'{parts[0]} group-title="{target_category}",{parts[1]}'
                            else:
                                b_line = f'{b_line} group-title="{target_category}"'
                        
                        # Jika nama dimutasi (Eleven->DAZN) atau ditambah tanggal (Event)
                        if new_channel_name != raw_channel_name:
                            parts = b_line.split(',', 1)
                            if len(parts) == 2:
                                b_line = f"{parts[0]},{new_channel_name}"
                                
                        current_buffer[idx] = b_line
                        
                    elif b_line.upper().startswith("#EXTGRP:"):
                        current_buffer[idx] = f"#EXTGRP:{target_category}"
            
            sort_key = new_channel_name.upper()
            if is_event_category and extracted_date:
                date_parts = extracted_date.split('-')
                if len(date_parts) == 3:
                    sort_key = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]} {new_channel_name.upper()}"
            
            # Hitung Skor Kasta (Hanya untuk SPORTS, yang lain default 99)
            priority_score = 99
            if target_category == "SPORTS":
                priority_score = get_channel_priority(new_channel_name)
            elif is_event_category:
                priority_score = 0 # Event urut berdasarkan tanggal/waktu
            
            # Memasukkan priority_score ke dalam data channels
            channels_data.append((priority_score, sort_key, current_buffer, stream_url))
            CATEGORIZED_URLS.add(stream_url)
                    
    # SORTING KASTA SULTAN (Prioritas 1st, Abjad/Tanggal 2nd)
    if require_time or is_event_category or target_category == "SPORTS":
        channels_data.sort(key=lambda x: (x[0], x[1]))
    else:
        channels_data.sort(key=lambda x: x[1]) # Kategori lain tetap sesuai abjad murni
    
    # GABUNGKAN PLAYLIST
    filtered_lines = ["#EXTM3U"]
    for _, _, block_data, s_url in channels_data:
        filtered_lines.extend(block_data)  
        filtered_lines.append(s_url)       

    print(f"Total {len(channels_data)} saluran berhasil dikelompokkan ke grup [{target_category}].")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(filtered_lines) + '\n')
    print(f"Playlist [{output_file}] berhasil disimpan.")

# ====================================================================
# III. EKSEKUSI UTAMA
# ====================================================================

if __name__ == "__main__":
    print("=====================================================")
    print("MEMULAI MESIN PENYEDOT IPTV (MULTITHREADING TURBO)")
    print("=====================================================")
    
    all_providers_data = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(download_playlist, MASTER_URLS)
        
        for url, channels in results:
            if channels:
                all_providers_data.append({
                    "url": url,
                    "channels": channels
                })
                
    print("\n[+] Membuat Daftar Saluran Super Bersih (Prioritas Penyedia Nomor 1)...")
    
    super_clean_channels = []
    master_seen_urls = set()
    
    for provider in all_providers_data:
        for ch in provider["channels"]:
            stream_url = ch["url"]
            
            if stream_url in GLOBAL_BLACKLIST_URLS:
                continue
            
            if stream_url not in master_seen_urls:
                master_seen_urls.add(stream_url)
                super_clean_channels.append(ch) 
    
    print(f"Total saluran unik (Link Beda) yang didapat: {len(super_clean_channels)}")
    print("\n[+] Memulai proses filtering ke Kategori...")
    
    for config in CONFIGURATIONS:
        filter_m3u_by_config(config, super_clean_channels)
        
    print("\n✅ PROSES SELESAI! M3U bersih, Nama Kembar diizinkan untuk cadangan asalkan link beda!")
