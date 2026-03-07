import requests
import re

# ====================================================================
# I. KONFIGURASI GLOBAL
# ====================================================================

ALL_POSITIVE_KEYWORDS = {
    "EVENT_ONLY": ["EVENT", "SEA GAMES", "PREMIER LEAGUE", "LA LIGA", "SERIE A", "BUNDESLIGA", "LIGUE 1", "EREDIVISIE", "LIGA 1 INDONESIA", "LIGA PRO SAUDI"],
    "SPORTS_LIVE": ["SPORT", "SPORTS", "LIVE", "LANGSUNG", "OLAHRAGA", "MATCH", "LIGA", "FOOTBALL", "BEIN", "SPOT", "BE IN"]
}

# PERBAIKAN 1: Menggunakan Set {} agar pencarian blacklist berkecepatan $O(1)$
GLOBAL_BLACKLIST_URLS = {
    "https://bit.ly/428RaFW",
    "https://bit.ly/DonzTelevisionNewAttention",
    "https://drive.google.com/uc?export=download&id=12slpj4XW5B5SlR9lruuZ77_NPtTHKKw8&usp",
    "https://iili.io/KxLFPLJ.md.png",
}

CONFIGURATIONS = [
    {
        "urls": ["https://bit.ly/KPL203", "https://bit.ly/TVKITKAT", "https://freeiptv2026.tsender57.workers.dev"],
        "output_file": "event_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "description": "EVENT: Gabungan dari beberapa sumber"
    },
    {
        "urls": ["https://donztelevisionpremium.icu/donztelevision/donztelevision.php", "https://bakulwifi.my.id/live.m3u"],
        "output_file": "sports_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"],
        "description": "SPORTS: Gabungan dari dua sumber Live"
    },
]

# Regex untuk mengambil group-title
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)
# Regex untuk membersihkan karakter (hanya alphanumeric dan spasi)
CLEANING_REGEX = re.compile(r'[^a-zA-Z0-9\s]+')

# ====================================================================
# II. FUNGSI UTAMA FILTERING
# ====================================================================

def get_ott_headers():
    """
    PERBAIKAN 2: HTTP Headers palsu untuk mem-bypass blokir dasar dari link OTT.
    Ini membuat server OTT mengira request datang dari Smart TV / Browser asli.
    """
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
    description = config["description"]

    print(f"\n--- Memproses [{description}] ---")
    
    filtered_lines = ["#EXTM3U"]
    total_entries = 0
    
    for url in urls:
        print(f"  > Mengunduh dari: {url}")
        
        try:
            # PERBAIKAN 3: stream=True agar hemat RAM, dan timeout lebih dinamis
            response = requests.get(url, headers=get_ott_headers(), timeout=(10, 30), stream=True)
            response.raise_for_status()
            
            current_extinf = None
            
            # PERBAIKAN 4: Membaca baris per baris tanpa memuat semua ke memori
            for raw_line in response.iter_lines():
                if not raw_line:
                    continue
                    
                line = raw_line.decode('utf-8', errors='ignore').strip()
                
                if line.startswith("#EXTINF"):
                    # Simpan metadata ini sambil menunggu baris URL-nya
                    current_extinf = line
                    
                # Abaikan baris komentar atau tag tambahan lain seperti #EXTGRP
                elif line.startswith("#"):
                    continue
                    
                # Jika bukan komentar dan panjangnya > 5, asumsikan ini URL
                elif len(line) > 5:
                    stream_url = line
                    
                    # Pastikan kita punya pasangan #EXTINF
                    if current_extinf:
                        if stream_url not in GLOBAL_BLACKLIST_URLS:
                            
                            # Ekstrak metadata
                            group_match = GROUP_TITLE_REGEX.search(current_extinf)
                            raw_group_title = group_match.group(1) if group_match else ""
                            
                            # PERBAIKAN 5: Regex yang lebih aman untuk nama channel
                            parts = current_extinf.split(',', 1)
                            raw_channel_name = parts[1] if len(parts) > 1 else ""
                            
                            clean_group_title = CLEANING_REGEX.sub(' ', raw_group_title).upper()
                            clean_channel_name = CLEANING_REGEX.sub(' ', raw_channel_name).upper()
                            
                            # Pencocokan
                            is_match = any(k in clean_group_title or k in clean_channel_name for k in keywords)
                            
                            if is_match:
                                filtered_lines.append(current_extinf)
                                filtered_lines.append(stream_url)
                                total_entries += 1
                                
                        # Reset metadata untuk mempersiapkan channel berikutnya
                        current_extinf = None
                        
        except requests.exceptions.RequestException as e:
            print(f"  > WARNING: Gagal memproses {url}. Error: {e}")
            continue
            
    print(f"Total {total_entries} saluran difilter.")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(filtered_lines) + '\n')
    print(f"Playlist {output_file} berhasil disimpan.")

# ====================================================================
# III. EKSEKUSI
# ====================================================================

if __name__ == "__main__":
    print("Memulai Multi-Filter M3U (Optimized & OTT Supported)...")
    for config in CONFIGURATIONS:
        filter_m3u_by_config(config)
    print("\nProses Multi-Filter selesai.")
