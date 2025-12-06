import requests
import re
import os
from datetime import datetime, timezone, timedelta

# --- Konfigurasi File ---
SOURCE_M3U_FILE = 'live.m3u'      
TARGET_M3U_FILE = 'live_dynamic.m3u' 

# --- Konfigurasi API ---
API_KEY = os.environ.get('FOOTBALL_API_KEY') 
API_BASE_URL = 'https://v3.football.api-sports.io/'

LIGA_IDS = {
    39: 'Premier League',   
    140: 'La Liga',         
    78: 'Bundesliga',       
    2: 'Champions League',  
}

# --- PEMETAAN (HARDCODE) CHANNEL KE LIGA ---
CHANNEL_MAPPING = {
    # PENTING: Nama channel di sini harus persis sama!
    'beIN Sports ID 1': [39, 140], 
    'beIN Sports ID 2': [39, 78], 
    'beIN Sports ID 3': [140, 78], 
}
BEIN_CHANNEL_NAMES = list(CHANNEL_MAPPING.keys())

# --- INFORMASI STATIS YANG HARUS ANDA UPDATE SECARA MANUAL ---
HARDCODE_EVENTS = [
    "--- PEMBERITAHUAN ACARA KHUSUS ---",
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
        return [], {}

    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    current_year = datetime.now().year
    all_matches_info = []
    channel_updates = {}
    
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
        return [], {}

    fixtures.sort(key=lambda x: x['fixture']['timestamp'])
    
    match_index = 0
    
    for fixture in fixtures:
        league_info = fixture['league']
        team1 = fixture['teams']['home']['name']
        team2 = fixture['teams']['away']['name']
        league_id = league_info['id']
        
        # Cek apakah pertandingan sudah dimulai (status 1-4) atau masih dijadwalkan (status 0)
        # Kita anggap "live" jika sudah dijadwalkan atau akan segera dimulai.
        # Untuk keakuratan, API-Sports menyediakan status: 'Time to be defined' (TBD), 'Not Started' (NS), 'Live' (1H, HT, 2H), 'Finished' (FT).
        # Kita hanya fokus pada 'Not Started' (NS) dan match time hari ini.
        
        match_time_utc = datetime.fromtimestamp(fixture['fixture']['timestamp'], tz=timezone.utc)
        wib_time = match_time_utc.astimezone(timezone.utc) + timedelta(hours=7)
        wib_time_str = wib_time.strftime('%H:%M WIB')

        match_info_full = f"[{LIGA_IDS.get(league_id, 'Unknown')}] {team1} vs {team2} @ {wib_time_str}"
        all_matches_info.append(match_info_full)

        # Logika Pemetaan Channel ke 3 Bein Sports pertama
        if match_index == 0 and league_id in CHANNEL_MAPPING.get('beIN Sports ID 1', []):
            channel_updates['beIN Sports ID 1'] = f"{team1.split()[0]} vs {team2.split()[0]} LIVE"
        elif match_index == 1 and league_id in CHANNEL_MAPPING.get('beIN Sports ID 2', []):
            channel_updates['beIN Sports ID 2'] = f"{team1.split()[0]} vs {team2.split()[0]} LIVE"
        elif match_index == 2 and league_id in CHANNEL_MAPPING.get('beIN Sports ID 3', []):
            channel_updates['beIN Sports ID 3'] = f"{team1.split()[0]} vs {team2.split()[0]} LIVE"
        
        match_index += 1
        if match_index >= 3:
            break 
            
    return all_matches_info, channel_updates

def generate_new_m3u(matches, hardcode_events, sea_games_info, channel_updates):
    """Membaca file lama, memisahkan channel live, menambahkan header, dan menulis ke file baru."""
    if not os.path.exists(SOURCE_M3U_FILE):
        print(f"File sumber '{SOURCE_M3U_FILE}' tidak ditemukan. Menghentikan.")
        return False

    with open(SOURCE_M3U_FILE, 'r') as f:
        source_lines = f.readlines()
        
    new_m3u_content = []
    live_channels = [] # List untuk menyimpan channel Bein Sports yang dimodifikasi
    remaining_channels = [] # List untuk menyimpan channel M3U lainnya
    
    # --- 1. Pemrosesan File Sumber: Identifikasi dan Modifikasi Channel Live ---
    
    # Regex untuk mencari baris EXTINF dan URL yang mengikutinya
    extinf_pattern = re.compile(r'#EXTINF:.*,(.*)')
    
    i = 0
    while i < len(source_lines):
        line = source_lines[i]
        
        if line.startswith('#EXTINF:'):
            match_extinf = extinf_pattern.search(line)
            current_channel_name = match_extinf.group(1).strip() if match_extinf else ""
            
            # Cek apakah ini adalah salah satu channel Bein Sports dinamis
            is_dynamic_channel = current_channel_name in BEIN_CHANNEL_NAMES
            
            # Kumpulkan semua baris untuk satu channel (EXTINF, VLCOPT, URL, KODIPROP)
            channel_block = [line]
            
            # Cari baris-baris URL/option berikutnya
            j = i + 1
            while j < len(source_lines) and not source_lines[j].startswith('#EXTINF:'):
                channel_block.append(source_lines[j])
                j += 1
            
            # Pindah pointer i ke baris sebelum channel berikutnya
            i = j - 1
            
            # --- Modifikasi dan Kategorisasi ---
            
            # Jika channel ini adalah salah satu Bein Sports dan ada update
            if current_channel_name in channel_updates:
                new_name = channel_updates[current_channel_name]
                
                # Ganti nama channel di baris EXTINF pertama
                modified_extinf = channel_block[0].replace(current_channel_name, new_name)
                channel_block[0] = modified_extinf
                
                # Tambahkan ke daftar LIVE CHANNELS
                live_channels.extend(channel_block)
                
            # Jika channel adalah Bein Sports tapi TIDAK ada update (kembalikan ke nama asli)
            elif is_dynamic_channel and current_channel_name not in channel_updates:
                # Tambahkan ke daftar REMAINING CHANNELS (di bawah)
                remaining_channels.extend(channel_block)
                
            # Jika channel adalah channel lain (BRI LIGA 1, ASTRO, SPORTSTARS, dll.)
            else:
                remaining_channels.extend(channel_block)
                
        # Jika bukan EXTINF (komentar, separator, dll.)
        else:
            # Lewati semua baris separator lama di live.m3u Anda
            if line.strip().startswith('###') or line.strip().startswith('####') or line.strip().startswith('=='):
                pass
            else:
                remaining_channels.append(line)

        i += 1
        
    # --- 2. Konstruksi File M3U Baru ---
    
    new_m3u_content.append("#EXTM3U\n")

    # A. Blok Informasi Dinamis (Header Event dan Jadwal)
    new_m3u_content.append(f"##################### EVENT INFORMATION - {datetime.now().strftime('%d %b %Y')} #####################\n")
    for info in hardcode_events:
        new_m3u_content.append(f"#EXTGRP: {info}\n")
    new_m3u_content.append(f"------------------------------------------------------------------\n")
    
    if matches:
        new_m3u_content.append(f"#EXTGRP: ⚽ ALL LIVE FOOTBALL TODAY\n")
        for match in matches:
            new_m3u_content.append(f"#EXTGRP: {match}\n")
    else:
        new_m3u_content.append(f"#EXTGRP: No Major Live Football Matches Scheduled Today (Source: API-Sports)\n")
        
    new_m3u_content.append(f"------------------------------------------------------------------\n")
    for info in sea_games_info:
        new_m3u_content.append(f"#EXTGRP: {info}\n")
    new_m3u_content.append(f"##################################################################\n\n")

    # B. Saluran LIVE SEKARANG (Yang Namanya Diubah dan Dipindah ke Atas)
    if live_channels:
        new_m3u_content.append(f"##################### ⚡ LIVE NOW (LIVE MATCH CHANNEL) ⚡ #####################\n")
        new_m3u_content.extend(live_channels)
        new_m3u_content.append(f"##################################################################\n\n")

    # C. Sisa Saluran
    new_m3u_content.append(f"##################### ALL OTHER SPORTS CHANNELS #####################\n")
    new_m3u_content.extend(remaining_channels)
    new_m3u_content.append(f"\n# Diperbarui oleh GitHub Action pada {datetime.now().strftime('%d/%m/%Y %H:%M:%S WIB')}")


    # Tulis ke file baru
    with open(TARGET_M3U_FILE, 'w') as f:
        f.writelines(new_m3u_content)
        
    print(f"File M3U baru '{TARGET_M3U_FILE}' berhasil dibuat dan diperbarui. {len(live_channels)//2} channel dipindah ke LIVE NOW.")
    return True


if __name__ == "__main__":
    live_matches, channel_updates = get_live_matches_apisports()
    generate_new_m3u(live_matches, HARDCODE_EVENTS, SEA_GAMES_INFO, channel_updates)

