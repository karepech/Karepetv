import requests
import re
import sys
import os

def process_m3u(source_urls_str, output_filename):
    """
    Mengunduh dari beberapa URL M3U, memfilter entri 'live' atau 'event',
    dan menggabungkan hasilnya ke file output.
    """
    # Pisahkan string URL menjadi list
    source_urls = [url.strip() for url in source_urls_str.split(',') if url.strip()]

    if not source_urls:
        print("Error: Daftar URL sumber kosong.")
        sys.exit(1)

    # Pola regex untuk mencari EXTLINF dengan group-title="live" ATAU group-title="event" (case-insensitive)
    # Filter: group-title="live" atau group-title="event"
    multi_category_pattern = re.compile(r'#EXTINF:.*group-title="(live|event)".*', re.IGNORECASE)
    
    output_lines = ["#EXTM3U"]
    total_channel_count = 0

    # Iterasi melalui setiap URL
    for url in source_urls:
        print(f"\n--- Memproses URL: {url} ---")
        try:
            # 1. Mengunduh konten M3U
            session = requests.Session()
            response = session.get(url, timeout=15)
            response.raise_for_status() 

            m3u_content = response.text
            lines = m3u_content.splitlines()

        except requests.exceptions.RequestException as e:
            print(f"Peringatan: Gagal mengunduh dari {url}. Melanjutkan ke URL berikutnya. Error: {e}")
            continue

        url_channel_count = 0
        in_valid_block = False
        
        # 2. Memproses dan memfilter baris
        for i in range(len(lines)):
            line = lines[i].strip()
            
            # Jika baris adalah #EXTINF dan memiliki group-title="live" atau "event"
            if multi_category_pattern.search(line):
                output_lines.append(line)
                in_valid_block = True
                url_channel_count += 1
                
            # Jika baris adalah URL (mengikuti #EXTINF sebelumnya)
            elif in_valid_block and line and not line.startswith('#'):
                output_lines.append(line)
                in_valid_block = False
                
            # Baris #EXTINF tapi bukan kategori yang valid, reset flag
            elif line.startswith('#EXTINF:'):
                in_valid_block = False

        print(f"Ditemukan {url_channel_count} channel (live/event) dari URL ini.")
        total_channel_count += url_channel_count


    # 3. Menyimpan hasilnya
    print(f"\nTotal ditemukan {total_channel_count} channel 'live' atau 'event' dari semua sumber.")
    
    try:
        # Menghapus duplikasi baris, kecuali baris EXTM3U
        unique_output_lines = []
        seen_lines = set()
        for line in output_lines:
            if line == "#EXTM3U":
                if "#EXTM3U" not in unique_output_lines:
                    unique_output_lines.append(line)
            elif line not in seen_lines:
                unique_output_lines.append(line)
                seen_lines.add(line)

        with open(output_filename, 'w') as f:
            f.write('\n'.join(unique_output_lines) + '\n')
        print(f"Berhasil menyimpan ke: {output_filename}")
        
    except IOError as e:
        print(f"Error saat menulis file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    SOURCE_URLS = os.environ.get("M3U_SOURCE_URLS")
    OUTPUT_FILE = "event_combined.m3u"
    
    if not SOURCE_URLS:
        print("Error: Variabel lingkungan M3U_SOURCE_URLS tidak ditemukan.")
        sys.exit(1)
        
    process_m3u(SOURCE_URLS, OUTPUT_FILE)
