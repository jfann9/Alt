"""SportsCardsPro scraper -> Bronze landing layer.

Pulls real sports-card data (player, set, year, card number, parallel, rookie
flag, ungraded + graded values, and a card image) from sportscardspro.com price
guide pages, then synthesizes a realistic marketplace-style listing
(title + description) on top of that ground truth.

Why synthesize the listing text? The pipeline's job is to resolve a *messy*
listing (the kind eBay returns) back to a canonical card. SportsCardsPro gives
us clean structured data instead, so we use it two ways at once:
  1. as ground truth for validating the pipeline, and
  2. as the seed for a noisy title/description that the text/image tiers parse.
When the eBay Browse API access clears, real eBay titles replace the synthesized
ones and the rest of the pipeline is unchanged.

robots.txt (checked) only disallows /stripe-connect, /publish-offer, /buy — none
of which we touch. We still throttle politely.

Run:  python -m scraper.sportscardspro
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Allow `python -m scraper.sportscardspro` and `python scraper/sportscardspro.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as C


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": C.USER_AGENT})
    return s


def get_html(session: requests.Session, url: str) -> BeautifulSoup | None:
    """Fetch a page politely; return parsed soup or None on failure."""
    try:
        r = session.get(url, timeout=25)
        r.raise_for_status()
        time.sleep(C.REQUEST_DELAY_S)
        return BeautifulSoup(r.text, "lxml")
    except requests.RequestException as e:
        print(f"  ! fetch failed {url}: {e}")
        return None


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
_PRICE_RE = re.compile(r"[-+]?\d[\d,]*\.?\d*")
_PARALLEL_RE = re.compile(r"\[([^\]]+)\]")
_NUMBER_RE = re.compile(r"#(\w+)")
_SLUG_RE = re.compile(r"^(.*?-cards)-(\d{4})-(.*)$")


def parse_price(text: str) -> float | None:
    """'$61.50' -> 61.5 ; '-' / '' -> None."""
    m = _PRICE_RE.search(text or "")
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def parse_console_slug(console_url: str) -> tuple[str, int | None, str]:
    """'/console/basketball-cards-2023-panini-prizm' -> ('basketball', 2023, 'Panini Prizm')."""
    slug = console_url.rstrip("/").split("/console/")[-1]
    m = _SLUG_RE.match(slug)
    if m:
        sport = m.group(1).replace("-cards", "").replace("-", " ").strip()
        year = int(m.group(2))
        brand = m.group(3).replace("-", " ").title()
        return sport, year, brand
    # Fallback for sets without a 4-digit year in the slug
    sport = slug.split("-cards")[0].replace("-", " ").strip() or "unknown"
    return sport, None, slug.replace("-", " ").title()


def parse_row(tr, sport: str, year: int | None, brand: str) -> dict | None:
    """Turn one price-table <tr> into a faithful structured record."""
    try:
        product_id = tr.get("data-product")
        title_a = tr.find("td", class_="title").find("a")
        text = title_a.get_text(strip=True)  # e.g. "Victor Wembanyama [Silver] #136"

        parallel_m = _PARALLEL_RE.search(text)
        parallel = parallel_m.group(1) if parallel_m else None

        number_m = _NUMBER_RE.search(text)
        card_number = number_m.group(1) if number_m else None

        # Player = title minus [parallel] and #number
        player = _PARALLEL_RE.sub("", text)
        player = _NUMBER_RE.sub("", player)
        player = re.sub(r"\s+", " ", player).strip()

        is_rookie = tr.find("span", class_="rookie") is not None

        def price_in(cls: str) -> float | None:
            td = tr.find("td", class_=cls)
            return parse_price(td.get_text()) if td else None

        img = tr.find("img", class_="photo")
        img_url = img["src"] if img and img.has_attr("src") else None
        if img_url:  # upgrade thumbnail (…/60.jpg) to a usable size
            img_url = re.sub(r"/\d+\.jpg$", f"/{C.IMAGE_SIZE}.jpg", img_url)

        game_a = tr.find("td", class_="image").find("a")
        game_url = game_a["href"] if game_a and game_a.has_attr("href") else None
        if game_url and game_url.startswith("/"):
            game_url = C.BASE_URL + game_url

        return {
            "product_id": product_id,
            "player": player,
            "sport": sport,
            "year": year,
            "brand": brand,
            "card_number": card_number,
            "parallel": parallel,
            "is_rookie": is_rookie,
            "ungraded_usd": price_in("used_price"),
            "grade9_usd": price_in("cib_price"),
            "psa10_usd": price_in("new_price"),
            "image_url": img_url,
            "source_url": game_url,
        }
    except (AttributeError, KeyError, TypeError):
        return None  # malformed row — skip, don't crash the run


def get_console_urls(session: requests.Session, category: str) -> list[str]:
    """Return set ('console') URLs listed on a sport category page, in site order."""
    soup = get_html(session, f"{C.BASE_URL}/category/{category}")
    if not soup:
        return []
    seen, urls = set(), []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/console/" in href and href not in seen:
            seen.add(href)
            urls.append(href if href.startswith("http") else C.BASE_URL + href)
    return urls


def scrape_console(session: requests.Session, console_url: str) -> list[dict]:
    """Scrape one set's price table into faithful structured records."""
    soup = get_html(session, console_url)
    if not soup:
        return []
    table = soup.find("table", id="games_table")
    if not table or not table.find("tbody"):
        return []
    sport, year, brand = parse_console_slug(console_url)
    out = []
    for tr in table.find("tbody").find_all("tr"):
        rec = parse_row(tr, sport, year, brand)
        if rec and rec["product_id"]:
            out.append(rec)
    return out


