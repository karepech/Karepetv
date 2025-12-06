import requests
import re # Digunakan untuk Regular Expressions

# Konfigurasi
SOURCE_URL = "https://dildo.beww.pl/ngen.m3u" 
OUTPUT_FILE = "live_events.m3u"
# Kata kunci filter:
# 1. Kategori (group-title) harus mengandung salah satu kata kunci ini
CATEGORY_KEYWORDS = ["live", "event", "sport"]
# 2. Nama Saluran (#EXTINF) harus mengandung salah satu kata kunci ini
CHANNEL_KEYWORDS = ["live", "event", "langsung", "match"]

# Regular Expression untuk mengambil group-title dan channel name
# Regex ini mencari pola group-title="..." dan nama saluran (setelah koma)
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)
CHANNEL_NAME_REGEX = re.compile(r',([^,]*)$')

def is_match(text, keywords):
    """Mengecek apakah teks mengandung salah satu kata kunci."""
    return any(keyword.lower() in text.lower() for keyword in keywords)

def filter_m3u(source_url, output_file):
    """Mengunduh dan memfilter playlist M3U berdasarkan group-title dan nama saluran."""
    
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
    
    # 2. Proses konten baris demi baris
    i = 0
    num_entries = 0
    while i < len(content):
        line = content[i].strip()
        
        if line.startswith("#EXTINF"):
            # Baris berikutnya diharapkan adalah URL streaming
            if i + 1 < len(content):
                stream_url = content[i+1].strip()
                
                # a. Ekstrak group-title
                group_match = GROUP_TITLE_REGEX.search(line)
                group_title = group_match.group(1) if group_match else ""
                
                # b. Ekstrak nama saluran
                name_match = CHANNEL_NAME_REGEX.search(line)
                channel_name = name_match.group(1).strip() if name_match else ""
                
                # c. Lakukan pemeriksaan filter
                is_live_category = is_match(group_title, CATEGORY_KEYWORDS)
                is_live_channel = is_match(channel_name, CHANNEL_KEYWORDS)
                
                # Jika salah satu kriteria terpenuhi (di kategori ATAU di nama saluran)
                if is_live_category or is_live_channel:
                    filtered_lines.append(line)
                    filtered_lines.append(stream_url)
                    num_entries += 1
                
                # Lompati ke baris setelah URL stream
                i += 2
                continue
        
        i += 1 # Pindah ke baris berikutnya
        
    # 3. Simpan konten yang sudah difilter
    print(f"Ditemukan {num_entries} live event yang difilter.")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(filtered_lines) + '\n')
    
    print(f"Playlist yang difilter berhasil disimpan ke {output_file}")


if __name__ == "__main__":
    filter_m3u(SOURCE_URL, OUTPUT_FILE)
