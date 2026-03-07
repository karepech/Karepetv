import requests
import re

# ====================================================================
# I. KONFIGURASI GLOBAL
# ====================================================================

ALL_POSITIVE_KEYWORDS = {
    "EVENT_ONLY": ["EVENT", "SEA GAMES", "PREMIER LEAGUE", "LA LIGA", "SERIE A", "BUNDESLIGA", "LIGUE 1", "EREDIVISIE", "LIGA 1 INDONESIA", "LIGA PRO SAUDI"],
    "SPORTS_LIVE": ["SPORT", "SPORTS", "LIVE", "LANGSUNG", "OLAHRAGA", "MATCH", "LIGA", "FOOTBALL", "BEIN", "SPOT", "BE IN"],
    "NASIONAL_ID": [
        "INDONESIA", "NASIONAL", "LOKAL", "DAERAH",
        "RCTI", "SCTV", "INDOSIAR", "TRANS", "MNC", "GTV", "GLOBAL TV", 
        "INEWS", "TVONE", "TV ONE", "METRO", "KOMPAS", "NET", "RTV", 
        "TVRI", "BTV", "CNN INDONESIA", "CNBC", "JAK TV", "JTV"
    ],
    "KIDS": [
        "KIDS", "ANAK", "CARTOON", "KARTUN", "NICKELODEON", "NICK JR", 
        "DISNEY", "CARTOON NETWORK", "CN", "BOOMERANG", "BABY", 
        "ANIMATION", "ANIMASI", "TOON", "CERIA", "MENTARI"
    ],
    "KNOWLEDGE": [
        "KNOWLEDGE", "EDUCATION", "EDUKASI", "PENGETAHUAN", "DISCOVERY", 
        "NATIONAL GEOGRAPHIC", "NAT GEO", "NATGEO", "HISTORY", 
        "ANIMAL PLANET", "SCIENCE", "SAINS", "DOCUMENTARY", "DOKUMENTER", "WILD"
    ]
}

GLOBAL_BLACKLIST_URLS = {
    "https://bit.ly/428RaFW",
    "https://iili.io/KfT7PJ2.jpg",
    "https://drive.google.com/uc?export=download&id=12slpj4XW5B5SlR9lruuZ77_NPtTHKKw8&usp",
    "https://shorter.me/SNozg",
    "https://kuk1.modprimus.cfd/kuk3/usergendx0slfk9QssDx9lgxlsdmqrnd.m3u8",
    "https://kuk1.modprimus.cfd/kuk2/usergendx0ul2J8tsDx9lgcddwqrnd.m3u8",
    "https://kudos111.terranovax1.cfd/kuk4/usergendx0thc60skrdnnd.m3u8",
    "https://pulse1.zalmora.cfd/kuk1/usergendx472snx93kdgwqrnd.m3u8",
}

CONFIGURATIONS = [
    {
        "urls": ["https://bit.ly/KPL203", "https://liveevent.iptvbonekoe.workers.dev", "https://deccotech.online/tv/tvstream.html", "https://freeiptv2026.tsender57.workers.dev"],
        "output_file": "event_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "EVENT", 
        "force_category": False, 
        "description": "EVENT: Gabungan Event Asli"
    },
    {
        "urls": ["https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25", "https://deccotech.online/tv/tvstream.html", "https://s.id/semartv"],
        "output_file": "sports_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"],
        "category_name": "SPORTS",
        "force_category": True,  
        "description": "SPORTS: Gabungan Live"
    },
    {
        "urls": ["https://s.id/semartv", "https://liveevent.iptvbonekoe.workers.dev", "https://freeiptv2026.tsender57.workers.dev", "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25"],
        "output_file": "nasional_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["NASIONAL_ID"],
        "category_name": "NASIONAL",
        "force_category": True,
        "description": "NASIONAL: Gabungan Saluran Lokal"
    },
    {
        "urls": ["https://s.id/semartv", "https://liveevent.iptvbonekoe.workers.dev", "https://freeiptv2026.tsender57.workers.dev", "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25"],
        "output_file": "kids_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["KIDS"],
        "category_name": "KIDS",
        "force_category": True,
        "description": "KIDS: Gabungan Saluran Anak"
    },
    {
        "urls": ["https://s.id/semartv", "https://liveevent.iptvbonekoe.workers.dev", "https://freeiptv2026.tsender57.workers.dev", "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25"],
        "output_file": "knowledge_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["KNOWLEDGE"],
        "category_name": "KNOWLEDGE",
        "force_category": True,
        "description": "KNOWLEDGE: Gabungan Saluran Edukasi"
    },
]