# --------------------------------------------------------------------------- #
# Sampling — keep player variety + the parallels we care about
# --------------------------------------------------------------------------- #
_AMBIGUOUS_PARALLELS = ("silver", "refractor", "holo", "prizm", "base")


def sample_cards(records: list[dict], n: int) -> list[dict]:
    """Pick base cards (player variety) plus a few visually-ambiguous parallels."""
    bases = [r for r in records if not r["parallel"]]
    # Prioritize Silver/Refractor-type parallels — the base-vs-parallel demo
    parallels = sorted(
        (r for r in records if r["parallel"]),
        key=lambda r: 0 if r["parallel"].lower() in _AMBIGUOUS_PARALLELS else 1,
    )
    n_base = max(1, int(n * 0.65))
    picked = bases[:n_base] + parallels[: n - n_base]
    return picked[:n]


# --------------------------------------------------------------------------- #
# Listing synthesis — build the noisy "incoming listing" from ground truth
# --------------------------------------------------------------------------- #
def _grade_for(rec: dict, idx: int) -> tuple[str | None, float | None]:
    """Assign this copy a grade + matching market value (cycles raw / PSA 9 / PSA 10)."""
    pick = idx % 3
    if pick == 0:
        return "PSA 10", rec["psa10_usd"]
    if pick == 1:
        return "PSA 9", rec["grade9_usd"]
    return None, rec["ungraded_usd"]  # raw / ungraded — Alt's raw-value case


