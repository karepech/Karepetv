import requests
import re
import os
from datetime import datetime, timezone, timedelta

# --- Konfigurasi ---
M3U_FILE = 'live.m3u'
# Kunci API akan dimuat secara otomatis dari GitHub Secrets
API_KEY = os.environ.get('FOOTBALL_API_KEY') 
API_BASE_URL = 'https://v3.football.api-sports.io/'

# --- ID Liga di API-Sports (Harap perbarui tahunnya saat musim berganti!) ---
# ID Liga untuk Premier League, La Liga, Bundesliga, dan UCL (Hanya contoh)
LIGA_IDS = {
    39: 'Premier League',   
    140: 'La Liga',         
    78: 'Bundesliga',       
    2: 'Champions League',  
    # Tambahkan ID Liga lain jika Anda menemukannya di dokumentasi API-Sports
}

# --- PEMETAAN (HARDCODE) CHANNEL KE LIGA ---
# Asumsi: Pertandingan Liga Prioritas pertama disiarkan di Bein 1, kedua di Bein 2, dst.
CHANNEL_MAPPING = {
    # PENTING: Nama channel di sini harus PERSIS SAMA dengan yang ada di file live.m3u Anda.
    'beIN Sports ID 1': [39, 140], 
    'beIN Sports ID 2': [39, 78], 
    'beIN Sports ID 3': [140, 78], 
}

# --- INFORMASI STATIS YANG HARUS ANDA UPDATE SECARA MANUAL ---
# Informasi ini akan muncul di header M3U setiap hari
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

START_TAG = '##### SPORTS CHANNEL #####'
UPDATE_TAG_HEADER = "#EXTGRP: ⚽ LIVE FOOTBALL TODAY"

