import requests # PERBAIKAN: Mengubah 'Iport' menjadi 'import'
import re
import os

# ====================================================================
# I. KONFIGURASI GLOBAL (URL, Kata Kunci, dan Blacklist)
# ====================================================================

# DAFTAR KATA KUNCI POSITIF
ALL_POSITIVE_KEYWORDS = {
    # URL 1: Hanya Event (mengambil kata kunci yang ada di contoh M3U Event Anda)
    "EVENT_ONLY": ["EVENT",], 
    # URL 2: Hanya Sports & Live (Didefinisikan tapi tidak digunakan di CONFIGURATIONS baru)
    "SPORTS_LIVE": ["SPORT", "SPORTS", "LIVE", "LANGSUNG", "OLAHRAGA", "MATCH", "LIGA", "FOOTBALL", "BEIN", "SPOT", "BE IN"]
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
        "url": "https://bit.ly/kopinyaoke",
        "output_file": "event_only_url1.m3u", # Output file untuk Event
        "keywords": ALL_POSITIVE_KEYWORDS["EVENT_ONLY"], # HANYA EVENT
        "description": "Hanya Event dari URL 1 (Kopi/Traktir)"
    },
    {
        "url": "https://donzcompany.shop/donztelevision/donztelevisions.php","https://bakulwifi.my.id/live.m3u",
        "output_file": "event_only_url2.m3u", # Output file untuk Event dari URL kedua
        "keywords": ALL_POSITIVE_KEYWORDS["EVENT_ONLY"], # HANYA EVENT (Diperbarui)
        "description": "Hanya Event dari URL 2 (Sports/Live)"
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
    """Mengunduh dan memfilter berdasarkan konfigurasi tunggal."""
    url = config["url"]
    output_file = config["output_file"]
    keywords = config["keywords"]
    description = config["description"]
    
    print(f"\n--- Memproses [{description}] dari: {url} ---")
    
    try:
        # Menggunakan 'import requests' yang benar
        response = requests.get(url, timeout=60) 
        response.raise_for_status()
        content = response.text.splitlines()
        print(f"Status Koneksi: {response.status_code} | Baris: {len(content)}") 
    except requests.exceptions.RequestException as e:
        print(f"FATAL ERROR: Gagal mengunduh URL {url}: {e}")
        return

    filtered_lines = ["#EXTM3U"]
    total_entries = 0
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
                        print(f"   [SKIP] URL di blacklist: {stream_url}")
                        i += 2
                        continue
                        
                    # 2. Ekstrak dan Bersihkan
                    group_match = GROUP_TITLE_REGEX.search(line)
                    channel_match = CHANNEL_NAME_REGEX.search(line)
                    
                    raw_group_title = group_match.group(1) if group_match else ""
                    raw_channel_name =