# Regex
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)
CLEANING_REGEX = re.compile(r'[^a-zA-Z0-9\s]+')

# ====================================================================
# II. FUNGSI UTAMA FILTERING
# ====================================================================

def get_ott_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://www.google.com",
        "Referer": "https://www.google.com/"
    }

def filter_m3u_by_config(config):
    urls = config["urls"]
    output_file = config["output_file"]
    keywords = config["keywords"]
    target_category = config["category_name"] 
    force_category = config["force_category"]
    description = config["description"]

    print(f"\n--- Memproses [{description}] ---")
    
    # LIST SEMENTARA UNTUK MENYIMPAN DATA SEBELUM DIURUTKAN
    # Format isi: (nama_channel_untuk_sorting, blok_metadata, stream_url)
    channels_data = [] 
    
    for url in urls:
        if not url:
            continue
            
        print(f"  > Mengunduh dari: {url}")
        
        try:
            response = requests.get(url, headers=get_ott_headers(), timeout=(10, 30), stream=True, allow_redirects=True)
            response.raise_for_status()
            
            current_buffer = []  
            current_extinf = ""  
            
            for raw_line in response.iter_lines():
                if not raw_line:
                    continue
                    
                line = raw_line.decode('utf-8', errors='ignore').strip()
                
                if line.startswith("#EXTM3U"):
                    continue
                
                if line.startswith("#"):
                    current_buffer.append(line)
                    if line.startswith("#EXTINF"):
                        current_extinf = line
                        
                elif len(line) > 5:
                    stream_url = line
                    
                    if current_buffer and current_extinf:
                        if stream_url not in GLOBAL_BLACKLIST_URLS:
                            
                            group_match = GROUP_TITLE_REGEX.search(current_extinf)
                            raw_group_title = group_match.group(1) if group_match else ""
                            
                            if "," in current_extinf:
                                raw_channel_name = current_extinf.split(',', 1)[1]
                            else:
                                raw_channel_name = current_extinf
                            
                            clean_group_title = CLEANING_REGEX.sub(' ', raw_group_title).upper()
                            clean_channel_name = CLEANING_REGEX.sub(' ', raw_channel_name).upper()
                            
                            # --- FITUR BARU: BUANG CHANNEL RADIO ---
                            if "RADIO" in clean_channel_name or "RADIO" in clean_group_title:
                                current_buffer = []
                                current_extinf = ""
                                continue # Langsung lewati ke baris berikutnya
                            
                            is_match = any(k in clean_group_title or k in clean_channel_name for k in keywords)
                            
                            if is_match:
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
                                            current_buffer[idx] = b_line
                                            
                                        elif b_line.upper().startswith("#EXTGRP:"):
                                            current_buffer[idx] = f"#EXTGRP:{target_category}"
                                
                                # Simpan ke list sementara (belum ditulis ke file) agar bisa diurutkan nanti
                                channels_data.append((clean_channel_name, current_buffer, stream_url))
                                
                    current_buffer = []
                    current_extinf = ""
                        
        except requests.exceptions.RequestException as e:
            print(f"  > WARNING: Gagal memproses {url}. Error: {e}")
            continue
            
    # --- FITUR BARU: URUTKAN BERDASARKAN ALFABET (NAMA CHANNEL) ---
    # Ini akan membuat RCTI berjejer dengan RCTI lainnya, beIN 1 dengan beIN 1 lainnya.
    channels_data.sort(key=lambda x: x[0])
    
    # Masukkan data yang sudah rapi berurutan ke hasil akhir
    filtered_lines = ["#EXTM3U"]
    for _, block_data, s_url in channels_data:
        filtered_lines.extend(block_data)
        filtered_lines.append(s_url)

    print(f"Total {len(channels_data)} saluran difilter dan diurutkan.")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(filtered_lines) + '\n')
    print(f"Playlist [{output_file}] berhasil disimpan.")

# ====================================================================
# III. EKSEKUSI
# ====================================================================

if __name__ == "__main__":
    print("Memulai Multi-Filter M3U (Sorted & Anti-Radio)...")
    for config in CONFIGURATIONS:
        filter_m3u_by_config(config)
    print("\nProses selesai. Semua file M3U kini berjejer rapi dan bebas Radio!")
