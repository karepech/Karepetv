import requests
import re
import os

# Konfigurasi
SOURCE_URLS = [
    "https://donzcompany.shop/donztelevision/donztelevision.php",
    # TAMBAHKAN URL M3U LAIN DI SINI
]
OUTPUT_FILE = "live_events.m3u"

# >>> FINAL KATA KUNCI UNTUK INKLUSI POSITIF (Mengatasi Bein dan Spot) <<<
POSITIVE_KEYWORDS = [
    "SPORT", "SPORTS", "LIVE", "LANGSUNG", "OLAHRAGA", "MATCH", "EVENT", 
    "PREMIER", "LIGA", "FOOTBALL", "BOLA", "TENNIS", "BASKET", "RACING", 
    "BEIN", "BE IN", "SPOT", "SPOTS" # Penambahan kata kunci baru
] 

# Daftar URL yang dikecualikan (BLACKLIST)
BLACKLIST_URLS = [
    "https://bit.ly/428RaFW",
    "https://bit.ly/DonzTelevisionNewAttention",
]

# Regular Expression untuk mengambil group-title dan channel name
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)
CHANNEL_NAME_REGEX = re.compile(r',([^,]*)$')
# Regex untuk membersihkan karakter non-alphanumeric (kecuali spasi)
CLEANING_REGEX = re.compile(r'[^a-zA-Z0-9\s]+') 

def filter_live_events(source_urls, output_file):
    """Mengunduh dari banyak URL, memfilter (hanya inklusi positif), dan blacklist."""
    
    filtered_lines = ["#EXTM3U"]
    total_entries = 0
    
    for url in source_urls:
        print(f"\n--- Memproses URL: {url} ---")
        
        try:
            response = requests.get(url, timeout=60) 
            response.raise_for_status()
            content = response.text.splitlines()
            print(f"Status Koneksi: {response.status_code}") 
            print(f"Jumlah baris yang berhasil diunduh: {len(content)}") 
        except requests.exceptions.RequestException as e:
            print(f"FATAL ERROR: Gagal mengunduh URL {url}: {e}")
            continue

        i = 0
        url_entries = 0
        
        while i < len(content):
            line = content[i].strip()
            
            if line.startswith("#EXTINF"):
                
                if i + 1 < len(content):
                    stream_url = content[i+1].strip()
                    
                    is_valid_url = not stream_url.startswith("#") and len(stream_url) > 5
                    
                    if is_valid_url:
                        
                        # 1. Cek Blacklist (Jika ada di blacklist, lewati)
                        if stream_url in BLACKLIST_URLS:
                            print(f"   [SKIP] URL di blacklist: {stream_url}")
                            i += 2
                            continue
                            
                        # 2. Ekstrak, Bersihkan, dan Ubah ke Kapital
                        group_match = GROUP_TITLE_REGEX.search(line)
                        channel_match = CHANNEL_NAME_REGEX.search(line)
                        
                        raw_group_title = group_match.group(1) if group_match else ""
                        raw_channel_name = channel_match.group(1) if channel_match else ""
                        
                        # Bersihkan Teks dari simbol aneh sebelum filtering
                        clean_group_title = CLEANING_REGEX.sub(' ', raw_group_title).upper()
                        clean_channel_name = CLEANING_REGEX.sub(' ', raw_channel_name).upper()
                        
                        # 3. LOGIKA FILTER UTAMA (POSITIF INKLUSI)
                        
                        # Cek apakah Group Title ATAU Channel Name mengandung SALAH SATU kata kunci positif
                        is_match_positive = any(keyword in clean_group_title or keyword in clean_channel_name for keyword in POSITIVE_KEYWORDS)
                        
                        if is_match_positive:
                            filtered_lines.append(line)
                            filtered_lines.append(stream_url)
                            total_entries += 1
                            url_entries += 1
                            
                        i += 2
                        continue
                    else:
                        i += 1
                        continue
            
            i += 1
            
        print(f"Ditemukan {url_entries} entri yang cocok dari URL ini.")

    # 4. Simpan konten yang sudah difilter
    print(f"\n--- Total ---")
    print(f"Total ditemukan {total_entries} saluran yang difilter dari semua sumber.")
    
    with open(output_file, "w", encoding="utf-8") as f:
        if total_entries == 0:
             f.write('#EXTM3U\n')
        else:
             f.write('\n'.join(filtered_lines) + '\n')

    print(f"Playlist yang difilter berhasil disimpan ke {output_file}")


if __name__ == "__main__":
    filter_live_events(SOURCE_URLS, OUTPUT_FILE)
