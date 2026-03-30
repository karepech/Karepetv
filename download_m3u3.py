import requests
import re
import concurrent.futures
import random
import urllib3
import gzip
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io import BytesIO

# Matikan peringatan SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ====================================================================
# I. KONFIGURASI GLOBAL & EPG
# ====================================================================

MASTER_URLS = [
    "https://ch-cub.disini.workers.dev",
    "https://deccotech.online/tv/tvstream.html", 
    "https://freeiptv2026.tsender57.workers.dev", 
    "https://raw.githubusercontent.com/tvplaylist/T2/refs/heads/main/tv1",
    "http://sauridigital.my.id/kerbaunakal/2026TVGNS.html", 
    "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25",
    "https://semar25.short.gy",
    "https://bit.ly/TVKITKAT",
    "https://liveevent.iptvbonekoe.workers.dev",
    "https://bwifi.my.id/lokal",
    "https://bit.ly/KPL203"
]

EPG_URLS = [
    "https://raw.githubusercontent.com/AqFad2811/epg/main/indonesia.xml",
    "https://epgshare01.online/epgshare01/epg_ripper_ALL_SPORTS.xml.gz"
]

ALL_POSITIVE_KEYWORDS = {
    "EVENT_ONLY": ["EVENT", "SEA GAMES", "PREMIER LEAGUE", "LA LIGA", "SERIE A", "BUNDESLIGA", "LIGUE 1", "EREDIVISIE", "LIGA 1 INDONESIA", "LIGA PRO SAUDI"],
    "SPORTS_LIVE": ["SPORT", "SPORTS", "LIVE", "LANGSUNG", "OLAHRAGA", "MATCH", "LIGA", "FOOTBALL", "BEIN", "SPOTV", "BE IN", "CTV", "DAZN", "ELEVEN", "ZIGGO", "SSC", "HUB", "PREMIER", "SETANTA", "PRIMA", "FUBO", "ARENA"],
    "INDONESIA": [
        "INDONESIA", "NASIONAL", "LOKAL", "DAERAH",
        "RCTI", "SCTV", "INDOSIAR", "TRANS", "MNC", "GTV", "GLOBAL TV", 
        "TVRI", "BTV", "JAK TV", "JTV", "RTV", "NET TV", "DAAI",
        "INEWS", "TVONE", "TV ONE", "METRO", "KOMPAS" 
    ],
    "KIDS": [
        "KIDS", "ANAK", "CARTOON", "KARTUN", "NICKELODEON", "NICK JR", 
        "DISNEY", "CARTOON NETWORK", "BOOMERANG", "BABY", 
        "ANIMATION", "ANIMASI", "TOON", "CERIA", "MENTARI", "YEYA"
    ],
    "KNOWLEDGE": [
        "KNOWLEDGE", "EDUCATION", "EDUKASI", "PENGETAHUAN", "DISCOVERY", 
        "NATIONAL GEOGRAPHIC", "NAT GEO", "NATGEO", "HISTORY", 
        "ANIMAL PLANET", "SCIENCE", "SAINS", "DOCUMENTARY", "DOKUMENTER", "WILD"
    ],
    "NEWS": [
        "NEWS", "BERITA", "INFORMASI", "CNN", "CNBC", "AL JAZEERA", "BBC", "CNA", "BLOOMBERG", "CCTV"
    ],
    "RELIGI": [
        "RELIGI", "ISLAM", "MUSLIM", "ROHANI", "DAKWAH", "NGAJI", 
        "SUNNAH", "QURAN", "RODJA", "WESAL", "INSAN", "SURAU", 
        "TVMU", "MTA", "KHAZANAH", "MADINAH", "MAKKAH", "NABAWI", "UMMAT"
    ]
}