def synthesize_listing(rec: dict, idx: int) -> dict:
    """Wrap a structured record into a Bronze listing with controlled difficulty.

    Difficulty buckets (deterministic, so the dataset has a known mix):
      clean            -> full structured title; Tier-1 regex should resolve it
      ambiguous_text   -> sparse/slangy title; needs the LLM text tier
      ambiguous_image  -> parallel omitted from text; only the image reveals it
    """
    grade, value = _grade_for(rec, idx)
    player, year, brand = rec["player"], rec["year"], rec["brand"]
    num, parallel = rec["card_number"], rec["parallel"]
    rc = " RC" if rec["is_rookie"] else ""

    bucket = ("clean", "clean", "ambiguous_text", "ambiguous_image")[idx % 4]
    # A base card can't demonstrate the "image-only parallel" case — make it clean.
    if bucket == "ambiguous_image" and not parallel:
        bucket = "clean"

    yr = f"{year} " if year else ""
    num_s = f"#{num} " if num else ""
    grade_s = f" {grade}" if grade else ""

    if bucket == "clean":
        par_s = f"{parallel} " if parallel else ""
        title = f"{yr}{brand} {player} {par_s}{num_s}{rc}{grade_s}".strip()
        desc = (
            f"{player} {yr}{brand}{' ' + parallel if parallel else ''} "
            f"{num_s}{'rookie ' if rec['is_rookie'] else ''}"
            f"{'graded ' + grade if grade else 'raw ungraded'}. Ships in a top loader."
        ).strip()
    elif bucket == "ambiguous_text":
        # Sparse / hobby slang — drop year, number, sometimes grade
        nick = player.split()[-1]
        title = f"{nick} {brand.split()[-1]}{rc} 🔥{grade_s}".strip()
        desc = f"{player} card, {brand}. {'Looks minty.' if not grade else 'Slabbed.'}"
    else:  # ambiguous_image — text reads like the base card; parallel hidden in image
        title = f"{yr}{brand} {player} {num_s}{rc}{grade_s}".strip()
        desc = (
            f"{player} {yr}{brand} {num_s}— see photos for the exact parallel/finish. "
            f"{'Graded ' + grade if grade else 'Raw.'}"
        ).strip()

    return {
        "listing_id": f"scp-{rec['product_id']}",
        "source": "sportscardspro",
        "source_url": rec["source_url"],
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "description": desc,
        "image_url": rec["image_url"],
        "image_path": f"data/images/{rec['product_id']}.jpg",
        # Ground truth (faithful from source) — used to score the pipeline later.
        "ground_truth": {
            "player": player,
            "sport": rec["sport"],
            "year": year,
            "brand": brand,
            "set_name": f"{yr}{brand}".strip(),
            "card_number": num,
            "parallel": parallel,
            "is_rookie": rec["is_rookie"],
            "grade": grade,
            "value_usd": value,
        },
        # Analysis-only metadata — the pipeline must NOT read this.
        "_synthetic": {"difficulty": bucket},
    }


# --------------------------------------------------------------------------- #
# Image download
# --------------------------------------------------------------------------- #
def download_image(session: requests.Session, url: str | None, dest: Path) -> bool:
    if not url:
        return False
    if dest.exists():  # cache: never re-download
        return True
    try:
        r = session.get(url, timeout=25)
        r.raise_for_status()
        dest.write_bytes(r.content)
        time.sleep(C.IMAGE_DELAY_S)
        return True
    except requests.RequestException as e:
        print(f"  ! image failed {url}: {e}")
        return False


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    C.BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    C.IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    session = make_session()
    listings: list[dict] = []
    idx = 0

    for category in C.CATEGORIES:
        print(f"\n== {category} ==")
        console_urls = get_console_urls(session, category)[: C.SETS_PER_CATEGORY]
        if not console_urls:
            print("  (no sets found)")
            continue
        for curl in console_urls:
            records = scrape_console(session, curl)
            picked = sample_cards(records, C.CARDS_PER_SET)
            print(f"  {curl.split('/console/')[-1]}: {len(records)} cards, took {len(picked)}")
            for rec in picked:
                ok = download_image(
                    session, rec["image_url"], C.IMAGES_DIR / f"{rec['product_id']}.jpg"
                )
                listing = synthesize_listing(rec, idx)
                if not ok:
                    listing["image_path"] = None
                listings.append(listing)
                idx += 1

    with C.LISTINGS_RAW.open("w", encoding="utf-8") as f:
        for r in listings:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Quick run summary
    by_diff: dict[str, int] = {}
    with_img = 0
    for r in listings:
        by_diff[r["_synthetic"]["difficulty"]] = by_diff.get(r["_synthetic"]["difficulty"], 0) + 1
        with_img += 1 if r["image_path"] else 0
    print(f"\nWrote {len(listings)} listings -> {C.LISTINGS_RAW}")
    print(f"  images downloaded: {with_img}/{len(listings)}")
    print(f"  difficulty mix:    {by_diff}")


if __name__ == "__main__":
    main()
