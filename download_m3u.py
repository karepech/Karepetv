import requests
import re

# ====================================================================
# I. KONFIGURASI GLOBAL
# ====================================================================

# Penyempurnaan: "CCTV" masuk News, "NET" diubah ke "NET TV", "CN" dihapus agar tidak bentrok dengan CNBC/CNN
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
    "https://kuk1.modprimus.cfd/kuk3/usergendx0slfk9QssDx9lgxlsdmqrnd.m3u8",
    "https://kuk1.modprimus.cfd/kuk2/usergendx0ul2J8tsDx9lgcddwqrnd.m3u8",
    "https://kudos111.terranovax1.cfd/kuk4/usergendx0thc60skrdnnd.m3u8",
    "https://pulse1.zalmora.cfd/kuk1/usergendx472snx93kdgwqrnd.m3u8",
}

# --- KONFIGURASI 7 KATEGORI (Semua Force Category = True) ---
CONFIGURATIONS = [
    {
        "urls": ["https://bit.ly/KPL203", "https://liveevent.iptvbonekoe.workers.dev", 
                 "https://deccotech.online/tv/tvstream.html",
                 "https://bit.ly/TVKITKAT",
                 "https://s.id/semartv",
                 "https://semar25.short.gy",
                 "https://freeiptv2026.tsender57.workers.dev"],
        "output_file": "event_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"], 
        "category_name": "EVENT", 
        "force_category": True, # PERUBAHAN: Event sekarang digabungkan ke dalam 1 folder "EVENT"
        "description": "EVENT: Gabungan Event Olahraga"
    },
    {
        "urls": ["https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25", "https://deccotech.online/tv/tvstream.html", "https://s.id/semartv"],
        "output_file": "sports_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"],
        "category_name": "SPORTS",
        "force_category": True,  
        "description": "SPORTS: Gabungan Live"
    },
    {
        "urls": ["https://s.id/semartv", "https://liveevent.iptvbonekoe.workers.dev", "https://freeiptv2026.tsender57.workers.dev", "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25"],
        "output_file": "indonesia_combined.m3u", 
        "keywords": ALL_POSITIVE_KEYWORDS["INDONESIA"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "INDONESIA",
        "force_category": True,
        "description": "INDONESIA: Gabungan TV Indonesia Murni"
    },
    {
        "urls": ["https://s.id/semartv", "https://liveevent.iptvbonekoe.workers.dev", "https://freeiptv2026.tsender57.workers.dev", "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25"],
        "output_file": "kids_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["KIDS"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "KIDS",
        "force_category": True,
        "description": "KIDS: Gabungan Saluran Anak"
    },
    {
        "urls": ["https://s.id/semartv", "https://liveevent.iptvbonekoe.workers.dev", "https://freeiptv2026.tsender57.workers.dev", "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25"],
        "output_file": "knowledge_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["KNOWLEDGE"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "KNOWLEDGE",
        "force_category": True,
        "description": "KNOWLEDGE: Gabungan Saluran Edukasi"
    },
    {
        "urls": ["https://s.id/semartv", "https://liveevent.iptvbonekoe.workers.dev", "https://freeiptv2026.tsender57.workers.dev", "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25"],
        "output_file": "news_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["NEWS"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "NEWS",
        "force_category": True,
        "description": "NEWS: Gabungan Saluran Berita & CCTV"
    },
    {
        "urls": ["https://s.id/semartv", "https://liveevent.iptvbonekoe.workers.dev", "https://freeiptv2026.tsender57.workers.dev", "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25"],
        "output_file": "religi_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["RELIGI"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "RELIGI",
        "force_category": True,
        "description": "RELIGI: Gabungan Saluran Dakwah & Rohani"
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
    exclude_keywords = config["exclude_keywords"] 
    target_category = config["category_name"] 
    force_category = config["force_category"]
    description = config["description"]

    print(f"\n--- Memproses [{description}] ---")
    
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
                            
                            # Buang Channel Radio
                            if "RADIO" in clean_channel_name or "RADIO" in clean_group_title:
                                current_buffer = []
                                current_extinf = ""
                                continue 
                            
                            is_match = any(k in clean_group_title or k in clean_channel_name for k in keywords)
                            is_excluded = any(k in clean_group_title or k in clean_channel_name for k in exclude_keywords)
                            
                            # Cek Kategori Murni (Masuk ke Target Grup yang Ditentukan)
                            if is_match and not is_excluded:
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
                                
                                channels_data.append((clean_channel_name, current_buffer, stream_url))
                                
                    current_buffer = []
                    current_extinf = ""
                        
        except requests.exceptions.RequestException as e:
            print(f"  > WARNING: Gagal memproses {url}. Error: {e}")
            continue
            
    # Urutkan secara alfabet berdasarkan nama channel agar berjejer rapi
    channels_data.sort(key=lambda x: x[0])
    
    filtered_lines = ["#EXTM3U"]
    for _, block_data, s_url in channels_data:
        filtered_lines.extend(block_data)
        filtered_lines.append(s_url)

    print(f"Total {len(channels_data)} saluran berhasil dikelompokkan ke grup [{target_category}].")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(filtered_lines) + '\n')
    print(f"Playlist [{output_file}] berhasil disimpan.")

# ====================================================================
# III. EKSEKUSI
# ====================================================================

if __name__ == "__main__":
    print("Memulai Multi-Filter M3U (Force Category & Anti-Tumpang-Tindih)...")
    for config in CONFIGURATIONS:
        filter_m3u_by_config(config)
    print("\nProses selesai. 7 Kategori M3U super rapi siap digunakan!")
