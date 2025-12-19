import requests
import re

# =========================================================
# KEYWORD EVENT (GABUNG SEMUA)
# =========================================================

EVENT_KEYWORDS = [
    # Event umum
    "EVENT", "SEA GAMES", "ASIAN GAMES",

    # Liga bola
    "PREMIER LEAGUE", "EPL",
    "LA LIGA",
    "SERIE A",
    "BUNDESLIGA",
    "LIGUE 1",
    "EREDIVISIE",
    "LIGA 1",
    "BRI LEAGUE",
    "SAUDI", "SPL",
    "CHAMPIONS LEAGUE", "UCL",
    "EUROPA LEAGUE",

    # Tim besar
    "ARSENAL", "CHELSEA", "LIVERPOOL",
    "MANCHESTER UNITED", "MAN UTD",
    "MANCHESTER CITY", "MAN CITY",
    "REAL MADRID", "BARCELONA",
    "PSG", "BAYERN",

    # Non-bola
    "WWE", "WRESTLING",
    "UFC",
    "BOXING",
    "FORMULA 1", "F1",
    "MOTOGP",
    "OLYMPIC",
    "ESPORT",

    # Channel sport (event carrier)
    "BEIN",
    "DAZN",
    "SSC",
    "SPOTV",
    "SPORTSTAR",
    "SKY SPORTS",
    "TNT SPORTS",
    "FOX SPORTS",
    "ESPN"
]

# =========================================================
# SUMBER PLAYLIST
# =========================================================

SOURCE_URLS = [
    "https://bit.ly/kopinyaoke",
    "https://raw.githubusercontent.com/mimipipi22/lalajo/refs/heads/main/playlist25",
    "https://bakulwifi.my.id/live.m3u",
    "https://donztelevisionpremium.icu/donztelevision/donztelevision.php",
]

OUTPUT_FILE = "event_combined.m3u"

# =========================================================
# REGEX
# =========================================================

GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]*)"', re.IGNORECASE)
CHANNEL_NAME_REGEX = re.compile(r',([^,]*)$')
CLEANING_REGEX = re.compile(r'[^a-zA-Z0-9\s]+')

# =========================================================
# MERGE + KEYWORD MATCH (NO DEDUP)
# =========================================================

def merge_event_m3u():
    result = ["#EXTM3U"]
    total = 0

    for url in SOURCE_URLS:
        print(f"Ambil: {url}")
        try:
            content = requests.get(url, timeout=60).text.splitlines()
        except Exception as e:
            print(f"  Gagal: {e}")
            continue

        i = 0
        while i < len(content):
            line = content[i].strip()

            if line.startswith("#EXTINF") and i + 1 < len(content):
                stream_url = content[i + 1].strip()

                group = GROUP_TITLE_REGEX.search(line)
                name = CHANNEL_NAME_REGEX.search(line)

                raw_group = group.group(1) if group else ""
                raw_name = name.group(1) if name else ""

                clean_group = CLEANING_REGEX.sub(" ", raw_group).upper()
                clean_name = CLEANING_REGEX.sub(" ", raw_name).upper()

                is_match = any(
                    k in clean_group or k in clean_name
                    for k in EVENT_KEYWORDS
                )

                if is_match:
                    result.append(line)
                    result.append(stream_url)
                    total += 1

                i += 2
            else:
                i += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(result) + "\n")

    print("\n✔ SELESAI")
    print(f"✔ Total entry: {total}")
    print(f"✔ Output: {OUTPUT_FILE}")

# =========================================================
# EKSEKUSI
# =========================================================

if __name__ == "__main__":
    merge_event_m3u()