GLOBAL_BLACKLIST_URLS = {
    "https://bit.ly/428RaFW", "https://iili.io/KfT7PJ2.jpg",
    "https://drive.google.com/uc?export=download&id=12slpj4XW5B5SlR9lruuZ77_NPtTHKKw8&usp",
    "https://shorter.me/SNozg", "https://mimipipi22.github.io/logo/offline.m3u8",
    "https://dn720407.ca.archive.org/0/items/warkop-dki-mana-tahan/Warkop%20DKI%20-%20Mana%20Tahan.mp4",
    "https://mantul.biz.id:443/inetwork/gayanet12/19132.ts",
    "http://sauridigital.my.id/infogeulis/JOIN%20GROUP.mp4",
    "https://sauridigital.my.id/infogeulis/DONASI%20DANA.mp4",
    "https://kuk1.modprimus.cfd/kuk3/usergendx0slfk9QssDx9lgxlsdmqrnd.m3u8",
    "https://kuk1.modprimus.cfd/kuk2/usergendx0ul2J8tsDx9lgcddwqrnd.m3u8",
    "https://kudos111.terranovax1.cfd/kuk4/usergendx0thc60skrdnnd.m3u8",
    "https://pulse1.zalmora.cfd/kuk1/usergendx472snx93kdgwqrnd.m3u8",
}

CONFIGURATIONS = [
    {"output_file": "event_combined.m3u", "keywords": ALL_POSITIVE_KEYWORDS["EVENT_ONLY"], "exclude_keywords": ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"], "category_name": "LIVE EVENT SPORTS", "force_category": True, "require_time": True, "description": "EVENT: Gabungan Event Olahraga (Wajib Berjadwal)"},
    {"output_file": "sports_combined.m3u", "keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"], "exclude_keywords": ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"], "category_name": "SPORTS", "force_category": True, "require_time": False, "description": "SPORTS: Gabungan Live"},
    {"output_file": "indonesia_combined.m3u", "keywords": ALL_POSITIVE_KEYWORDS["INDONESIA"], "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"], "category_name": "INDONESIA", "force_category": True, "require_time": False, "description": "INDONESIA: Gabungan TV Indonesia Murni"},
    {"output_file": "kids_combined.m3u", "keywords": ALL_POSITIVE_KEYWORDS["KIDS"], "exclude_keywords": ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"], "category_name": "KIDS", "force_category": True, "require_time": False, "description": "KIDS: Gabungan Saluran Anak"},
    {"output_file": "knowledge_combined.m3u", "keywords": ALL_POSITIVE_KEYWORDS["KNOWLEDGE"], "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"], "category_name": "KNOWLEDGE", "force_category": True, "require_time": False, "description": "KNOWLEDGE: Gabungan Saluran Edukasi"},
    {"output_file": "news_combined.m3u", "keywords": ALL_POSITIVE_KEYWORDS["NEWS"], "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"] + ALL_POSITIVE_KEYWORDS["INDONESIA"], "category_name": "NEWS", "force_category": True, "require_time": False, "description": "NEWS: Gabungan Saluran Berita Internasional"},
    {"output_file": "religi_combined.m3u", "keywords": ALL_POSITIVE_KEYWORDS["RELIGI"], "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"], "category_name": "RELIGI", "force_category": True, "require_time": False, "description": "RELIGI: Gabungan Saluran Dakwah & Rohani"},
]

# Regex
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)
TVG_ID_REGEX = re.compile(r'tvg-id="([^"]*)"', re.IGNORECASE)
CLEANING_REGEX = re.compile(r'[^a-zA-Z0-9\s]+')
TIME_PATTERN_REGEX = re.compile(r'\b(?:[01]?[0-9]|2[0-3])[:.][0-5][0-9]\s*WIB\b', re.IGNORECASE)
SPAM_KEYWORDS = ['EXTVLCOPT', 'USER-AGENT', 'GECKO', 'CHROME', 'SAFARI', 'WINK', 'MOZILLA', 'APPLEWEBKIT', 'HTTP']

# Data Penampung
CATEGORIZED_URLS = set()
CATEGORY_LOGS = {} 
VALID_EPGS_DICT = {}
REVERSE_EPG_DICT = {}

# Warna Cetak
C_GREEN = '\033[92m'
C_RED = '\033[91m'
C_YELLOW = '\033[93m'
C_ORANGE = '\033[38;5;208m'
C_CYAN = '\033[96m'
C_RESET = '\033[0m'

# ====================================================================
# II. FUNGSI PARSING EPG & UTILITAS
# ====================================================================

def clean_channel_for_lookup(name):
    return CLEANING_REGEX.sub('', name).upper().replace(" ", "")

