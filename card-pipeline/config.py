"""Central configuration for the card-classification pipeline.

One place for paths, scraper settings, and the constants the pipeline tiers
will share in later builds. Keeping this flat and import-light so every module
(`from config import ...`) stays cheap.
"""
from pathlib import Path

# --- Paths (all relative to this file, so the project is portable) ---
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
BRONZE_DIR = DATA_DIR / "bronze"
IMAGES_DIR = DATA_DIR / "images"
LISTINGS_RAW = BRONZE_DIR / "listings_raw.jsonl"   # Bronze landing: incoming listings
DB_PATH = DATA_DIR / "pipeline.db"                 # Silver/Gold/quarantine (later builds)
EVENTS_LOG = DATA_DIR / "pipeline_events.jsonl"    # per-record journey log (later builds)

# --- Scraper (SportsCardsPro / BeautifulSoup) ---
BASE_URL = "https://www.sportscardspro.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
REQUEST_DELAY_S = 1.5      # polite throttle between HTML page requests
IMAGE_DELAY_S = 0.2        # lighter throttle between image downloads
IMAGE_SIZE = "240"         # pricecharting image variant: 60 | 240 | 1600

# Sports-card focus for now (Pokemon/TCG added later). Each is a category slug.
CATEGORIES = ["basketball-cards", "baseball-cards", "football-cards"]
SETS_PER_CATEGORY = 3      # how many recent sets to pull per sport
CARDS_PER_SET = 14         # sampled per set (base cards + a few parallels)

# --- Pipeline constants (used by later builds; here so config stays the one source) ---
CONFIDENCE_THRESHOLD = 0.75
# Relative per-record cost by tier, for the cost-comparison panel.
TIER_COSTS = {
    "regex": 0.0,
    "llm_text": 0.002,
    "cv_retrieval": 0.0005,
    "vision_llm": 0.02,
    "human": 1.50,
}
