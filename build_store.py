"""
Regenerates the game data embedded in store.html from g2bulk's public
catalogue API (https://api.g2bulk.com/v1) — no API key needed, since
games/categories/products/catalogue are all public read endpoints.

What it does:
  1. Fetches /v1/games (every direct top-up game g2bulk offers).
  2. Collapses regional duplicates (e.g. 12 "Free Fire" variants, one per
     country) down to a single representative per game, preferring a
     plain/Global/SEA/Singapore listing over a single-country one.
  3. Fetches /v1/games/{code}/catalogue for each surviving game and picks
     the next-ranked variant if the top pick has gone dead/empty.
  4. Converts each USD price to MMK at EXCHANGE_RATE.
  5. Fetches /v1/games/fields (which inputs the checkout form needs —
     player id, server, character name) and /v1/games/servers (the actual
     server list, when one is needed) for each game.
  6. Writes the result back into store.html, between the
     GENERATED:GAMES_JSON markers.

Run it whenever you want to refresh prices/stock, or after changing
EXCHANGE_RATE:

    python3 build_store.py

Gift-card / voucher products (Amazon, PSN, Steam, Xbox, Google Play, etc.,
from /v1/category and /v1/products) are intentionally NOT included here —
this store is games only.
"""
import json
import re
import collections
import time
import sys

import requests

API = "https://api.g2bulk.com/v1"
STORE_HTML = "store.html"
EXCHANGE_RATE = 4325  # 1 USD in MMK — update as the rate moves

# Games whose display name is a raw internal code, not a real title, and
# duplicate a properly-named entry elsewhere in the catalogue.
MANUAL_EXCLUDE_CODES = {"lds_login"}  # same game as "lds" / Love and Deepspace

REGION_WORDS = [
    "Middle East", "South Africa", "South Korea", "Saudi Arabia", "New Zealand", "Hong Kong",
    "Czech Republic", "North America", "United States", "Login Mode",
    "Bangladesh", "Brazil", "Cambodia", "Colombia", "Europe", "Global", "Indonesia", "LATAM",
    "Malaysia", "Mexico", "Philippines", "Singapore", "Taiwan", "Thailand", "Vietnam", "Russia",
    "Turkey", "Ukraine", "Poland", "France", "Germany", "Spain", "Italy", "Austria", "Belgium",
    "Finland", "Greece", "Hungary", "Kuwait", "Lebanon", "Oman", "Qatar", "Romania", "Slovakia",
    "Bahrain", "Netherlands", "Canada", "Australia", "Japan", "India", "Switzerland", "Argentina",
    "Ireland", "Login", "Instant", "Worldwide", "Asia", "Americas", "NAEU",
    "MENA", "CIS", "SEA", "SGMY", "SG", "MY", "KH", "PH", "VN", "TH", "ID", "BR", "EU", "NA",
    "UAE", "US", "USA", "UK", "KSA",
]
REGION_WORDS.sort(key=len, reverse=True)
_alt = "|".join(re.escape(w) for w in REGION_WORDS)
_paren_pattern = re.compile(r"\(\s*(?:" + _alt + r")\s*\)", re.IGNORECASE)
_word_pattern = re.compile(r"(?:^|[\s:\-(])(" + _alt + r")(?:$|(?=[\s():]))", re.IGNORECASE)


def base_name(name):
    """Strip region/variant qualifiers to find the underlying game name,
    e.g. 'Freefire Indonesia' and 'Freefire Global' both -> 'freefire'."""
    n = name
    prev = None
    while prev != n:
        prev = n
        n = _paren_pattern.sub("", n)
        n = _word_pattern.sub("", n)
        n = n.strip(" :-()").strip()
    return re.sub(r"\s+", " ", n).strip()


