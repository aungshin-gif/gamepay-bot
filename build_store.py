"""
Regenerates the game data embedded in store.html from g2bulk's public
catalogue API (https://api.g2bulk.com/v1) — no API key needed, since
games/categories/products/catalogue are all public read endpoints.

What it does:
  1. Fetches /v1/games (every direct top-up game g2bulk offers).
  2. Groups regional/variant duplicates under one game (e.g. all 12
     "Free Fire" country listings become one "Free Fire" entry), but
     — unlike the first version of this script — keeps every working
     variant as a selectable category under that game, instead of
     throwing the others away. A game with only one source listing just
     gets a single "Standard" variant.
  3. For every variant, fetches /v1/games/{code}/catalogue (prices),
     /v1/games/fields (which inputs checkout needs) and, when a server
     id is required, /v1/games/servers (the real server list).
  4. Converts USD prices to MMK at EXCHANGE_RATE.
  5. Pins Mobile Legends to the front of the list and flags it "hot".
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
PINNED_FIRST = "mobile legends"  # base name (lowercase) to always show first
HOT_GAMES = {"mobile legends"}   # base names (lowercase) that get a Hot badge

# Games whose display name is a raw internal code, not a real title, or
# that are a confirmed dead-duplicate of a properly-named entry.
MANUAL_EXCLUDE_CODES = {
    "lds_login",          # same game as "lds" / Love and Deepspace, code shown as its name
    "magic_chest_gogo",   # typo'd duplicate of magic_chess_gogo
}

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
    e.g. 'Freefire Indonesia' and 'Freefire Global' both -> 'Freefire'."""
    n = name
    prev = None
    while prev != n:
        prev = n
        n = _paren_pattern.sub("", n)
        n = _word_pattern.sub("", n)
        n = n.strip(" :-()").strip()
    return re.sub(r"\s+", " ", n).strip()


def rank(member, base_l):
    """Lower tuple sorts first — decides which variant is shown/selected
    by default. Prefer, in order: the plain/unsuffixed name, a 'Global'
    listing, a SEA/Asia/Instant listing, a Singapore listing, else the
    oldest (lowest id) entry."""
    name_l = member["name"].lower()
    exact = name_l == base_l
    is_global = "global" in name_l
    is_neutral = any(w in name_l for w in ("sea", "asia", "instant"))
    is_sg = "singapore" in name_l or member["code"].lower().endswith("_sg")
    return (not exact, not is_global, not is_neutral, not is_sg, member["id"])


def variant_label(name, base_display):
    """Human label for a variant within its game, e.g. 'Mobile Legends
    Brazil' with base 'Mobile Legends' -> 'Brazil'."""
    idx = name.lower().find(base_display.lower())
    if idx == -1:
        return name
    remainder = (name[:idx] + name[idx + len(base_display):]).strip(" :-()").strip()
    return remainder if remainder else "Standard"


def slugify(name):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


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
    try:
        r = session.post(f"{API}/games/fields", json={"game": code}, timeout=15)
        data = r.json()
        info = data.get("info") or {}
        return info.get("fields") or ["userid"], info.get("notes") or ""
    except requests.RequestException:
        return ["userid"], ""


def fetch_servers(session, code):
    try:
        r = session.post(f"{API}/games/servers", json={"game": code}, timeout=15)
        if r.status_code != 200:
            return None
        servers = r.json().get("servers")
        return servers if servers else None
    except requests.RequestException:
        return None


def build_variant(session, member, label):
    data = fetch_catalogue(session, member["code"])
    time.sleep(0.05)
    if not data:
        return None
    denoms = []
    for c in data["catalogues"]:
        usd = c.get("amount")
        if not isinstance(usd, (int, float)):
            continue
        denoms.append({"n": c.get("name", ""), "u": usd, "m": round(usd * EXCHANGE_RATE)})
    denoms.sort(key=lambda d: -d["u"])  # biggest first

    fields, notes = fetch_fields(session, member["code"])
    time.sleep(0.05)
    servers = fetch_servers(session, member["code"]) if "serverid" in fields else None
    if "serverid" in fields:
        time.sleep(0.05)

    return {
        "label": label,
        "code": member["code"],
        "denoms": denoms,
        "startMmk": denoms[-1]["m"] if denoms else None,
        "fields": fields,
        "notes": notes,
        "servers": servers,
    }


def main():
    session = requests.Session()

    print("Fetching game list...", file=sys.stderr)
    games = session.get(f"{API}/games", timeout=20).json()["games"]

    groups = collections.defaultdict(list)
    base_display_by_key = {}
    for g in games:
        if g["code"].lower() == "test" or g["code"] in MANUAL_EXCLUDE_CODES:
            continue
        base_display = base_name(g["name"])
        key = base_display.lower()
        base_display_by_key[key] = base_display
        groups[key].append(g)

    print(f"{len(games)} raw games -> {len(groups)} unique games. Fetching prices/fields...", file=sys.stderr)

    result = []
    skipped = []
    label_collisions_fixed = 0

    for i, (key, members) in enumerate(sorted(groups.items())):
        base_display = base_display_by_key[key]
        ordered = sorted(members, key=lambda m: rank(m, key))

        labels = [variant_label(m["name"], base_display) for m in ordered]
        # Disambiguate any label collision within this game (e.g. two
        # "Standard"-labelled console/pc listings of the same title) using
        # the tail of their code instead.
        seen = collections.Counter(labels)
        for idx, lbl in enumerate(labels):
            if seen[lbl] > 1:
                tail = ordered[idx]["code"].rsplit("_", 1)[-1]
                labels[idx] = tail.upper() if len(tail) <= 3 else tail.capitalize()
                label_collisions_fixed += 1

        variants = []
        for member, label in zip(ordered, labels):
            v = build_variant(session, member, label)
            if v:
                variants.append(v)

        if not variants:
            skipped.append(base_display)
            continue

        result.append({
            "name": base_display,
            "slug": slugify(base_display),
            "img": next((m.get("image_url") for m in ordered if m.get("image_url")), None),
            "variants": variants,
            "startMmk": min(v["startMmk"] for v in variants if v["startMmk"] is not None),
            "hot": key in HOT_GAMES,
        })
        if (i + 1) % 20 == 0:
            print(f"  ...{i + 1}/{len(groups)}", file=sys.stderr)

    result.sort(key=lambda g: g["name"].lower())
    pinned = [g for g in result if g["name"].lower() == PINNED_FIRST]
    rest = [g for g in result if g["name"].lower() != PINNED_FIRST]
    result = pinned + rest

    total_variants = sum(len(g["variants"]) for g in result)
    print(
        f"Done. {len(result)} games ({total_variants} variants total, "
        f"{label_collisions_fixed} label collisions resolved). "
        f"Skipped (no working variant): {skipped}",
        file=sys.stderr,
    )

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
