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
LIGA_IDS = {
    39: 'Premier League',   
    140: 'La Liga',         
    78: 'Bundesliga',       
    2: 'Champions League',  
}

# --- PEMETAAN (HARDCODE) CHANNEL KE LIGA ---
CHANNEL_MAPPING = {
    # Nama channel di sini harus PERSIS SAMA dengan yang ada di live.m3u Anda.
    'beIN Sports ID 1': [39, 140], 
    'beIN Sports ID 2': [39, 78], 
    'beIN Sports ID 3': [140, 78], 
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

    match_index =