def rank(member, base):
    """Lower tuple sorts first. Prefer, in order: the plain/unsuffixed
    name, a 'Global' listing, a SEA/Asia/Instant listing, a Singapore
    listing, else the oldest (lowest id) entry."""
    name_l = member["name"].lower()
    exact = member["name"].strip().lower() == base
    is_global = "global" in name_l
    is_neutral = any(w in name_l for w in ("sea", "asia", "instant"))
    is_sg = "singapore" in name_l or member["code"].lower().endswith("_sg")
    return (not exact, not is_global, not is_neutral, not is_sg, member["id"])


def fetch_catalogue(session, code):
    try:
        r = session.get(f"{API}/games/{code}/catalogue", timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data.get("catalogues"):
            return None
        return data
    except requests.RequestException:
        return None


def fetch_fields(session, code):
    """What input fields this game needs (userid, serverid, charname) plus
    any eligibility notes. Falls back to a plain userid if the call fails."""
    try:
        r = session.post(f"{API}/games/fields", json={"game": code}, timeout=15)
        data = r.json()
        info = data.get("info") or {}
        fields = info.get("fields") or ["userid"]
        notes = info.get("notes") or ""
        return fields, notes
    except requests.RequestException:
        return ["userid"], ""


def fetch_servers(session, code):
    """Server list for games that need one, or None when the game has no
    servers (g2bulk returns 403 for that case — not a real error)."""
    try:
        r = session.post(f"{API}/games/servers", json={"game": code}, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        servers = data.get("servers")
        return servers if servers else None
    except requests.RequestException:
        return None


def main():
    session = requests.Session()

    print("Fetching game list...", file=sys.stderr)
    games = session.get(f"{API}/games", timeout=20).json()["games"]

    groups = collections.defaultdict(list)
    for g in games:
        if g["code"].lower() == "test" or g["code"] in MANUAL_EXCLUDE_CODES:
            continue
        groups[base_name(g["name"]).lower()].append(g)

    print(f"{len(games)} raw games -> {len(groups)} unique after dedup. Fetching prices...", file=sys.stderr)

    result = []
    skipped = []
    for i, (base, members) in enumerate(sorted(groups.items())):
        ordered = sorted(members, key=lambda m: rank(m, base))
        chosen = None
        for cand in ordered:
            data = fetch_catalogue(session, cand["code"])
            time.sleep(0.07)
            if data:
                chosen = (cand, data)
                break
        if not chosen:
            skipped.append(base)
            continue
        member, data = chosen
        denoms = []
        for c in data["catalogues"]:
            usd = c.get("amount")
            if not isinstance(usd, (int, float)):
                continue
            denoms.append({"n": c.get("name", ""), "u": usd, "m": round(usd * EXCHANGE_RATE)})
        denoms.sort(key=lambda d: d["u"])

        fields, notes = fetch_fields(session, member["code"])
        time.sleep(0.07)
        servers = fetch_servers(session, member["code"]) if "serverid" in fields else None
        time.sleep(0.07)

        result.append({
            "name": member["name"],
            "code": member["code"],
            "img": member.get("image_url"),
            "denoms": denoms,
            "startMmk": denoms[0]["m"] if denoms else None,
            "fields": fields,
            "notes": notes,
            "servers": servers,
        })
        if (i + 1) % 25 == 0:
            print(f"  ...{i + 1}/{len(groups)}", file=sys.stderr)

    result.sort(key=lambda g: g["name"].lower())
    print(f"Done. {len(result)} games with live pricing. Skipped (no working variant): {skipped}", file=sys.stderr)

    payload = json.dumps(result, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    with open(STORE_HTML, encoding="utf-8") as f:
        html = f.read()

    start_marker = "/*GENERATED:GAMES_JSON_START*/"
    end_marker = "/*GENERATED:GAMES_JSON_END*/"
    start = html.index(start_marker) + len(start_marker)
    end = html.index(end_marker, start)
    html = html[:start] + payload + html[end:]

    with open(STORE_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {len(payload)} bytes of game data into {STORE_HTML}", file=sys.stderr)


if __name__ == "__main__":
    main()
