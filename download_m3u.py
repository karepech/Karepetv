import requests
import re
import os

# Konfigurasi
SOURCE_URLS = [
    "https://donzcompany.shop/donztelevision/donztelevision.php",
    # Tambahkan URL M3U lain di sini jika ada.
]
# Mengubah nama file output agar jelas bahwa ini adalah output debug/full
OUTPUT_FILE = "live_events_full_debug.m3u" 

# Daftar URL yang dikecualikan (BLACKLIST) - INI ADALAH SATU-SATUNYA FILTER AKTIF
BLACKLIST_URLS = [
    "https://bit.ly/428RaFW",
    "https://bit.ly/DonzTelevisionNewAttention",
]

def filter_live_events(source_urls, output_file):
    """Mendownload SEMUA konten dan hanya MENGECUALIKAN link yang ada di blacklist."""
    
    filtered_lines = ["#EXTM3U"]
    total_entries = 0
    
    for url in source_urls:
        print(f"\n--- Memproses URL: {url} (MODE: BLACKLIST ONLY) ---")
        
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
        
        while i < len(content):
            line = content[i].strip()
            
            if line.startswith("#EXTINF"):
                
                if i + 1 < len(content):
                    stream_url = content[i+1].strip()
                    
                    is_valid_url = not stream_url.startswith("#") and len(stream_url) > 5
                    
                    if is_valid_url:
                        
                        # LOGIKA FILTER: Jika BUKAN di blacklist, masukkan.
                        if stream_url not in BLACKLIST_URLS:
                            filtered_lines.append(line)
                            filtered_lines.append(stream_url)
                            total_entries += 1
                        else:
                            print(f"   [SKIP] URL di blacklist: {stream_url}")
                            
                        i += 2
                        continue
                    else:
                        i += 1
                        continue
            
            i += 1
            
        print(f"Total entries dari URL ini: {total_entries}")


    # 4. Simpan konten yang sudah difilter
    print(f"\n--- Total ---")
    print(f"Total ditemukan {total_entries} saluran yang difilter (BLACKLIST-ONLY).")
    
    with open(output_file, "w", encoding="utf-8") as f:
        if total_entries == 0:
             f.write('#EXTM3U\n')
        else:
             f.write('\n'.join(filtered_lines) + '\n')

    print(f"Playlist berhasil disimpan ke {output_file}")


if __name__ == "__main__":
    filter_live_events(SOURCE_URLS, OUTPUT_FILE)
