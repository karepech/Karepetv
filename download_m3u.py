import requests 
import re
import os

# ====================================================================
# I. KONFIGURASI GLOBAL (URL, Kata Kunci, dan Blacklist)
# ====================================================================

# DAFTAR LENGKAP SEMUA URL SUMBER
ALL_SOURCE_URLS = [
    "https://bit.ly/kopinyaoke",
    "https://donzcompany.shop/donztelevision/donztelevision.php",
    "https://URL_EVENT_TAMBAHAN_ANDA.m3u", 
    "https://bakulwifi.my.id/bwifi.m3u"
]


# DAFTAR KATA KUNCI POSITIF
ALL_POSITIVE_KEYWORDS = {
    # KATEGORI 1: Fokus pada Event Spesifik dan Live
    "EVENT_AND_LIVE": [
        "EVENT", "LIVE", "LANGSUNG", "MATCH", "FINAL", "SEMI FINAL",
        "QUARTER FINAL", "FIFA" 
    ], 
    
    # KATEGORI 2: Fokus pada Nama Liga dan Sports umum
    "LEAGUES_AND_SPORTS": [
        "SPORT", "PREMIER LEAGUE", "EPL", "SERIE A", "LIGA ITALIA", 
        "LALIGA", "LIGA SPANYOL", "CHAMPIONS", "LIGA CHAMPIONS", 
        "LIGUE 1", "BUNDESLIGA", "FOOTBALL", "BASKET", "NBA", "TENNIS", "BEIN", "ASTRO", "DAZN", "SPOT" 
    ]
}

# DAFTAR URL YANG DIKECUALIKAN SECARA GLOBAL
GLOBAL_BLACKLIST_URLS = [
    "https://bit.ly/428RaFW",
    "https://bit.ly/DonzTelevisionNewAttention",
    "https://drive.google.com/uc?export=download&id=12slpj4XW5B5SlR9lruuZ77_NPtTHKKw8&usp",
]

# DAFTAR KONFIGURASI DENGAN ATURAN KHUSUS PER URL
CONFIGURATIONS = [
    {
        "urls": ALL_SOURCE_URLS, 
        # PERUBAHAN: Nama file tetap 'event_combined.m3u', tetapi disimpan di folder
        "output_file": "GROUP_EVENT_LIVE/event_combined.m3u", 
        "keywords": ALL_POSITIVE_KEYWORDS["EVENT_AND_LIVE"], 
        "description": "GRUP 1: EVENT & LIVE (Scan Semua Sumber)"
    },
    {
        "urls": ALL_SOURCE_URLS, 
        # PERUBAHAN: Nama file tetap 'sports_combined.m3u', tetapi disimpan di folder
        "output_file": "GROUP_SPORTS_LEAGUES/sports_combined.m3u", 
        "keywords": ALL_POSITIVE_KEYWORDS["LEAGUES_AND_SPORTS"], 
        "description": "GRUP 2: LEAGUES & SPORTS (Scan Semua Sumber)"
    },
        
]

# Regular Expression
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)
CHANNEL_NAME_REGEX = re.compile(r',([^,]*)$')
CLEANING_REGEX = re.compile(r'[^a-zA-Z0-9\s]+') 

# ====================================================================
# II. FUNGSI UTAMA FILTERING
# ====================================================================

def filter_m3u_by_config(config):
    """Mengunduh dan memfilter berdasarkan konfigurasi tunggal (multi-URL)."""
    urls = config["urls"] 
    output_file = config["output_file"]
    keywords = config["keywords"]
    description = config["description"]
    
    print(f"\n--- Memproses [{description}] ---")
    
    filtered_lines = ["#EXTM3U"]
    total_entries = 0
    
    # Membuat direktori jika belum ada
    output_dir = os.path.dirname(output_file)
    if output_dir: 
        os.makedirs(output_dir, exist_ok=True)
        print(f"  > Memastikan direktori '{output_dir}' sudah tersedia.")

    # Iterasi melalui setiap URL di dalam daftar
    for url in urls:
        print(f"  > Mengunduh dari: {url}")
        
        try:
            response = requests.get(url, timeout=60) 
            response.raise_for_status()
            content = response.text.splitlines()
            print(f"  > Status: {response.status_code} | Baris Total: {len(content)}") 
        except requests.exceptions.RequestException as e:
            print(f"  > WARNING: Gagal mengunduh URL {url}. Melewatkan sumber ini. Error: {e}")
            continue 

        i = 0
        while i < len(content):
            line = content[i].strip()
            
            if line.startswith("#EXTINF"):
                
                if i + 1 < len(content):
                    stream_url = content[i+1].strip()
                    
                    is_valid_url = not stream_url.startswith("#") and len(stream_url) > 5
                    
                    if is_valid_url:
                        
                        # 1. Cek Blacklist GLOBAL
                        if stream_url in GLOBAL_BLACKLIST_URLS:
                            i += 2
                            continue
                            
                        # 2. Ekstrak dan Bersihkan
                        group_match = GROUP_TITLE_REGEX.search(line)
                        channel_match = CHANNEL_NAME_REGEX.search(line)
                        
                        raw_group_title = group_match.group(1) if group_match else ""
                        raw_channel_name = channel_match.group(1) if channel_match else ""
                        
                        clean_group_title = CLEANING_REGEX.sub(' ', raw_group_title).upper()
                        clean_channel_name = CLEANING_REGEX.sub(' ', raw_channel_name).upper()
                        
                        # 3. LOGIKA FILTER POSITIF KHUSUS
                        is_match = any(keyword in clean_group_title or keyword in clean_channel_name for keyword in keywords)
                        
                        if is_match:
                            filtered_lines.append(line)
                            filtered_lines.append(stream_url)
                            total_entries += 1
                            
                        i += 2
                        continue
                    else:
                        i += 1
                        continue
            
            i += 1
            
    print(f"Total {total_entries} saluran difilter dari semua sumber.")
    
    # Simpan file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(filtered_lines) + '\n')
    print(f"Playlist {output_file} berhasil disimpan.")


# ====================================================================
# III. EKSEKUSI
# ====================================================================

if __name__ == "__main__":
    print(f"Memulai Multi-Filter M3U.")
    
    for config in CONFIGURATIONS:
        filter_m3u_by_config(config)
        
    print("\nProses Multi-Filter selesai.")