# Header yang dibutuhkan oleh API-Sports
HEADERS = {
    'x-apisports-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

def get_live_matches_apisports():
    """Mengambil data pertandingan yang akan datang hari ini dari API-Sports."""
    if not API_KEY:
        print("API_KEY tidak ditemukan. Gagal mengambil data.")
        return [], {}

    # Menggunakan tanggal hari ini untuk filter
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    current_year = datetime.now().year
    all_matches_info = []
    channel_updates = {}
    
    league_ids_str = '-'.join(map(str, LIGA_IDS.keys()))
    
    # Endpoint untuk mengambil fixtures berdasarkan tanggal dan ID liga
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

    # Sortir fixtures berdasarkan waktu (yang paling awal muncul di Bein 1)
    fixtures.sort(key=lambda x: x['fixture']['timestamp'])

    match_index = 0
    
    for fixture in fixtures:
        match_info = fixture['fixture']
        league_info = fixture['league']
        team1 = fixture['teams']['home']['name']
        team2 = fixture['teams']['away']['name']
        league_id = league_info['id']
        league_name = LIGA_IDS.get(league_id, 'Unknown League')

        # Konversi waktu Unix Timestamp ke WIB (UTC+7)
        match_time_utc = datetime.fromtimestamp(match_info['timestamp'], tz=timezone.utc)
        wib_time = match_time_utc.astimezone(timezone.utc) + timedelta(hours=7)
        wib_time_str = wib_time.strftime('%H:%M WIB')

        match_info_full = f"[{league_name}] {team1} vs {team2} @ {wib_time_str}"
        # Nama channel baru (hanya nama tim yang disingkat)
        match_info_short = f"{team1.split()[0]} vs {team2.split()[0]} LIVE" 
        all_matches_info.append(match_info_full)

        # Logika Pemetaan Channel ke 3 Bein Sports pertama
        if match_index == 0 and league_id in CHANNEL_MAPPING.get('beIN Sports ID 1', []):
            channel_updates['beIN Sports ID 1'] = match_info_short
        elif match_index == 1 and league_id in CHANNEL_MAPPING.get('beIN Sports ID 2', []):
            channel_updates['beIN Sports ID 2'] = match_info_short
        elif match_index == 2 and league_id in CHANNEL_MAPPING.get('beIN Sports ID 3', []):
            channel_updates['beIN Sports ID 3'] = match_info_short
        
        match_index += 1
        if match_index >= 3:
            # Hanya memproses 3 channel Bein Sports untuk penggantian nama dinamis
            pass 
            
    return all_matches_info, channel_updates

def update_m3u_file(matches, hardcode_events, sea_games_info, channel_updates):
    """Membaca file M3U, menyisipkan info, dan memperbarui nama channel."""
    if not os.path.exists(M3U_FILE):
        print(f"File M3U '{M3U_FILE}' tidak ditemukan.")
        return

    with open(M3U_FILE, 'r') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    changes_made = False
    
    # 1. Konstruksi Blok Sisipan Penuh (Header/Event Info)
    full_insertion_block = [f"##################### EVENT INFORMATION - {datetime.now().strftime('%d %b %Y')} #####################\n"]
    
    for info in hardcode_events:
        full_insertion_block.append(f"#EXTGRP: {info}\n")
        
    full_insertion_block.append(f"------------------------------------------------------------------\n")
    if matches:
        full_insertion_block.append(f"{UPDATE_TAG_HEADER}\n")
        for match in matches:
            full_insertion_block.append(f"#EXTGRP: {match}\n")
    else:
        full_insertion_block.append(f"#EXTGRP: No Major Live Football Matches Scheduled Today (Source: API-Sports)\n")
        
    full_insertion_block.append(f"------------------------------------------------------------------\n")
    for info in sea_games_info:
        full_insertion_block.append(f"#EXTGRP: {info}\n")
    full_insertion_block.append(f"##################################################################\n")
    
    # 2. Proses File M3U (Memperbarui Nama Channel dan Menyisipkan Header)
    channel_name_pattern = re.compile(r'#EXTINF:.*,(.*)')
    
    while i < len(lines):
        line = lines[i]
        
        # A. HANDLE INSERTION BLOCKS (di bawah START_TAG)
        if line.strip() == START_TAG:
            new_lines.append(line)
            
            # Hapus baris konten lama yang disisipkan (dimulai dari baris setelah START_TAG)
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                # Kriteria baris yang akan dihapus:
                if (next_line.startswith('#EXTGRP:') or 
                    next_line.startswith('######') or
                    next_line.startswith('---') or
                    next_line.startswith('#EXTGRP: ⚽ LIVE FOOTBALL TODAY') or
                    next_line.startswith('# Match info di atas') or
                    next_line == '#' or next_line == ''):
                    j += 1
                elif next_line.startswith('#EXTINF:'):
                    # Hentikan pembersihan jika menemukan channel baru
                    break
                else:
                    j += 1
            
            # Sisipkan blok informasi Penuh
            new_lines.extend(full_insertion_block)
            i = j - 1
            changes_made = True
            
        # B. HANDLE CHANNEL NAME UPDATE (di semua baris)
        elif line.startswith('#EXTINF:'):
            match_extinf = channel_name_pattern.search(line)
            if match_extinf:
                current_channel_name = match_extinf.group(1).strip()
                
                # Periksa apakah nama channel ini harus diubah
                for target_name, new_match_info in channel_updates.items():
                    # Mencocokkan nama saluran
                    if target_name in current_channel_name: 
                        # Ganti nama lama dengan nama baru (match info)
                        # Kita harus memastikan hanya channel yang TIDAK sedang disiarkan yang dikembalikan ke nama aslinya
                        new_line = line.replace(current_channel_name, new_match_info)
                        new_lines.append(new_line)
                        changes_made = True
                        break
                else:
                    # Jika tidak ada perubahan dinamis, pastikan nama channel dikembalikan ke nama aslinya 
                    # jika sebelumnya diubah oleh action. 
                    
                    # LOGIKA PENGEMBALIAN NAMA ASLI (fallback)
                    # Jika nama channel saat ini adalah nama pertandingan (ada 'vs' dan 'LIVE')
                    is_dynamic_name = 'vs' in current_channel_name and 'LIVE' in current_channel_name
                    
                    # Cek di baris M3U Anda, nama asli Bein Sports adalah:
                    # "beIN Sports ID 1", "beIN Sports ID 2", "beIN Sports ID 3"
                    original_name = None
                    if 'beIN Sports ID 1' in lines[i-1] or 'beIN Sports ID 1' in lines[i+1]:
                        original_name = 'beIN Sports ID 1'
                    elif 'beIN Sports ID 2' in lines[i-1] or 'beIN Sports ID 2' in lines[i+1]:
                        original_name = 'beIN Sports ID 2'
                    elif 'beIN Sports ID 3' in lines[i-1] or 'beIN Sports ID 3' in lines[i+1]:
                        original_name = 'beIN Sports ID 3'
                        
                    if is_dynamic_name and original_name not in channel_updates.keys():
                         new_line = line.replace(current_channel_name, original_name)
                         new_lines.append(new_line)
                         changes_made = True
                    else:
                        new_lines.append(line)


        # C. HANDLE LINE BIASA (tetap sama)
        else:
            new_lines.append(line)

        i += 1

    if changes_made:
        with open(M3U_FILE, 'w') as f:
            f.writelines(new_lines)
        print(f"File M3U '{M3U_FILE}' berhasil diperbarui.")
    else:
        print("Tidak ada perubahan yang dilakukan.")


if __name__ == "__main__":
    live_matches, channel_updates = get_live_matches_apisports()
    update_m3u_file(live_matches, HARDCODE_EVENTS, SEA_GAMES_INFO, channel_updates)
