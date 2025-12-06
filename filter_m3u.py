import requests
import re 

# Konfigurasi
SOURCE_URL = "https://dildo.beww.pl/ngen.m3u" 
OUTPUT_FILE = "live_events.m3u"

# Kunci utama adalah frasa "LIVE NOW" di group-title
LIVE_CATEGORY_PHRASE = "LIVE NOW"

# Regular Expression untuk mengambil group-title
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)

def filter_m3u(source_url, output_file):
    """Mengunduh dan memfilter playlist M3U berdasarkan group-title "LIVE NOW"."""
    
    try:
        # 1. Unduh konten M3U
        print(f"Mengunduh M3U dari: {source_url}")
        response = requests.get(source_url, timeout=30)
        response.raise_for_status()
        content = response.text.splitlines()
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengunduh M3U: {e}")
        return

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
                
                # b. Lakukan pemeriksaan filter: Cek apakah group-title mengandung "LIVE NOW"
                # Menggunakan startswith untuk akurasi tinggi
                is_live_category = group_title.upper().startswith(LIVE_CATEGORY_PHRASE)
                
                if is_live_category:
                    filtered_lines.append(line)
                    filtered_lines.append(stream_url)
                    num_entries += 1
                
                i += 2 # Lompati ke baris setelah URL stream
                continue
        
        i += 1
        
    # 3. Simpan konten yang sudah difilter
    print(f"Ditemukan {num_entries} live event yang difilter.")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(filtered_lines) + '\n')
    
    print(f"Playlist yang difilter berhasil disimpan ke {output_file}")


if __name__ == "__main__":
    filter_m3u(SOURCE_URL, OUTPUT_FILE)
