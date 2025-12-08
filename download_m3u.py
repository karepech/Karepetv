import requests
import re
import sys
import os

def process_m3u(source_urls_str, output_filename):
    """
    Mengunduh dari beberapa URL M3U, memfilter entri 'live',
    dan menggabungkan hasilnya ke file output.
    """
    source_urls = [url.strip() for url in source_urls_str.split(',') if url.strip()]

    if not source_urls:
        print("Error: Daftar URL sumber kosong.")
        sys.exit(1)

    live_pattern = re.compile(r'#EXTINF:.*group-title="live".*', re.IGNORECASE)
    output_lines = ["#EXTM3U"]
    total_live_count = 0

    for url in source_urls:
        print(f"\n--- Memproses URL: {url} ---")
        try:
            session = requests.Session()
            response = session.get(url, timeout=15)
            response.raise_for_status() 

            m3u_content = response.text
            lines = m3u_content.splitlines()

        except requests.exceptions.RequestException as e:
            print(f"Peringatan: Gagal mengunduh dari {url}. Melanjutkan ke URL berikutnya. Error: {e}")
            continue

        live_count = 0
        in_live_block = False
        
        for i in range(len(lines)):
            line = lines[i].strip()
            
            if live_pattern.search(line):
                output_lines.append(line)
                in_live_block = True
                live_count += 1
                
            elif in_live_block and line and not line.startswith('#'):
                output_lines.append(line)
                in_live_block = False
                
            elif line.startswith('#EXTINF:'):
                in_live_block = False

        print(f"Ditemukan {live_count} channel 'live' dari URL ini.")
        total_live_count += live_count

    print(f"\nTotal ditemukan {total_live_count} channel 'live' dari semua sumber.")
    
    try:
        unique_output_lines = []
        for line in output_lines:
            if line not in unique_output_lines or line != "#EXTM3U":
                unique_output_lines.append(line)

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
