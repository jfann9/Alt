# Card Pipeline — Study Notes (interview prep)

Plain-language deep dive on how the pipeline runs, so it can be defended end to end.
Companion to `plan.md` (the architecture) and `README` (to come). Covers: routing,
the medallion store, the extraction vocabularies, exactly which pages we scrape, a
real end-to-end trace of one card, and how this would run incrementally on a schedule.

---

## A. Routing — deep dive

**File:** `pipeline/routing.py`. One function, `route(extraction)`, returns a small
decision dict. It is the brain of the cost-aware design.

### Two independent gates, checked cheapest-first
```
conf  = extraction["confidence"]        # 0.0 – 1.0 textual completeness
pstat = extraction["parallel_status"]   # "named" | "uncertain" | "base"

Gate 1:  conf < 0.75            -> escalate to "llm_text"     (text too sparse)
Gate 2:  pstat == "uncertain"  -> escalate to "cv_retrieval" (parallel is visual)
else:                          -> resolved (text alone is enough)
```
The decision dict looks like:
`{"decision": "resolved"|"escalate", "next_tier": None|"llm_text"|"cv_retrieval",
"status": "resolved_text"|"pending_llm_text"|"pending_cv_retrieval", "reason": "..."}`

### Why this exact order and design
- **Gate 1 before Gate 2** because the LLM text tier is *cheaper* than the image
  tiers. If we don't even have enough text, fix that first.
