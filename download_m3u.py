import requests
import re
import os

# Konfigurasi
# >>> PERUBAHAN 1: MENGGUNAKAN DAFTAR URL SUMBER <<<
SOURCE_URLS = [
    "https://dildo.beww.pl/ngen.m3u",
    # TAMBAHKAN URL M3U LAIN DI SINI, PISAHKAN DENGAN KOMA
    # Contoh: "http://link-m3u-lain.com/playlist.m3u",
]
OUTPUT_FILE = "live_events.m3u"

# >>> PERUBAHAN 2: KATA KUNCI FILTER GANDA (SPORT ATAU LIVE) <<<
FILTER_KEYWORDS = ["SPORT", "LIVE"] 

# >>> PERUBAHAN 3: DAFTAR URL YANG DIKECUALIKAN (BLACKLIST) <<<
# URL ini akan diabaikan/dilewatkan, terlepas dari kategori mereka.
BLACKLIST_URLS = [
    "https://bit.ly/428RaFW",
    "https://bit.ly/DonzTelevisionNewAttention",
]

# Regular Expression untuk mengambil group-title
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)

def filter_live_events(source_urls, output_file):
    """Mengunduh dari banyak URL, memfilter berdasarkan kategori dan blacklist, lalu menyimpan hasilnya."""
    
    filtered_lines = ["#EXTM3U"]
    total_entries = 0
    
    # Loop melalui setiap URL sumber
    for url in source_urls:
        print(f"\n--- Memproses URL: {url} ---")
        
        try:
            # 1. Unduh konten M3U
            response = requests.get(url, timeout=60) 
            response.raise_for_status()
            content = response.text.splitlines()

            print(f"Status Koneksi: {response.status_code}") 
            print(f"Jumlah baris yang berhasil diunduh: {len(content)}") 

        except requests.exceptions.RequestException as e:
            print(f"FATAL ERROR: Gagal mengunduh URL {url}: {e}")
            continue # Lanjutkan ke URL berikutnya jika ada error

        i = 0
        url_entries = 0
        
        while i < len(content):
            line = content[i].strip()
            
            if line.startswith("#EXTINF"):
                
                if i + 1 < len(content):
                    stream_url = content[i+1].strip()
                    
                    # Logika Pengecekan URL dan Filter
                    
                    # 1. Pastikan baris berikutnya adalah URL valid
                    is_valid_url = not stream_url.startswith("#") and len(stream_url) > 5
                    
                    if is_valid_url:
                        
                        # 2. Cek apakah URL ada di daftar pengecualian (BLACKLIST)
                        if stream_url in BLACKLIST_URLS:
                            print(f"   [SKIP] URL di blacklist: {stream_url}")
                            i += 2
                            continue
                            
                        # 3. Lakukan Pengecekan Kategori (LIVE ATAU SPORT)
                        group_match = GROUP_TITLE_REGEX.search(line)
                        group_title = group_match.group(1).strip() if group_match else ""
                        group_title_upper = group_title.strip().upper()
                        
                        # Cek jika group-title mengandung SALAH SATU kata kunci
                        is_category_match = any(keyword in group_title_upper for keyword in FILTER_KEYWORDS)
                        
                        if is_category_match:
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

    # 3. Simpan konten yang sudah difilter
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
