import requests
import re
import os
from datetime import datetime, timezone

# --- Konfigurasi ---
M3U_FILE = 'live.m3u'
OPENLIGADB_BASE_URL = 'https://api.openligadb.de/getmatchdata/'

# Daftar liga yang ingin Anda lacak (diperbarui setiap tahun, gunakan tahun 2026 sebagai contoh)
LIGA_CODES = {
    'pl1/2026': 'Premier League',   # Inggris
    'bl1/2026': 'Bundesliga',      # Jerman
    'es1/2026': 'La Liga',         # Spanyol
    'it1/2026': 'Serie A',         # Italia
    'fr1/2026': 'Ligue 1',         # Prancis
    'cl/2026': 'Champions League'  # UCL
}

TARGET_GROUP_TITLE = 'SPORTS LIVE'
START_TAG = '##### SPORTS CHANNEL #####'

# --- Informasi Statis untuk Acara Besar ---
# Perkiraan Tanggal SEA Games 2026 (November - Desember) di Thailand
SEA_GAMES_INFO = [
    "--- PEMBERITAHUAN ACARA BESAR ---",
    "SEA Games 2026: Bangkok, Thailand (TBD: Nov - Des 2026)",
    "Pastikan saluran LIGA 1 (BRI) dan saluran SPORTS lain aktif pada hari pertandingan!"
]

def get_live_matches(codes):
    """Mengambil dan menggabungkan data pertandingan hari ini dari semua liga."""
    all_matches_info = []
    # Set zona waktu ke UTC
    tz = timezone.utc
    today_utc = datetime.now(tz).date() 

    for code_year, league_name in codes.items():
        api_url = f"{OPENLIGADB_BASE_URL}{code_year}"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error mengambil data untuk {league_name}: {e}")
            continue

        for match in data:
            match_date_str = match.get('matchDateTimeUTC')
            
            if not match_date_str:
                continue
                
            match_time_utc = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
            match_date = match_time_utc.date()
            
            # Filter: Hanya pertandingan hari ini dan belum selesai
            if match_date == today_utc and not match.get('matchIsFinished', True):
                team1 = match.get('team1', {}).get('shortName') or match.get('team1', {}).get('teamName', 'TBA')
                team2 = match.get('team2', {}).get('shortName') or match.get('team2', {}).get('teamName', 'TBA')
                
                # Konversi waktu ke WIB (UTC+7, Indonesia) untuk tampilan
                # Menggunakan offset +7 jam dari UTC
                wib_time = match_time_utc.astimezone(tz).replace(tzinfo=None) + timezone.timedelta(hours=7)
                wib_time_str = wib_time.strftime('%H:%M WIB')
                
                match_info = f"[{league_name}] {team1} vs {team2} @ {wib_time_str}"
                all_matches_info.append(match_info)

    return all_matches_info

def update_m3u_file(matches, extra_info):
    """Membaca file M3U dan menyisipkan info pertandingan di bawah START_TAG."""
    if not os.path.exists(M3U_FILE):
        print(f"File M3U '{M3U_FILE}' tidak ditemukan.")
        return

    with open(M3U_FILE, 'r') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    changes_made = False
    
    # 1. Konstruksi Konten Dinamis (Pertandingan)
    dynamic_insertion_block = []
    if matches:
        dynamic_insertion_block.append(f"#EXTGRP: ⚽ LIVE FOOTBALL TODAY - {datetime.now().strftime('%d %b %Y')}\n")
        for match in matches:
            dynamic_insertion_block.append(f"#EXTGRP: {match}\n")
    else:
        dynamic_insertion_block.append(f"#EXTGRP: No Major Live Football Matches Scheduled Today\n")
    
    # 2. Konstruksi Konten Statis (SEA Games, dll.)
    static_insertion_block = [f"##################### PENGUMUMAN ACARA BESAR #####################\n"]
    for info in extra_info:
        static_insertion_block.append(f"#EXTGRP: {info}\n")
    static_insertion_block.append(f"##################################################################\n")

    full_insertion_block = dynamic_insertion_block + static_insertion_block


    # 3. Proses file M3U
    while i < len(lines):
        line = lines[i]
        
        if line.strip() == START_TAG:
            new_lines.append(line)
            
            # Lewati/Hapus blok konten lama (dinamis dan statis)
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                # Kriteria untuk baris yang harus dihapus:
                # Dimulai dengan #EXTGRP: (baik dinamis maupun statis)
                # Adalah baris separator '####...'
                # Adalah baris kosong atau hanya '#'
                if (next_line.startswith('#EXTGRP:') or 
                    next_line.startswith('######') or
                    next_line.startswith('# Match info di atas') or
                    next_line == '#' or next_line == ''):
                    j += 1
                    changes_made = True 
                elif next_line.startswith('#EXTINF:'):
                    # Hentikan pembersihan jika menemukan channel baru
                    break
                else:
                    j += 1
            
            # Sisipkan blok informasi pertandingan dan info tambahan baru
            new_lines.extend(full_insertion_block)
            i = j - 1 # Lanjutkan loop dari baris setelah konten yang dihapus/disisipkan
            changes_made = True
            
        else:
            new_lines.append(line)

        i += 1

    if changes_made:
        # Tulis kembali file hanya jika ada perubahan
        with open(M3U_FILE, 'w') as f:
            f.writelines(new_lines)
        print(f"File M3U '{M3U_FILE}' berhasil diperbarui dengan data multi-liga dan info SEA Games.")
    else:
        print("Tidak ada perubahan yang dilakukan pada konten pertandingan.")


if __name__ == "__main__":
    live_matches = get_live_matches(LIGA_CODES)
    # Panggil fungsi update dengan data pertandingan dan info statis SEA Games
    update_m3u_file(live_matches, SEA_GAMES_INFO)