def load_epg_databases():
    print("[+] Mengunduh dan Membaca Database EPG XML...")
    session = requests.Session()
    for url in EPG_URLS:
        try:
            print(f"  > Mengambil EPG: {url}")
            resp = session.get(url, timeout=30, verify=False)
            resp.raise_for_status()
            content = resp.content
            
            if url.endswith('.gz'):
                with gzip.GzipFile(fileobj=BytesIO(content)) as gz:
                    content = gz.read()
            
            root = ET.fromstring(content)
            for channel in root.findall('channel'):
                ch_id = channel.get('id')
                display_name = channel.find('display-name')
                if ch_id and display_name is not None and display_name.text:
                    name = display_name.text.strip()
                    VALID_EPGS_DICT[ch_id] = name
                    REVERSE_EPG_DICT[clean_channel_for_lookup(name)] = ch_id
        except Exception as e:
            print(f"  > GAGAL load EPG {url}: {e}")
    print(f"  > Selesai. Total Channel ID di EPG: {len(VALID_EPGS_DICT)}")

def get_suggested_epg_id(channel_name):
    cleaned = clean_channel_for_lookup(channel_name)
    for k, v in REVERSE_EPG_DICT.items():
        if k in cleaned or cleaned in k:
            return v
    return "TIDAK DITEMUKAN"

def contains_time_pattern(text):
    return bool(TIME_PATTERN_REGEX.search(text))

def get_ott_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*"
    }

def get_provider_name(url):
    domain = urlparse(url).netloc
    if domain: return domain
    return "Unknown_Provider"

def extract_date_from_group(group_title):
    return None

def download_playlist(args):
    idx, url = args
    print(f"  > Sedang menyedot dari: {url}")
    channels = []
    provider_name = get_provider_name(url)
    try:
        session = requests.Session()
        response = session.get(url, headers=get_ott_headers(), timeout=(15, 60), verify=False)
        response.raise_for_status()
        
        text_data = response.text.replace('<br>', '\n')
        current_buffer = []  
        current_extinf = ""  
        
        for line in text_data.splitlines():
            line = line.strip()
            if not line: continue
            if line.startswith("#EXTM3U"): continue
            
            if line.startswith("#"):
                current_buffer.append(line)
                if line.startswith("#EXTINF"):
                    current_extinf = line
                    
            elif len(line) > 5 and line.lower().startswith("http"): 
                if current_buffer and current_extinf:
                    tvg_id_match = TVG_ID_REGEX.search(current_extinf)
                    tvg_id = tvg_id_match.group(1).strip() if tvg_id_match else ""

                    channels.append({
                        "buffer": current_buffer,
                        "extinf": current_extinf,
                        "url": line,
                        "tvg_id": tvg_id,
                        "provider_name": provider_name
                    })
                current_buffer = []
                current_extinf = ""
                
        return idx, url, channels
    except Exception as e:
        print(f"  > WARNING: Gagal {url}")
        return idx, url, []

def filter_m3u_by_config(config, super_clean_channels):
    output_file = config["output_file"]
    keywords = config["keywords"]
    target_category = config["category_name"] 
    description = config["description"]

    print(f"\n--- Memproses [{description}] ---")
    if target_category not in CATEGORY_LOGS:
        CATEGORY_LOGS[target_category] = {}
        
    channels_data = [] 
    
    for ch in super_clean_channels:
        stream_url = ch["url"]
        provider_name = ch["provider_name"]
        
        if stream_url in CATEGORIZED_URLS: continue

        current_extinf = ch["extinf"]
        raw_channel_name = current_extinf.split(',', 1)[1].strip() if "," in current_extinf else current_extinf.strip()
        clean_channel_name = CLEANING_REGEX.sub(' ', raw_channel_name).upper()

        # ====================================================================
        # SATPAM KHUSUS: CTV & CHAMPIONS HANYA BOLEH DARI DECCOTECH!
        # ====================================================================
        is_ctv = re.search(r'\bCTV\b', clean_channel_name) or "CHAMPIONS" in clean_channel_name
        if is_ctv:
            if "deccotech" not in provider_name.lower():
                continue # Langsung buang kalau bukan dari Deccotech!
        # ====================================================================
        
        match_found = any(k in clean_channel_name for k in keywords)

        if match_found:
            if provider_name not in CATEGORY_LOGS[target_category]:
                CATEGORY_LOGS[target_category][provider_name] = []
            
            CATEGORY_LOGS[target_category][provider_name].append({
                "name": re.sub(r'\[.*?\]|\(.*?\)', '', raw_channel_name).strip(),
                "tvg_id": ch["tvg_id"]
            })
            CATEGORIZED_URLS.add(stream_url)
            channels_data.append(ch)

    print(f"Total {len(channels_data)} saluran ke [{target_category}].")


