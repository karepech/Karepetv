import requests
import re
import os
from datetime import datetime, timezone, timedelta

# --- Konfigurasi File ---
SOURCE_M3U_FILE = 'live.m3u'      # File M3U lama (dibaca)
TARGET_M3U_FILE = 'live_dynamic.m3u' # File M3U baru (ditulis)

# --- Konfigurasi API ---
API_KEY = os.environ.get('FOOTBALL_API_KEY') 
API_BASE_URL = 'https://v3.football.api-sports.io/'

LIGA_IDS = {
    39: 'Premier League',   
    140: 'La Liga',         
    78: 'Bundesliga',       
    2: 'Champions League',  
}

# --- INFORMASI STATIS YANG HARUS ANDA UPDATE SECARA MANUAL ---
HARDCODE_EVENTS = [
    "--- PEMBERITAHUAN ACARA KHUSUS ---",
    "BEIN SPORTS: Jadwal diperbarui otomatis jika ada pertandingan hari ini (PL, La Liga, BL)!",
    "BRI LIGA 1: Cek jadwal terkini di saluran PEGADAIAN CHAMPIONSHIP!",
    "WWE EVENTS: Cek jadwal mingguan Raw/SmackDown/PPV!",
    "------------------------------------"
]

SEA_GAMES_INFO = [
    "SEA Games 2026: Bangkok, Thailand (TBD: Nov - Des 2026)",
    "Pastikan saluran LIGA 1 (BRI) dan saluran SPORTS lain aktif saat event berlangsung!"
]

HEADERS = {
    'x-apisports-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

def get_live_matches_apisports():
    """Mengambil data pertandingan yang akan datang hari ini dari API-Sports."""
    if not API_KEY:
        print("API_KEY tidak ditemukan. Gagal mengambil data.")
        return []

    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    current_year = datetime.now().year
    all_matches_info = []
    
    league_ids_str = '-'.join(map(str, LIGA_IDS.keys()))
    params = {
        'date': today_date,
        'season': current_year,
        'league': league_ids_str
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}fixtures", headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        fixtures = data.get('response', [])
        
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengambil data dari API-Sports: {e}")
        return []

    fixtures.sort(key=lambda x: x['fixture']['timestamp'])
    
    for fixture in fixtures:
        league_info = fixture['league']
        team1 = fixture['teams']['home']['name']
        team2 = fixture['teams']['away']['name']
        league_id = league_info['id']
        league_name = LIGA_IDS.get(league_id, 'Unknown League')

        match_time_utc = datetime.fromtimestamp(fixture['fixture']['timestamp'], tz=timezone.utc)
        wib_time = match_time_utc.astimezone(timezone.utc) + timedelta(hours=7)
        wib_time_str = wib_time.strftime('%H:%M WIB')

        match_info_full = f"[{league_name}] {team1} vs {team2} @ {wib_time_str}"
        all_matches_info.append(match_info_full)
            
    return all_matches_info

def generate_new_m3u(matches, hardcode_events, sea_games_info):
    """Membaca file lama, menambahkan header, dan menulis ke file baru."""
    if not os.path.exists(SOURCE_M3U_FILE):
        print(f"File sumber '{SOURCE_M3U_FILE}' tidak ditemukan. Menghentikan.")
        return False

    with open(SOURCE_M3U_FILE, 'r') as f:
        source_lines = f.readlines()
        
    new_m3u_content = []
    
    # --- 1. Header M3U Standard ---
    new_m3u_content.append("#EXTM3U\n")

    # --- 2. Blok Informasi Dinamis ---
    new_m3u_content.append(f"##################### EVENT INFORMATION - {datetime.now().strftime('%d %b %Y')} #####################\n")
    
    for info in hardcode_events:
        new_m3u_content.append(f"#EXTGRP: {info}\n")
        
    new_m3u_content.append(f"------------------------------------------------------------------\n")
    
    if matches:
        new_m3u_content.append(f"#EXTGRP: ⚽ LIVE FOOTBALL TODAY\n")
        for match in matches:
            new_m3u_content.append(f"#EXTGRP: {match}\n")
    else:
        new_m3u_content.append(f"#EXTGRP: No Major Live Football Matches Scheduled Today (Source: API-Sports)\n")
        
    new_m3u_content.append(f"------------------------------------------------------------------\n")
    for info in sea_games_info:
        new_m3u_content.append(f"#EXTGRP: {info}\n")
    new_m3u_content.append(f"##################################################################\n\n")

    # --- 3. Masukkan Semua Channel dari File Lama ---
    
    # Hapus semua baris sebelum channel pertama (#EXTINF)
    found_first_channel = False
    for line in source_lines:
        if line.startswith('#EXTINF:'):
            found_first_channel = True
        
        # Tambahkan hanya baris yang merupakan channel atau di bawah channel pertama
        if found_first_channel:
            new_m3u_content.append(line)

    # Tulis ke file baru
    with open(TARGET_M3U_FILE, 'w') as f:
        f.writelines(new_m3u_content)
        
    print(f"File M3U baru '{TARGET_M3U_FILE}' berhasil dibuat dan diperbarui.")
    return True


if __name__ == "__main__":
    live_matches = get_live_matches_apisports()
    generate_new_m3u(live_matches, HARDCODE_EVENTS, SEA_GAMES_INFO)
