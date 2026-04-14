import requests
import re
import concurrent.futures
import random
import urllib3
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Matikan peringatan SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ====================================================================
# I. KONFIGURASI GLOBAL
# ====================================================================

MASTER_URLS = [
    "https://bwifi.my.id/aspal.m3u",
    "https://deccotech.online/tv/tvstream.html", 
    "https://freeiptv2026.tsender57.workers.dev", 
    "https://raw.githubusercontent.com/tvplaylist/T2/refs/heads/main/tv1",
    "", 
    "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25",
    "https://semar25.short.gy",
    "https://bit.ly/TVKITKAT",
    "https://liveevent.iptvbonekoe.workers.dev",
    "",
    "https://bit.ly/KPL203"
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
    "https://bit.ly/428RaFW",
    "https://iili.io/KfT7PJ2.jpg",
    "https://drive.google.com/uc?export=download&id=12slpj4XW5B5SlR9lruuZ77_NPtTHKKw8&usp",
    "https://shorter.me/SNozg",
    "https://mimipipi22.github.io/logo/offline.m3u8",
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
    {
        "output_file": "event_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"], 
        "category_name": "BACKUP EVENT SPORTS", 
        "force_category": True, 
        "require_time": True, 
        "description": "EVENT: Gabungan Event Olahraga (Wajib Berjadwal)"
    },
    {
        "output_file": "sports_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"],
        "category_name": "SPORTS",
        "force_category": True,  
        "require_time": False, 
        "description": "SPORTS: Gabungan Live"
    },
    {
        "output_file": "indonesia_combined.m3u", 
        "keywords": ALL_POSITIVE_KEYWORDS["INDONESIA"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["KNOWLEDGE"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "INDONESIA",
        "force_category": True,
        "require_time": False,
        "description": "INDONESIA: Gabungan TV Indonesia Murni"
    },
    {
        "output_file": "kids_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["KIDS"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "KIDS",
        "force_category": True,
        "require_time": False,
        "description": "KIDS: Gabungan Saluran Anak"
    },
    {
        "output_file": "knowledge_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["KNOWLEDGE"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "KNOWLEDGE",
        "force_category": True,
        "require_time": False,
        "description": "KNOWLEDGE: Gabungan Saluran Edukasi"
    },
    {
        "output_file": "news_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["NEWS"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["RELIGI"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"] + ALL_POSITIVE_KEYWORDS["INDONESIA"],
        "category_name": "NEWS",
        "force_category": True,
        "require_time": False,
        "description": "NEWS: Gabungan Saluran Berita Internasional"
    },
    {
        "output_file": "religi_combined.m3u",
        "keywords": ALL_POSITIVE_KEYWORDS["RELIGI"],
        "exclude_keywords": ALL_POSITIVE_KEYWORDS["SPORTS_LIVE"] + ALL_POSITIVE_KEYWORDS["KIDS"] + ALL_POSITIVE_KEYWORDS["NEWS"] + ALL_POSITIVE_KEYWORDS["EVENT_ONLY"],
        "category_name": "RELIGI",
        "force_category": True,
        "require_time": False,
        "description": "RELIGI: Gabungan Saluran Dakwah & Rohani"
    },
]

# Regex
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)
CLEANING_REGEX = re.compile(r'[^a-zA-Z0-9\s]+')
TIME_PATTERN_REGEX = re.compile(r'\b(?:[01]?[0-9]|2[0-3])[:.][0-5][0-9]\s*WIB\b', re.IGNORECASE)
SPAM_KEYWORDS = ['EXTVLCOPT', 'USER-AGENT', 'GECKO', 'CHROME', 'SAFARI', 'WINK', 'MOZILLA', 'APPLEWEBKIT', 'HTTP']

CATEGORIZED_URLS = set()
CATEGORY_LOGS = {} 

# ====================================================================
# II. FUNGSI UTAMA MESIN SEDOT & FILTERING
# ====================================================================

def contains_time_pattern(text):
    return bool(TIME_PATTERN_REGEX.search(text))

def get_ott_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "VLC/3.0.18 LibVLC/3.0.18",
        "TiviMate/4.7.0 (Android)"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "*/*",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive"
    }