# ====================================================================
# III. EKSEKUSI UTAMA
# ====================================================================

if __name__ == "__main__":
    print("=====================================================")
    print("MEMULAI MESIN PENYEDOT IPTV (OMNI-KASTA SUPER TURBO)")
    print("=====================================================")
    
    load_epg_databases()
    
    all_providers_data = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(download_playlist, enumerate(MASTER_URLS))
        for idx, url, channels in results:
            if channels:
                all_providers_data.append({
                    "provider_idx": idx,
                    "url": url,
                    "channels": channels
                })
                
    super_clean_channels = []
    master_seen_urls = set()
    for provider in all_providers_data:
        for ch in provider["channels"]:
            if ch["url"] not in master_seen_urls and ch["url"] not in GLOBAL_BLACKLIST_URLS:
                master_seen_urls.add(ch["url"])
                super_clean_channels.append(ch) 
    
    for config in CONFIGURATIONS:
        filter_m3u_by_config(config, super_clean_channels)
        
    print("\n[+] Mencetak file Laporan EPG Lengkap per Kategori & Penyedia...")
    
    with open("daftar_epg_lengkap.txt", "w", encoding="utf-8") as f:
        f.write("DAFTAR LENGKAP CHANNEL (KATEGORI & PROVIDER) BESERTA STATUS EPG\n")
        f.write("=========================================================\n\n")
        f.write("LEGENDA STATUS EPG:\n")
        f.write("🟢 = Cocok (ID EPG Ditemukan & Valid)\n")
        f.write("🔴 = Tidak Cocok (ID EPG ada, tapi nama EPG & Channel jauh berbeda)\n")
        f.write("🟡 = Kosong (tvg-id di M3U kosong)\n")
        f.write("🟠 = ID Salah/Mati (tvg-id ada di M3U, tapi tidak ada di file XML EPG)\n")
        f.write("=========================================================\n\n")
        
        for category in sorted(CATEGORY_LOGS.keys()):
            f.write(f"\n{C_CYAN}=== KATEGORI: {category} ==={C_RESET}\n")
            
            provider_dict = CATEGORY_LOGS[category]
            for provider in sorted(provider_dict.keys()):
                f.write(f"  {C_YELLOW}Penyedia: [{provider}]{C_RESET}\n")
                
                for ch in sorted(provider_dict[provider], key=lambda x: x["name"]):
                    name = ch["name"]
                    tvg_id = ch["tvg_id"]
                    
                    if not tvg_id:
                        saran_id = get_suggested_epg_id(name)
                        line_out = f"    🟡 {C_YELLOW}{name} (Kosong) -> Harusnya id epgnya: {saran_id}{C_RESET}\n"
                    
                    elif tvg_id not in VALID_EPGS_DICT:
                        saran_id = get_suggested_epg_id(name)
                        line_out = f"    🟠 {C_ORANGE}{name} ({tvg_id}) -> Tidak valid/kosong di XML. Harusnya: {saran_id}{C_RESET}\n"
                    
                    else:
                        epg_name = VALID_EPGS_DICT[tvg_id]
                        clean_ch_name = clean_channel_for_lookup(name)
                        clean_epg_name = clean_channel_for_lookup(epg_name)
                        
                        if clean_epg_name in clean_ch_name or clean_ch_name in clean_epg_name:
                            line_out = f"    🟢 {C_GREEN}{name} ({tvg_id}) -> Cocok!{C_RESET}\n"
                        else:
                            saran_id = get_suggested_epg_id(name)
                            line_out = f"    🔴 {C_RED}{name} ({tvg_id}) -> Meleset (di EPG bernama '{epg_name}'). Harusnya: {saran_id}{C_RESET}\n"
                            
                    f.write(line_out)
            f.write("\n")
                
    print("\n✅ PROSES SELESAI! Laporan sudah dicetak ke 'daftar_epg_lengkap.txt'.")