- **Gate 2 is the crown jewel: textual confidence ≠ visual confidence.** A card can
  score 1.0 on text (player, set, year, number, grade all found) yet still need a
  photo to tell a **base** card from a **Silver parallel**. So the parallel is kept
  *out* of the confidence number and tracked separately as `parallel_status`. When
  the listing text hints at an unstated parallel ("see photos for the exact
  parallel/finish"), we route to the image tier **even at confidence 1.0**.
- The **threshold (0.75)** is the real decision boundary, and it is a tunable dial:
  raise it → fewer cards trusted, more sent to paid tiers, higher precision in Gold;
  lower it → cheaper, slightly riskier. We tune it against measured accuracy.

### How it maps to the data (from the live run)
| difficulty | confidence | parallel_status | route |
|---|---|---|---|
| clean | high (≥0.75) | base / named | **resolved** |
| ambiguous_text | low (<0.75) | — | **llm_text** |
| ambiguous_image | high (≥0.75) | **uncertain** | **cv_retrieval** |

> In the full pipeline, `route()` is called again *after* each tier runs. Tier 2
> (LLM) might raise confidence enough to resolve, or still leave the parallel
> uncertain → then Tier 3 (image). Right now it's a single Tier-1 pass.

---

## B. Medallion store (SQLite) — deep dive

**File:** `pipeline/medallion.py`. This owns the queryable layers the dashboard
will sit on. Three tables: `silver`, `gold`, `quarantine` (only `silver` is
populated so far).

### Why three layers
- **Bronze** = `data/bronze/listings_raw.jsonl` — the raw scrape, **immutable**. If
  anything downstream is wrong, we can always replay from Bronze.
- **Silver** = every record after extraction + routing — the **in-flight working
  layer** (cleaned, validated, enriched with confidence + provenance).
- **Gold** = trusted, resolved canonical cards ready to consume (later builds).
- **Quarantine** = low-confidence records for human review, priority-sorted (later).

### The SQLite mechanics (simple)
- `connect()` opens the DB file and sets `row_factory = sqlite3.Row` so we can read
  columns by name (`row["confidence"]`) instead of by position.
- `init_db(conn, reset=True)` runs `CREATE TABLE IF NOT EXISTS` for all three tables
  (and drops them first on a full rebuild).
- `upsert_silver(...)` is the important one. It uses **`INSERT OR REPLACE`** keyed on
  `listing_id` (the primary key). That single choice gives us **idempotency**:
  processing the same card twice **overwrites** its row instead of creating a
  duplicate. (This is the foundation of safe re-runs — see §F.)

### What a Silver row stores (and why)
`listing_id` (PK), `source`, `scraped_at`, `processed_at` (two timestamps = lineage:
when we scraped vs when we processed), the raw `title`/`description`/`image_path`,
then the Tier-1 result: `tier_reached`, `confidence`, `parallel_status`, `decision`,
`next_tier`, `status`, plus `extracted_json` and `ground_truth_json` (stored as JSON
text so the dashboard can query everything without re-running the pipeline), and
`synthetic_difficulty` (our analysis label).

### What this maps to in a real AWS shop
SQLite is the laptop-sized stand-in. In production at Alt:
- **Bronze** → raw files in **S3** (Parquet/JSON), often a table format like
  **Apache Iceberg** or **Delta Lake** for time-travel + safe upserts.
- **Silver/Gold** → warehouse tables in **Redshift**, **Athena/Glue** over S3, or
  **Aurora** — same three-layer idea, bigger engine.
- `INSERT OR REPLACE` → a **MERGE** (upsert) in the warehouse, or a DynamoDB
  conditional write.

---

## C. The extraction vocabularies (Q1)

**File:** `pipeline/text_extract.py` — `KNOWN_SETS`, `KNOWN_PARALLELS`,
`UNCERTAINTY_CUES`, `_STOP_WORDS`.

### Where they came from
Hand-curated from (a) the hobby research we did (base-vs-Silver-Prizm, refractor vs
prizm terminology, reprints) and (b) **what we actually saw in the scraped data** —
the set slugs (`panini-prizm`, `topps-chrome`) and the bracketed parallels on the
console pages (`[Silver]`, `[Refractor]`, `[Ice]`, …). They are intentionally a
**seed list**, not exhaustive — which is why exotic parallels ("Foilfractor",
"Blackout") slip through today. That gap is honest and motivates the later tiers.

### How this would be stored in production (AWS)
The #1 principle: **reference data does not belong hardcoded in application code.**
It's "master/dimension data" that changes independently of the code and must be
updatable without a deploy. On AWS, the common shapes:

| Option | When to use |
|---|---|
| **S3 + JSON/CSV** loaded at startup, cached in memory | Simplest. Version-controlled reference files; pipeline reads on cold start, refreshes on a schedule. |
| **DynamoDB** table (key = token) | Fast point lookups, serverless, good for "is this a known parallel?" |
| **Aurora/RDS** dimension tables | When you need joins and rich relational queries (card ↔ set ↔ player). |
| **OpenSearch (Elasticsearch)** | **Fuzzy / typo-tolerant** name matching ("Wembenyama" → Wembanyama). |
| **ElastiCache/Redis** | Hot in-memory cache if latency-critical at high volume. |

Typical pattern: store the canonical lists as a **dimension** in DynamoDB or S3,
load+cache them in the Lambda/container at init, and refresh on a schedule or when
the master data changes (an event). Code references the cache, never literals.

### How we expand the vocabulary over time
1. **Feedback loop (active learning):** every human correction in the quarantine
   queue yields new tokens (a parallel/set/player we didn't know) → append to the
   reference store. The review queue *is* the labeling pipeline.
2. **Ingest manufacturer checklists:** Topps/Panini/Upper Deck publish a checklist
   for every release (every set + parallel). Periodically load these into the master.
3. **Mine unmatched tokens:** log tokens that appear in listings but match nothing;
   surface the frequent ones for review and promote them.

### Is a "database of every card ever made" feasible?
**Mostly yes, asymptotically.** There's no single official free "every card" DB, but
a strong, continuously-updated **card master** is very achievable by aggregating:
- **Manufacturer set checklists** (Topps, Panini, Upper Deck) — authoritative per
  release, covers the modern era well.
- **Community/commercial DBs:** TCDB (Trading Card Database), Beckett, Cardboard
  Connection, Card Ladder, plus **PSA/SGC population reports** (graded cards) and
  COMC inventory.
- Your own **sold/graded data** accumulating over time.

The catch: counting every parallel and every serial-numbered 1/1 as a distinct
"card" makes the set effectively unbounded and growing weekly — so you don't aim for
"literally every card." You build a **card-master dimension** (a slowly-changing
dimension) that covers the commercially-relevant universe and grows continuously.
This master is the canonical entity the pipeline resolves *to* — exactly the open-set
retrieval framing in `plan.md` §1.

### Is a database of every NFL/NBA/MLB player feasible?
**Yes — easily, and it's bounded.** The total set of everyone who has ever played in
those leagues is only in the tens of thousands. Sources:
- **Official stats APIs:** MLB Stats API (`statsapi.mlb.com`, free + thorough), the
  NBA stats API, NFL feeds; commercial: Sportradar, Stats Perform.
- **Sports Reference** (Basketball/Baseball/Pro-Football-Reference) — comprehensive
  historical rosters; **Wikidata** for long-tail/historical players.

You'd store it as a **player-master dimension** (canonical name, **aliases/nicknames**
like "Wemby" → Victor Wembanyama, team history, debut year, sport). This is the
biggest realistic upgrade to Tier 1: replace the fragile "capitalized-token"
heuristic (see §G) with a **lookup + fuzzy match** against the player master, which
also resolves nicknames. High value, low effort.

---

## D. Exactly which pages we scrape (Q2)

Per run the scraper makes **3 category requests + 9 set requests + 126 image
downloads = 138 requests**. It never touches the `robots.txt`-disallowed paths
(`/buy`, `/publish-offer`, `/stripe-connect`) and never fetches the individual
`/game/` card pages (we get everything from the set tables).

**robots.txt:** <https://www.sportscardspro.com/robots.txt>

**Category pages (3)** — to discover the set URLs:
- <https://www.sportscardspro.com/category/basketball-cards>
- <https://www.sportscardspro.com/category/baseball-cards>
- <https://www.sportscardspro.com/category/football-cards>

**Console / set pages (9)** — the price tables we actually parse:
- <https://www.sportscardspro.com/console/basketball-cards-2025-topps-chrome>
- <https://www.sportscardspro.com/console/basketball-cards-2023-panini-prizm>
- <https://www.sportscardspro.com/console/basketball-cards-2025-topps>
- <https://www.sportscardspro.com/console/baseball-cards-2026-topps>
- <https://www.sportscardspro.com/console/baseball-cards-2025-topps>
- <https://www.sportscardspro.com/console/baseball-cards-2024-topps>
- <https://www.sportscardspro.com/console/football-cards-2025-topps-chrome>
- <https://www.sportscardspro.com/console/football-cards-2024-panini-prizm>
- <https://www.sportscardspro.com/console/football-cards-2025-panini-prizm>

**Game (individual card) pages** — we DON'T fetch these, but we store the link as
`source_url`, e.g.
<https://www.sportscardspro.com/game/basketball-cards-2025-topps-chrome/victor-wembanyama-221>

**Images** — downloaded from Google Cloud Storage, e.g.
`https://storage.googleapis.com/images.pricecharting.com/4ejl5hifveyisrqi/240.jpg`

---

## E. Real end-to-end trace of ONE card (Q3)

Card: **2025 Topps Chrome Victor Wembanyama #221** (`listing_id = scp-11482641`).

### Step 1 — the page we hit
Set page: <https://www.sportscardspro.com/console/basketball-cards-2025-topps-chrome>.
The real `<tr>` for this card (trimmed):
```html
<tr data-product="11482641" id="product-11482641">
  <td class="image">
    <a href="https://www.sportscardspro.com/game/basketball-cards-2025-topps-chrome/victor-wembanyama-221">
      <img class="photo" src="https://storage.googleapis.com/images.pricecharting.com/4ejl5hifveyisrqi/60.jpg"/>
    </a>
  </td>
  <td class="title"><a>Victor Wembanyama #221</a></td>
  <td class="price ... used_price"><span class="js-price">$1.93</span></td>     <!-- Ungraded -->
  <td class="price ... cib_price"><span class="js-price">$18.51</span></td>    <!-- Grade 9 -->
  <td class="price ... new_price"><span class="js-price">$104.58</span></td>   <!-- PSA 10 -->
</tr>
```

### Step 2 — scraper grabs it (`parse_row`)
- `tr.get("data-product")` → `"11482641"`
- title `<a>` text → `"Victor Wembanyama #221"` → regex pulls **number 221**,
  **parallel None** (no `[..]`), **player "Victor Wembanyama"**
- no `<span class="rookie">` → **is_rookie False**
- the three price cells → **1.93 / 18.51 / 104.58**
- image `src` `.../60.jpg` → upgraded to `.../240.jpg`, downloaded to
  `data/images/11482641.jpg`

`parse_console_slug("...basketball-cards-2025-topps-chrome")` → **basketball / 2025 /
Topps Chrome**.

### Step 3 — scraper synthesizes the messy listing (`synthesize_listing`)
A grade is assigned for this copy (this one landed **PSA 10** → value **$104.58**,
the `new_price`), difficulty bucket = **clean**. The Bronze record written:
```json
{ "listing_id": "scp-11482641",
  "title": "2025 Topps Chrome Victor Wembanyama #221  PSA 10",
  "description": "Victor Wembanyama 2025 Topps Chrome #221 graded PSA 10. Ships in a top loader.",
  "image_path": "data/images/11482641.jpg",
  "ground_truth": { "player":"Victor Wembanyama","year":2025,"brand":"Topps Chrome",
                    "card_number":"221","parallel":null,"grade":"PSA 10","value_usd":104.58 },
  "_synthetic": { "difficulty":"clean" } }
```

### Step 4 — pipeline cleans/resolves it
`text_extract.extract(title, description)` on the combined text:
- `_find_year` → **2025**, `_find_set` → **Topps Chrome**, `_find_number` → **221**,
  `_find_grade` → **PSA 10** (so grade is "determined")
- `_find_parallel` → **None**, no uncertainty cue → `parallel_status = "base"`
- `_find_player` → **"Victor Wembanyama PSA"**  ⚠️ (the heuristic over-grabs "PSA";
  see §G — it doesn't change the outcome here, but it's a real wart)
- confidence = player 0.35 + set 0.20 + year 0.15 + number 0.15 + grade 0.15 = **1.00**

`routing.route(...)`: confidence 1.00 ≥ 0.75 **and** parallel_status is "base" (not
"uncertain") → **resolved**. `medallion.upsert_silver` writes the Silver row
(`decision=resolved`, `status=resolved_text`, `confidence=1.0`), and three events
(`ingested`, `tier1_extract`, `routed`) land in `pipeline_events.jsonl`.

Ground-truth check: player tokens overlap (✅), year ✅, number ✅, parallel both null
✅ → **fully correct**, resolved for **$0.00**.

---

## F. Running on a schedule without reprocessing (Q4)

If this ran on a trigger (say every 15 min, or per new sale), the danger is
re-ingesting cards we've already processed → wasted compute, **wasted LLM/vision
dollars**, and duplicate Gold records. Three layers of defense:

### 1. Idempotency (already built in)
`listing_id` is a **stable natural key** (`scp-<product_id>` now; the eBay item /
transaction id later), and `upsert_silver` uses `INSERT OR REPLACE`. So even if the
same record is reprocessed, it **overwrites** rather than duplicates. Idempotency
makes re-runs *safe* — but not *cheap*.

### 2. Watermark / delta processing (only touch new data)
Track a **high-water mark** = the timestamp (or monotonic id) of the last record we
successfully processed. Each run pulls only records **newer than the watermark**:
```
SELECT * FROM source WHERE event_ts > :last_watermark AND event_ts < :now_minus_safety
-- process ...
-- then advance: last_watermark = max(event_ts processed)
```
- For sold-transaction data, the natural watermark is the **sale timestamp**.
- **Late-arriving data** (a sale recorded with an older timestamp after the watermark
  moved) is handled by re-reading a small **overlap window** (`watermark − safety
  margin`) and leaning on idempotent upsert to dedupe the overlap. This "overlap +
  idempotent merge" combo is the standard pattern.
- Store the watermark durably: a small **control table**, **DynamoDB** item, or
  **SSM Parameter Store** value.

### 3. Change detection (skip unchanged re-seen records)
Compute a **content hash** of the meaningful fields (title + description + image +
price) and store the last hash per id. On re-seeing an id: same hash → **unchanged,
skip the expensive tiers**; different hash → reprocess. Catches "same listing, price
updated."

### How this looks on AWS at Alt
- **Trigger:** EventBridge cron, **or** event-driven (S3 `PutObject` / an SQS message
  per new transaction) — event-driven is naturally incremental (you only ever get new
  events).
- **Dedupe key:** `transaction_id` with a **DynamoDB conditional put** ("put if not
  exists") for near-exactly-once ingestion.
- **Watermark store:** DynamoDB item or SSM Parameter.
- **AWS-native bookmarking:** **AWS Glue job bookmarks** do watermarking for you —
  Glue tracks what it already processed between runs.
- **Idempotent sink:** MERGE into Silver/Gold keyed by `transaction_id` (warehouse)
  or conditional writes (DynamoDB).
- **Failure handling:** an SQS **dead-letter queue**; reprocessing from it is safe
  precisely because the sink is idempotent.

### What our code would add (next build)
Before processing, check the watermark / existing `listing_id`s in Silver and skip
ones already resolved or promoted to Gold (process only **new or changed** records) —
turning the current full-rescan into an incremental load.

---

## G. Known imperfections (be honest about these)
1. **Player heuristic over-grabs — now mitigated (§H).** The capitalized-token
   heuristic (`_candidate_name`) once extracted **"Victor Wembanyama PSA"**. Fixed
   two ways: grade companies are now in the stop-words, AND the **dim_player
   resolver** normalizes the candidate to the canonical name and verifies it exists.
   Players not in the master (MLB/NFL today) still fall back to the raw heuristic.
2. **Parallel vocabulary ceiling.** Exotic parallels ("Foilfractor", "Blackout")
   aren't in `KNOWN_PARALLELS`, so they resolve as **confidently base** — the
   dangerous "confidently wrong" case. Caught downstream by the image tier + the
   value-sorted human queue. Cleaner fix: escalate on an unrecognized modifier token.
3. **Synthetic listing text.** Cards, images, and values are 100% real (scraped); the
   eBay-style title is synthesized until the eBay API clears. Swapping in real titles
   changes nothing else.
4. **Confidence is a heuristic, not a model probability** — by design (see the
   `plan.md` discussion and the README to come). It's transparent, needs no training
   data, and is validated/tuned against ground truth.

---

## H. Reference dimensions (master data)

**Files:** `reference/schema.py` (DDL) · `reference/seed_vocabulary.py` ·
`reference/seed_players.py` · `reference/seed_all.py` · `reference/lookup.py`.
Seed once: `python -m reference.seed_all`. They live in the same SQLite DB as the
medallion tables but are seeded separately and are **not** dropped by a pipeline run.

### The tables (and the modeling decisions to defend)
- **`dim_vocabulary`** — 97 terms (sets, parallels, grade companies, uncertainty
  cues, stop words). A **typed reference dimension**: surrogate PK `term_id`, a
  `term_type` discriminator, the `term`, and a `canonical_term`. This replaces the
  hardcoded Python lists — `text_extract` loads from it and falls back to in-code
  defaults if it isn't seeded. (Reference data lives in data, not code — NOTES §C.)
- **`dim_player`** — 5,103 NBA/ABA players from nba_api's **offline static list**
  (no scraping/anti-bot). Grain = **one row per player**. PK = surrogate
  `player_id`; **natural key** = `nba_person_id` (UNIQUE); the name is an attribute.
- **`player_alias`** — nicknames/spellings → player (1-to-many): "Wemby" → Victor
  Wembanyama, "SGA" → Shai Gilgeous-Alexander, etc.
- **`bridge_player_season`** — created (empty) to make the model explicit: this is
  where **(player_id, season, team_id)** belongs — the composite key — *not* on the
  player. It's a roster bridge/fact, seeded from roster data later. **This is the
  answer to "should the player PK be (year, team, player)?": no — that's this
  separate bridge.**

### The resolver (`lookup.build_player_resolver`)
Loads dim_player + player_alias into memory once, returns a closure. **Precision-
first**: exact **full-name** or **alias** only, **accent-folded** ("Luka Doncic" ↔
"Luka Dončić"), with trailing-junk trimming ("Victor Wembanyama PSA" → "Victor
Wembanyama"). The extractor calls it to validate/normalize the name and treat a
verified player as full-weight.

### Lessons baked in (great interview material)
- **Cross-entity collision (found & fixed):** an earlier "unique last name" rule
  made NFL **J.J. McCarthy** resolve to NBA **Johnny McCarthy** ("McCarthy" was
  unique in the NBA master). We dropped lone-last-name matching. The *correct*
  production fix is **per-sport masters + sport-scoped resolution**.
- **The master also flags non-cards:** sealed boxes ("Mega Box", "Blaster Box")
  correctly fail to resolve — a free signal for "this listing isn't a single card."
- **Coverage today:** only basketball has a master, so **37 of 42** basketball cards
  resolve (the other 5 are boxes); MLB (MLB Stats API) and NFL masters extend this.

### Production shape (AWS)
dim tables → Redshift/Aurora/Glue; player/card masters as **conformed dimensions**;
**OpenSearch** for fuzzy matching at scale; alias growth via the human-review
feedback loop (NOTES §C).