def extract_date_from_group(group_title):
    if not group_title: return None
    months = {
        'januari': '01', 'jan': '01', 'februari': '02', 'feb': '02',
        'maret': '03', 'mar': '03', 'april': '04', 'apr': '04',
        'mei': '05', 'juni': '06', 'jun': '06',
        'juli': '07', 'jul': '07', 'agustus': '08', 'agu': '08', 'agus': '08',
        'september': '09', 'sep': '09', 'oktober': '10', 'okt': '10',
        'november': '11', 'nov': '11', 'desember': '12', 'des': '12'
    }
    pattern = r'(\d{1,2})\s*(' + '|'.join(months.keys()) + r')'
    match = re.search(pattern, group_title, re.IGNORECASE)
    
    if match:
        day = match.group(1).zfill(2)
        month_str = match.group(2).lower()
        month = months[month_str]
        year = datetime.now().strftime("%y") 
        return f"{day}-{month}-{year}"
    return None

def get_channel_priority(channel_name, category):
    """ SISTEM 31 KASTA SUPER VIP UNTUK SPORTS """
    n = channel_name.upper()
    
    if category == "SPORTS":
        if "BEIN" in n: return 1
        if re.search(r'\bCTV\b', n) or "CHAMPIONS" in n: return 2
        if "SPOTV" in n: return 3
        if "SPORTSTAR" in n: return 4
        if "SOCCER CHANNEL" in n: return 5
        
        lokal_gratis = ["RCTI", "SCTV", "INDOSIAR", "ANTV", "MNC TV", "MNCTV", "INEWS", "GTV", "TVRI", "TRANS", "MOJI", "RTV", "VOLI TV", "RCTV"]
        if any(k in n for k in lokal_gratis) and ("SPORT" in n or "LIGA" in n): return 6
        
        if "DAZN" in n: return 7
        if "ZIGGO" in n: return 8
        if "ARENA" in n and not "BEIN" in n: return 9
        if "SKY" in n and "SPORT" in n: return 10
        if "TNT" in n and "SPORT" in n: return 11
        if "TRUE" in n and ("SPORT" in n or "PREMIER" in n): return 12
        if "HUB" in n and ("PREMIER" in n or "SPORT" in n): return 13
        if "ASTRO" in n: return 14
        if "SETANTA" in n: return 15
        if "PRIMA" in n: return 16
        
        if any(k in n for k in ["EUROSPORT", "SPORT KLUB", "NOVA SPORT", "DIGI SPORT", "CT SPORT", "MAXSPORT", "GO3 SPORT"]): return 17
        if "ESPN" in n: return 18
        if any(k in n for k in ["SSC", "ALKASS", "ABU DHABI", "DUBAI", "OMAN SPORT", "BAHRAIN", "SHARJAH"]): return 19
        if any(k in n for k in ["NBA", "NFL", "MLB", "NHL", "CBS", "FOX SPORT", "NBC", "FUBO", "PEACOCK", "DRAFTKINGS", "FANDUEL"]): return 20
        if any(k in n for k in ["WWE", "SMACKDOWN", "RAW", "UFC", "BELLATOR", "GLORY", "IMPACT", "FNC", "FIGHT", "MMA"]): return 21
        if any(k in n for k in ["MUTV", "LFCTV", "CHELSEA", "REAL MADRID", "BARCA", "HAJDUK", "INTER TV"]): return 22
        if "TSN" in n or "SPORTSNET" in n or "GAME+" in n: return 23
        if "SUPERSPORT" in n or "SS PREMIER" in n or "SS F1" in n or "SS FOOTBALL" in n or "SS GOLF" in n or "SS MAIN" in n or "SS RACING" in n: return 24
        if "SONY" in n or "STAR SPORT" in n or "DD SPORT" in n or "FANCODE": return 25
        if "MATCH!" in n or "KHL" in n or "ZVEZDA" in n: return 26
        if "FIFA" in n or "AFC" in n: return 27
        if any(k in n for k in ["TUDN", "TYC", "TELEDEPORTE", "SPORTV", "CAZE", "CDN", "OVACION", "MULTIVISION"]): return 28
        if any(k in n for k in ["GOLF", "MOTORVISION", "GP1", "AUTO MOTOR", "RACER", "NHRA"]): return 29
        if any(k in n for k in ["BWF", "LIVE EVENT", "TIMNAS", "EPL", "M LIVE"]): return 30
        if any(k in n for k in ["PILIPINAS", "UAAP", "SUKAN", "RTB", "ELTA", "J SPORT", "GAORA", "NITTELE"]): return 31
        
        return 999 

    elif category == "INDONESIA":
        if "RCTI" in n: return 1
        if "SCTV" in n: return 2
        if "INDOSIAR" in n: return 3
        if "TRANS" in n: return 4
        if "MNC" in n: return 5
        if "GTV" in n or "GLOBAL" in n: return 6
        if "TVRI" in n: return 7
        if "METRO" in n: return 8
        if "TVONE" in n or "TV ONE" in n: return 9
        if "KOMPAS" in n: return 10
        if "INEWS" in n: return 11
        if "RTV" in n: return 12
        if "NET" in n: return 13
        if "BTV" in n or "BERITA SATU" in n: return 14
        if "JTV" in n or "JAK TV" in n: return 15
        if "DAAI" in n: return 16
        return 99

    elif category == "KIDS":
        if "DISNEY" in n: return 1
        if "NICKELODEON" in n or "NICK" in n: return 2
        if "CARTOON" in n or "CN" in n: return 3
        if "BOOMERANG" in n: return 4
        if "BABY" in n: return 5
        if "MENTARI" in n: return 6
        if "CERIA" in n: return 7
        if "ANIMASI" in n or "ANIMATION" in n: return 8
        return 99

    elif category == "KNOWLEDGE":
        if "NAT" in n and "GEO" in n: return 1
        if "DISCOVERY" in n: return 2
        if "ANIMAL" in n: return 3
        if "HISTORY" in n: return 4
        if "SCIENCE" in n: return 5
        if "WILD" in n: return 6
        if "DOKUMENTER" in n or "DOCUMENTARY" in n: return 7
        return 99

    elif category == "NEWS":
        if "CNN" in n: return 1
        if "CNBC" in n: return 2
        if "BBC" in n: return 3
        if "AL JAZEERA" in n: return 4
        if "CNA" in n: return 5
        if "BLOOMBERG" in n: return 6
        if "CCTV" in n: return 999 
        return 99

    elif category == "RELIGI":
        if "MAKKAH" in n or "MADINAH" in n: return 1
        if "RODJA" in n: return 2
        if "TVMU" in n: return 3
        if "MTA" in n: return 4
        if "WESAL" in n or "INSAN" in n or "SURAU" in n: return 5
        if "KHAZANAH" in n: return 6
        if "UMMAT" in n or "NABAWI" in n: return 7
        return 99
        
    elif category == "LIVE EVENT SPORTS":
        return 0 
        
    return 99

