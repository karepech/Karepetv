import requests 
import re
import os

# ====================================================================
# I. KONFIGURASI GLOBAL (URL, Kata Kunci, dan Blacklist)
# ====================================================================

# DAFTAR KATA KUNCI POSITIF
ALL_POSITIVE_KEYWORDS = {
    # URL 1: Hanya Event 
    "EVENT_ONLY": ["EVENT",], 
    # URL 2: Hanya Sports & Live 
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
        # PERUBAHAN UTAMA 1: URL kini berupa LIST
        "urls": ["https://bit.ly/kopinyaoke", "https://dildo.beww.pl/ngen.m3u"], 
        "output_file": "event_combined.m3u", 
        "keywords": ALL_POSITIVE_KEYWORDS["EVENT_ONLY"], 
        "description": "EVENT: Gabungan dari beberapa sumber"
    },
    {
        # Contoh jika Anda ingin Sports dari dua sumber digabungkan
        "urls": ["https://donzcompany.shop/donztelevision/donztelevisions.php", "https://bakulwifi.my.id/live.m3u"], 
        "output_file": "sports_combined.m3u", 
        "keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"], # Menggunakan Kategori Sports
        "description": "SPORTS: Gabungan dari dua sumber Live"
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
    # PERUBAHAN: Kini mengambil 'urls' (list) bukan 'url' (string)
    urls = config["urls"] 
    output_file = config["output_file"]
    keywords = config["keywords"]
    description = config["description"]
    
    print(f"\n--- Memproses [{description}] ---")
    
    filtered_lines = ["#EXTM3U"]
    total_entries = 0
    
    # PERUBAHAN UTAMA 2: Iterasi melalui setiap URL di dalam daftar
    for url in urls:
        print(f"  > Mengunduh dari: {url}")
        
        try:
            response = requests.get(url, timeout=60) 
            response.raise_for_status()
            content = response.text.splitlines()
            print(f"  > Status: {response.status_code} | Baris Total: {len(content)}") 
        except requests.exceptions.RequestException as e:
            print(f"  > WARNING: Gagal mengunduh URL {url}. Melewatkan sumber ini. Error: {e}")
            continue # Lanjut ke URL berikutnya jika gagal

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
