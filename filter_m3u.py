import requests
import os

# Konfigurasi
SOURCE_URL = "https://dildo.beww.pl/ngen.m3u" 
# Ganti nama file output menjadi 'full_playlist.m3u'
OUTPUT_FILE = "full_playlist.m3u" 

def download_m3u(source_url, output_file):
    """Mengunduh seluruh konten M3U tanpa filter."""
    
    try:
        print(f"Mengunduh seluruh konten M3U dari: {source_url}")
        # Timeout diset ke 60 detik
        response = requests.get(source_url, timeout=60) 
        response.raise_for_status() # Akan memicu exception jika kode status >= 400
        content = response.text
        
        # >>>>>> DEBUGGING OUTPUT <<<<<<
        print(f"Status Koneksi: {response.status_code}") 
        print(f"Ukuran konten yang berhasil diunduh (karakter): {len(content)}") 
        # >>>>>> DEBUGGING OUTPUT <<<<<<

    except requests.exceptions.RequestException as e:
        print(f"FATAL ERROR: Gagal mengunduh atau koneksi terputus: {e}")
        exit(1) 

    # 2. Simpan konten yang sudah diunduh langsung ke file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Seluruh playlist berhasil disimpan ke {output_file}")


if __name__ == "__main__":
    download_m3u(SOURCE_URL, OUTPUT_FILE)