def download_playlist(args):
    idx, url = args
    print(f"  > Sedang menyedot dari: {url}")
    channels = []
    try:
        session = requests.Session()
        retry_strategy = Retry(
            total=2,  
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1  
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        response = session.get(url, headers=get_ott_headers(), timeout=(15, 60), verify=False)
        response.raise_for_status()
        
        text_data = response.text.replace('<br>', '\n').replace('<br/>', '\n').replace('<BR>', '\n')
        
        url_logo_lama1 = "https://raw.githubusercontent.com/tsender57-dotcom/offline/refs/heads/main/logo/Logo%20OGI%20Bone.png"
        url_logo_lama2 = "https://raw.githubusercontent.com/tsender57-dotcom/offline/refs/heads/main/logo/Logo OGI Bone.png"
        url_logo_baru = "https://raw.githubusercontent.com/karepech/bakul/refs/heads/main/bw.png" 
        
        text_data = text_data.replace(url_logo_lama1, url_logo_baru).replace(url_logo_lama2, url_logo_baru)
        
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
                stream_url = line
                if current_buffer and current_extinf:
                    channels.append({
                        "buffer": current_buffer,
                        "extinf": current_extinf,
                        "url": stream_url
                    })
                current_buffer = []
                current_extinf = ""
                
        return idx, url, channels
    except Exception as e:
        print(f"  > WARNING: Gagal memproses {url}. Error: {e}")
        return idx, url, []

def filter_m3u_by_config(config, super_clean_channels):
    output_file = config["output_file"]
    keywords = config["keywords"]
    exclude_keywords = config["exclude_keywords"] 
    target_category = config["category_name"] 
    force_category = config["force_category"]
    require_time = config.get("require_time", False) 
    description = config["description"]

    print(f"\n--- Memproses [{description}] ---")
    
    if target_category not in CATEGORY_LOGS:
        CATEGORY_LOGS[target_category] = {}
        
    channels_data = [] 
    
    for ch in super_clean_channels:
        stream_url = ch["url"]
        provider_idx = ch["provider_idx"] 
        
        if stream_url in CATEGORIZED_URLS:
            continue

        current_extinf = ch["extinf"]
        current_buffer = list(ch["buffer"]) 

        group_match = GROUP_TITLE_REGEX.search(current_extinf)
        raw_group_title = group_match.group(1) if group_match else ""
        
        if "," in current_extinf:
            raw_channel_name = current_extinf.split(',', 1)[1].strip()
        else:
            raw_channel_name = current_extinf.strip()
        
        has_time_pattern = contains_time_pattern(raw_channel_name)
        new_channel_name = raw_channel_name
        extracted_date = None
        
        if target_category == "SPORTS":
            new_channel_name = re.sub(r'(?i)eleven', 'DAZN', new_channel_name)
        
        clean_group_title = CLEANING_REGEX.sub(' ', raw_group_title).upper()
        clean_channel_name = CLEANING_REGEX.sub(' ', new_channel_name).upper()

        if "SPOTV" in clean_channel_name and re.search(r'[\U0001F1E6-\U0001F1FF]', raw_channel_name):
            continue 
        
        if any(spam in clean_channel_name for spam in SPAM_KEYWORDS):
            continue

        if target_category == "SPORTS":
            if "BEIN" in clean_channel_name and "MAX" in clean_channel_name: continue

        if "RADIO" in clean_channel_name or "RADIO" in clean_group_title:
            continue

        if "TVRI" in clean_channel_name:
            tvri_daerah = ["JABAR", "JATIM", "JATENG", "BALI", "PAPUA", "MALUKU", "SULSEL", "SULUT", "SUMUT", "SUMBAR", "RIAU", "JAMBI", "BANTEN", "JAKARTA", "DKI", "KALTIM", "KALBAR", "KALSEL", "KALTENG", "NTB", "NTT", "GORONTALO", "LAMPUNG", "BENGKULU", "BABEL", "KEPRI", "ACEH", "YOGYAKARTA", "JOGJA", "DIY", "SULTENG", "SULTRA", "SULBAR"]
            if any(d in clean_channel_name for d in tvri_daerah):
                continue 

        match_found = False

        if target_category == "LIVE EVENT SPORTS":
            if has_time_pattern:
                match_found = True
                extracted_date = extract_date_from_group(raw_group_title)
                if extracted_date and not re.match(r'^\d{2}-\d{2}-\d{2,4}', raw_channel_name.strip()):
                    new_channel_name = f"{extracted_date} {raw_channel_name.strip()}"
        else:
            for k in keywords:
                if k == "CTV":
                    if re.search(r'\bCTV\b', clean_group_title) or re.search(r'\bCTV\b', clean_channel_name):
                        match_found = True
                        break
                else:
                    if k in clean_group_title or k in clean_channel_name:
                        match_found = True
                        break
                        
            if match_found:
                for ek in exclude_keywords:
                    if ek == "CTV":
                        if re.search(r'\bCTV\b', clean_group_title) or re.search(r'\bCTV\b', clean_channel_name):
                            match_found = False
                            break
                    else:
                        if ek in clean_group_title or ek in clean_channel_name:
                            match_found = False
                            break

            if match_found and require_time and not has_time_pattern:
                match_found = False

        if match_found and target_category == "SPORTS":
            lokal_gratis = ["RCTI", "SCTV", "INDOSIAR", "ANTV", "MNC TV", "MNCTV", "INEWS", "GTV", "TVRI", "TRANS", "MOJI", "RTV", "NET TV", "VOLI TV", "RCTV"]
            if any(k in clean_channel_name for k in lokal_gratis):
                if not any(s in clean_channel_name for s in ["SPORT", "LIGA"]):
                    match_found = False
            
            # ====================================================================
            # PERBAIKAN SATPAM CTV: Cek ke Provider URL, bukan ke Stream URL
            # ====================================================================
            if "CHAMPIONS" in clean_channel_name or re.search(r'\bCTV\b', clean_channel_name):
                if "deccotech" not in MASTER_URLS[provider_idx].lower():
                    match_found = False

        if match_found:
            priority_score = get_channel_priority(new_channel_name, target_category)
            
            if target_category == "SPORTS" and priority_score == 999:
                continue 

            if force_category:
                for idx in range(len(current_buffer)):
                    b_line = current_buffer[idx]
                    
                    if b_line.startswith("#EXTINF"):
                        if 'group-title="' in b_line:
                            b_line = re.sub(r'group-title="[^"]*"', f'group-title="{target_category}"', b_line, flags=re.IGNORECASE)
                        else:
                            if ',' in b_line:
                                parts = b_line.split(',', 1)
                                b_line = f'{parts[0]} group-title="{target_category}",{parts[1]}'
                            else:
                                b_line = f'{b_line} group-title="{target_category}"'
                        
                        if new_channel_name != raw_channel_name:
                            parts = b_line.split(',', 1)
                            if len(parts) == 2:
                                b_line = f"{parts[0]},{new_channel_name}"
                                
                        current_buffer[idx] = b_line
                        
                    elif b_line.upper().startswith("#EXTGRP:"):
                        current_buffer[idx] = f"#EXTGRP:{target_category}"
            
            sort_key = new_channel_name.upper()
            if target_category == "LIVE EVENT SPORTS" and extracted_date:
                date_parts = extracted_date.split('-')
                if len(date_parts) == 3:
                    sort_key = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]} {new_channel_name.upper()}"
            
            clean_name_for_log = re.sub(r'\[.*?\]|\(.*?\)', '', new_channel_name).strip()
            
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', current_extinf, re.IGNORECASE)
            epg_name = tvg_id_match.group(1).strip() if tvg_id_match else ""
            if not epg_name:
                tvg_name_match = re.search(r'tvg-name="([^"]*)"', current_extinf, re.IGNORECASE)
                epg_name = tvg_name_match.group(1).strip() if tvg_name_match else "KOSONG"
                
            log_entry = f"{clean_name_for_log}  [EPG: {epg_name}]"
            
            if priority_score not in CATEGORY_LOGS[target_category]:
                CATEGORY_LOGS[target_category][priority_score] = set()
            CATEGORY_LOGS[target_category][priority_score].add(log_entry)
            
            channels_data.append((priority_score, provider_idx, sort_key, current_buffer, stream_url))
            CATEGORIZED_URLS.add(stream_url)
                    
    if target_category == "LIVE EVENT SPORTS":
        channels_data.sort(key=lambda x: (x[2], x[1])) 
    else:
        channels_data.sort(key=lambda x: (x[0], x[1], x[2])) 
    
    filtered_lines = ["#EXTM3U"]
    for _, _, _, block_data, s_url in channels_data:
        filtered_lines.extend(block_data)  
        filtered_lines.append(s_url)       

    print(f"Total {len(channels_data)} saluran berhasil dikelompokkan ke grup [{target_category}].")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(filtered_lines) + '\n')
    print(f"Playlist [{output_file}] berhasil disimpan.")

