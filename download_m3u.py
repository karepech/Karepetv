import requests
import re
import os

# Konfigurasi
SOURCE_URL = "https://dildo.beww.pl/ngen.m3u" 
OUTPUT_FILE = "live_events.m3u"

# >>>>> PERUBAHAN DI SINI: KATA KUNCI DIUBAH KE "SPORT" <<<<<
LIVE_CATEGORY_PHRASE = "SPORT"

# Regular Expression untuk mengambil group-title
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)

def filter_live_events(source_url, output_file):
    """Mengunduh, memfilter (berdasarkan SPORT), dan menyimpan playlist M3U."""
    
    try:
        # 1. Unduh konten M3U
        print(f"Mengunduh M3U dari: {source_url}")
        response = requests.get(source_url, timeout=60) 
        response.raise_for_status()
        content = response.text.splitlines()

        # DEBUGGING OUTPUT
        print(f"Status Koneksi: {response.status_code}") 
        print(f"Jumlah baris yang berhasil diunduh: {len(content)}") 

    except requests.exceptions.RequestException as e:
        print(f"FATAL ERROR: Gagal mengunduh atau koneksi terputus: {e}")
        exit(1) 

    filtered_lines = ["#EXTM3U"]
    i = 0
    num_entries = 0
    
    while i < len(content):
        line = content[i].strip()
        
        # Cari baris deskripsi
        if line.startswith("#EXTINF"):
            
            # --- Perbaikan Logika: Pastikan URL disalin dan bukan baris kosong/komentar ---
            if i + 1 < len(content):
                stream_url = content[i+1].strip()
                
                # Hanya lanjutkan jika baris berikutnya bukan baris komentar atau terlalu pendek
                if not stream_url.startswith("#") and len(stream_url) > 5:
                    
                    # a. Ekstrak group-title
                    group_match = GROUP_TITLE_REGEX.search(line)
                    group_title = group_match.group(1).strip() if group_match else ""
                    
                    # b. Lakukan pemeriksaan filter: Cek apakah "SPORT" ada di group-title.
                    is_live_category = LIVE_CATEGORY_PHRASE in group_title.strip().upper()
                    
                    if is_live_category:
                        # Salin BARIS DESKRIPSI (i) dan BARIS URL (i+1)
                        filtered_lines.append(line)
                        filtered_lines.append(stream_url)
                        num_entries += 1
                        
                    # Lompati ke baris setelah URL stream
                    i += 2
                    continue
                else:
                    # Jika baris setelah EXTINF bukan URL, lompati hanya 1 baris
                    i += 1
                    continue
            
        i += 1
        
    # 3. Simpan konten yang sudah difilter
    print(f"Ditemukan {num_entries} saluran yang difilter.")
    
    # Simpan file live_events.m3u
    with open(output_file, "w", encoding="utf-8") as f:
        if num_entries == 0:
             f.write('#EXTM3U\n')
        else:
             f.write('\n'.join(filtered_lines) + '\n')

    print(f"Playlist yang difilter berhasil disimpan ke {output_file}")


if __name__ == "__main__":
    filter_live_events(SOURCE_URL, OUTPUT_FILE)
