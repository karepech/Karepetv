import requests
import re
import os

# Konfigurasi
SOURCE_URL = "https://dildo.beww.pl/ngen.m3u" 
OUTPUT_FILE = "live_events.m3u"

# Frasa kunci utama yang Anda konfirmasi
LIVE_CATEGORY_PHRASE = "LIVE NOW"

# Regular Expression untuk mengambil group-title
# Digunakan re.IGNORECASE untuk memastikan pencocokan tidak sensitif huruf besar/kecil
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)

def filter_m3u(source_url, output_file):
    """Mengunduh, memfilter, dan menyimpan playlist M3U berdasarkan frasa LIVE NOW."""
    
    try:
        # 1. Unduh konten M3U
        print(f"Mengunduh M3U dari: {source_url}")
        # Timeout diset ke 60 detik untuk file besar
        response = requests.get(source_url, timeout=60) 
        response.raise_for_status() # Akan memicu exception jika kode status >= 400
        content = response.text.splitlines()

        # >>>>>> DEBUGGING OUTPUT <<<<<<
        print(f"Status Koneksi: {response.status_code}") 
        print(f"Jumlah baris yang berhasil diunduh: {len(content)}") 
        # >>>>>> DEBUGGING OUTPUT <<<<<<

    except requests.exceptions.RequestException as e:
        print(f"FATAL ERROR: Gagal mengunduh atau koneksi terputus: {e}")
        # Jika gagal, skrip akan keluar
        exit(1) 

    filtered_lines = ["#EXTM3U"]
    i = 0
    num_entries = 0
    
    while i < len(content):
        line = content[i].strip()
        
        if line.startswith("#EXTINF"):
            if i + 1 < len(content):
                stream_url = content[i+1].strip()
                
                # a. Ekstrak group-title
                group_match = GROUP_TITLE_REGEX.search(line)
                group_title = group_match.group(1).strip() if group_match else ""
                
                # b. Lakukan pemeriksaan filter: Cek apakah "LIVE NOW" ada di group-title.
                # Menggunakan .strip().upper() dan operator 'in' untuk pencocokan yang paling toleran
                # dan mengabaikan spasi/huruf besar/kecil.
                is_live_category = LIVE_CATEGORY_PHRASE in group_title.strip().upper()
                
                if is_live_category:
                    filtered_lines.append(line)
                    filtered_lines.append(stream_url)
                    num_entries += 1
                
                i += 2
                continue
        
        i += 1
        
    # 3. Simpan konten yang sudah difilter
    print(f"Ditemukan {num_entries} live event yang difilter.")
    
    # Simpan file hanya jika ada konten selain header #EXTM3U
    if num_entries > 0:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write('\n'.join(filtered_lines) + '\n')
        print(f"Playlist yang difilter berhasil disimpan ke {output_file}")
    else:
        # Jika 0, kita masih menyimpan file agar git tahu bahwa file sudah diproses, 
        # tetapi hanya berisi header.
        with open(output_file, "w", encoding="utf-8") as f:
            f.write('#EXTM3U\n')
        print(f"Tidak ada saluran yang cocok dengan '{LIVE_CATEGORY_PHRASE}'. File {output_file} dibuat dengan hanya header.")


if __name__ == "__main__":
    filter_m3u(SOURCE_URL, OUTPUT_FILE)