# ====================================================================
# III. EKSEKUSI UTAMA
# ====================================================================

if __name__ == "__main__":
    print("=====================================================")
    print("MEMULAI MESIN PENYEDOT IPTV (OMNI-KASTA SUPER TURBO)")
    print("=====================================================")
    
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
                
    print("\n[+] Membuat Daftar Saluran Super Bersih (Prioritas Penyedia Nomor 1)...")
    
    super_clean_channels = []
    master_seen_urls = set()
    
    for provider in all_providers_data:
        p_idx = provider["provider_idx"]
        for ch in provider["channels"]:
            stream_url = ch["url"]
            
            if stream_url in GLOBAL_BLACKLIST_URLS:
                continue
            
            if stream_url not in master_seen_urls:
                master_seen_urls.add(stream_url)
                super_clean_channels.append({
                    "buffer": ch["buffer"],
                    "extinf": ch["extinf"],
                    "url": stream_url,
                    "provider_idx": p_idx
                }) 
    
    print(f"Total saluran unik (Link Beda) yang didapat: {len(super_clean_channels)}")
    print("\n[+] Memulai proses filtering Omni-Kasta...")
    
    for config in CONFIGURATIONS:
        filter_m3u_by_config(config, super_clean_channels)
        
    print("\n[+] Mencetak file Laporan EPG Lengkap...")
    
    kasta_names_sports = {
        1: "[KASTA 1 - BEIN]", 2: "[KASTA 2 - CTV]", 3: "[KASTA 3 - SPOTV]",
        4: "[KASTA 4 - SPORTSTARS]", 5: "[KASTA 5 - SOCCER CHANNEL]",
        6: "[KASTA 6 - LOKAL SPORTS]", 7: "[KASTA 7 - DAZN / ELEVEN]",
        8: "[KASTA 8 - ZIGGO SPORT]", 9: "[KASTA 9 - ARENA SPORT]",
        10: "[KASTA 10 - SKY SPORTS]", 11: "[KASTA 11 - TNT SPORTS]",
        12: "[KASTA 12 - TRUE SPORTS]", 13: "[KASTA 13 - HUB PREMIER / SPORTS]",
        14: "[KASTA 14 - ASTRO]", 15: "[KASTA 15 - SETANTA]",
        16: "[KASTA 16 - PRIMA]", 17: "[KASTA 17 - EUROSPORT & SPORT KLUB]",
        18: "[KASTA 18 - ESPN NETWORK]", 19: "[KASTA 19 - SULTAN TIMUR TENGAH]",
        20: "[KASTA 20 - US MAJOR LEAGUES & NETWORKS]", 21: "[KASTA 21 - COMBAT & WRESTLING]",
        22: "[KASTA 22 - FOOTBALL CLUB TV]", 23: "[KASTA 23 - TSN CANADA & SPORTSNET]",
        24: "[KASTA 24 - SUPERSPORT AFRICA]", 25: "[KASTA 25 - SONY & STAR SPORTS]",
        26: "[KASTA 26 - MATCH! RUSSIA]", 27: "[KASTA 27 - OLYMPIC, FIFA & FEDERATION]",
        28: "[KASTA 28 - LATIN & SPANISH]", 29: "[KASTA 29 - GOLF & RACING]",
        30: "[KASTA 30 - FEEDS & LIVE EVENTS]", 31: "[KASTA 31 - PHILIPPINES & EAST ASIA]"
    }

    with open("daftar_epg_lengkap.txt", "w", encoding="utf-8") as f:
        f.write("DAFTAR LENGKAP CHANNEL SEMUA KATEGORI BESERTA ID EPG\n")
        f.write("=========================================================\n\n")
        
        for category in sorted(CATEGORY_LOGS.keys()):
            f.write(f"=== KATEGORI: {category} ===\n")
            kasta_dict = CATEGORY_LOGS[category]
            
            for kasta in sorted(kasta_dict.keys()):
                if kasta == 0:
                    kasta_name = "[JADWAL EVENT]"
                elif category == "SPORTS" and kasta <= 31:
                    kasta_name = kasta_names_sports.get(kasta, f"[KASTA {kasta} - SPORTS]")
                elif kasta == 99:
                    kasta_name = "[KASTA 99 - UMUM / LAIN-LAIN]"
                elif kasta == 999:
                    kasta_name = "[KASTA 999 - BAWAH / JURU KUNCI]" 
                else:
                    kasta_name = f"[KASTA {kasta} - PRIORITAS UTAMA]"
                    
                f.write(f"  {kasta_name}\n")
                for name_with_epg in sorted(kasta_dict[kasta]):
                    f.write(f"    - {name_with_epg}\n")
            f.write("\n")
                
    print("\n✅ PROSES SELESAI! Daftar Channel dan EPG sukses dicetak ke TXT!")
