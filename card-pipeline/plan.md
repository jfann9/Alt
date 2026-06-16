# Build 2 — Conditional CV/NLP Card Classification Pipeline

**Status:** Plan (approved scope, pre-build)
**Location:** `Alt/card-pipeline/`
**Stack:** Python 3.14 · Anthropic SDK · SQLite · Streamlit · open_clip · BeautifulSoup · eBay Browse API
**Interview target:** Senior Data Engineer @ Alt — cost-aware ML pipeline design + data-quality monitoring.

---

## 1. What this demonstrates

Alt's core entity-resolution problem: given a raw listing (`title` + `description` + `image`), determine the exact card — set, year, number, parallel, grade, language.

The architecture makes three points a senior data engineer is expected to land:

1. **Cost-aware conditional routing.** Run the cheapest classifier first; escalate to expensive ones (and ultimately a human) only for the residual. We quantify the savings vs. "run the expensive tiers on everything."
2. **Medallion data architecture.** Raw data is promoted Bronze → Silver → Gold, with explicit quality gates and a human-graded path into the trusted Gold layer.
3. **Data-quality monitoring.** A dashboard that shows the *health of the data assets* in real time — built for a small team where someone is on call to catch a degrading pipeline before it corrupts the Gold layer.

> **Key insight to articulate:** card identification is an **open-set retrieval / entity-resolution** problem, not fixed-class classification. The card universe is unbounded and grows weekly, so we never train a from-scratch classifier. We resolve with cheap text rules, then **retrieval over pretrained image embeddings**, then a vision LLM, then a human — paying for each tier only when the one before it isn't confident enough.

---

## 2. Medallion architecture (Bronze → Silver → Gold)

| Layer | Contents | Store | Quality gate |
|---|---|---|---|
| **Bronze** | Raw scraped listings + downloaded images, exactly as ingested. Immutable landing zone. | `data/bronze/listings_raw.jsonl` + `data/images/` | Ingestion validation only (well-formed record, image downloaded). |
| **Silver** | Cleaned, deduped, schema-validated records enriched with extracted fields, per-tier confidence, and routing provenance. The in-flight working layer. | SQLite `silver` table | Field extraction + confidence scoring + dedup. |
| **Gold** | Trusted, resolved canonical cards ready for consumption (valuation / marketplace). | SQLite `gold` table | Resolved at/above threshold by a tier, **or** specialist-graded out of quarantine. |
| **Quarantine** | Low-confidence records flagged for human review, priority-sorted. Promoted to Gold once a specialist grades them. | SQLite `quarantine` table | `value × (1 − confidence)` priority; specialist grade → promote. |

**Storage rationale:** SQLite for the medallion tables (so the dashboard can run real health queries), plus an append-only **JSONL event log** (`data/pipeline_events.jsonl`) recording each record's per-tier journey — the simple, walkable audit trail to narrate file-by-file in the interview.

---

## 3. The 4-tier cost-escalation engine

Every record enters at Tier 1 and stops at the first tier that clears the confidence threshold (default **0.75**). Below threshold after Tier 4 → **Quarantine**.

| Tier | Method | Relative cost | Resolves… |
|---|---|---|---|
| **1 — Regex / rules** | Pattern extraction: year, grade (`PSA\|BGS\|CGC \d+`), card number (`#\d+`), known sets, parallel keywords (Prizm, Silver, Refractor, Holo, Illustration Rare…), language. Confidence = weighted field coverage. | **Free** | Clean, well-formed titles. |
| **2 — LLM text** | `claude-sonnet-4-6`, structured JSON output + self-reported confidence. Only for records Tier 1 couldn't resolve. | **Cheap** ($3/$15 per MTok) | Fuzzy / ambiguous titles ("Special Edition Pikachu"). |
| **3 — CLIP image retrieval** | Embed the card image with pretrained CLIP, nearest-neighbor against the reference index (cosine). Distance → confidence. **No training.** | **Moderate** (local compute) | Visual-only distinctions: base vs. Silver Prizm, refractor variants. |
| **4 — Claude vision** | `claude-opus-4-8` / Sonnet vision, image input, for the hardest residual. | **Expensive** ($5/$25 per MTok, + image tokens) | Reprints/counterfeits ("REPRINT" on back), genuinely degraded photos. |
| **Terminal — Human** | Specialist grades the card; on approval it lands in Gold. | **Most expensive** | Everything still ambiguous. |

**Why this ordering matters at Alt's scale:** the expensive tiers (vision LLM, human specialist) are exactly the ones you cannot afford to run on 100% of volume. Conditional routing is the cost lever; the dashboard proves it.

### Ambiguity the dataset deliberately includes
Seeded so records exercise every tier (sourced from hobby research):
- **Base vs. Silver Prizm** — both look shiny; the Silver has the rainbow refractor and trades 3–5× base. Titles often omit "Silver" → Tier 1/2 low-confidence → **image tiers**.
- **Refractor vs. "Prizm" terminology** — Topps "Refractor" vs. Panini "Prizm" conflation.
- **Reprints & counterfeits** — "1952 Topps Mantle" for $50; 1986 Fleer Jordan fakes; legit reprints say "REPRINT" on the back (an image-only signal).

---

## 4. Data sources & scraping

Two ingestion paths (both requested), feeding the same Bronze schema:

1. **eBay Browse API** (`scraper/ebay_scraper.py`) — official, OAuth, free tier. Pulls ~100 active sports-card listings (title, price, condition, image URLs). *Dev account pending approval (≥1 business day).* Reads credentials from env vars; caches results to Bronze so the demo never hits eBay live.
2. **BeautifulSoup scraper** (`scraper/html_scraper.py`) — pure HTML scraping to demonstrate the skill directly.
   - **Primary target: [SportsCardsPro](https://www.sportscardspro.com/)** — static HTML price pages, predictable URL structure, real ungraded/PSA/BGS guide.
   - Secondary: [130point](https://130point.com/) sold-listing aggregator.
   - Posture: respect `robots.txt`/ToS, throttle requests, small one-time volume, cache to disk.

**Reference set** (`scraper/build_reference_set.py`) — builds `data/reference_cards.json` + reference images (reuse existing `images/card_art/` plus scraped images) that the CLIP tier matches against. Each reference has a known canonical card ID.

**Ground truth:** where derivable from clean source listings, store `ground_truth_id` for accuracy scoring on the dashboard. Sports-card emphasis (Alt's history favors sports over Pokémon), with a few Pokémon records for range.

---

## 5. Module layout

```
card-pipeline/
├─ scraper/
│  ├─ ebay_scraper.py          # eBay Browse API → Bronze (cached)
│  ├─ html_scraper.py          # BeautifulSoup → Bronze
│  └─ build_reference_set.py   # reference card index for CLIP
├─ data/
│  ├─ bronze/listings_raw.jsonl
│  ├─ images/                  # downloaded card images
│  ├─ reference_cards.json
│  ├─ pipeline.db              # SQLite: silver / gold / quarantine
│  └─ pipeline_events.jsonl    # per-record journey log
├─ pipeline/
│  ├─ ingestion.py             # Bronze load + validation
│  ├─ text_extract.py          # Tier 1 regex + Tier 2 LLM (real / --offline mock)
│  ├─ cv_retrieval.py          # Tier 3 CLIP embeddings + nearest-neighbor
│  ├─ vision_llm.py            # Tier 4 Claude vision (base64 image input)
│  ├─ routing.py               # confidence thresholds → next tier / terminal bucket
│  ├─ quarantine.py            # priority queue + specialist-grade → Gold promotion
│  ├─ medallion.py             # Bronze→Silver→Gold promotion + SQLite schema
│  ├─ quality.py               # data-quality metrics (nulls, dupes, schema fails, freshness)
│  ├─ costs.py                 # per-tier cost constants + comparison math
│  └─ logging_store.py         # JSONL event log writer
├─ run_pipeline.py             # orchestrator + CLI summary
├─ dashboard.py                # Streamlit data-quality + asset-browser dashboard
├─ requirements.txt
└─ README.md                   # architecture walkthrough for the interview
```

**LLM reliability:** real `claude-sonnet-4-6` (text) and Claude vision when `ANTHROPIC_API_KEY` is present; deterministic **`--offline` mock** otherwise, so the demo can't break on network/key. CLIP runs locally (no key needed); the rest of the pipeline degrades gracefully if CLIP isn't installed.

---

## 6. Data-quality monitoring dashboard (`dashboard.py`)

The interview explicitly emphasized a **data-quality monitoring dashboard to view the health of assets**, on a small team where someone is always on call to fix a pipeline that goes down. This is a headline deliverable, not a stats printout.

**Panels:**
- **Pipeline health** — records processed, throughput, success/error rate, per-stage latency, last-run time, **data freshness** (age of newest Gold record).
- **Asset health (red/yellow/green)** — status tiles per layer with **alert thresholds** that would page on-call: error rate > X, quarantine backlog > N, freshness stale > T, schema-validation-failure spike. An "alerts" feed lists active/recent breaches.
- **Data-quality metrics** — schema-validation failures, null/missing-field rates, duplicate rate, accuracy vs. ground truth, confidence-score distribution.
- **Cost panel** — actual cost (conditional routing) vs. "expensive tiers on 100% of records," with **% savings** headline.
- **Routing funnel** — counts/percent resolved at each tier and quarantined.
- **Quarantine review queue** — priority-sorted by `value × (1 − confidence)`; a specialist "grade" action that **promotes the record to the Gold layer** (demonstrates the human-in-the-loop Bronze→Gold flow).
- **Card browser / gallery** — visualize cards with images; filter by player/set/tier/status/layer; inspect a single record's full pipeline journey.

**Feedback-loop note (talking point):** specialist corrections are gold-standard labels — they grow the CLIP reference index and LLM few-shot examples over time (active learning), so the quarantine rate falls. The review queue *is* the labeling pipeline.

---

## 7. Build order

1. **Scaffold** — repo, `requirements.txt`, SQLite schema (`medallion.py`), config (threshold, cost constants, paths).
2. **Bronze** — BeautifulSoup scraper + reference-set builder; cache real data now (eBay scraper stubbed against API, wired when credentials clear).
3. **Tier 1 + routing + logging** — regex extraction, confidence, JSONL event log; get records flowing Bronze→Silver end-to-end with a CLI summary.
4. **Tier 2** — LLM text extraction (real + `--offline` mock).
5. **Tier 3** — CLIP retrieval + reference index.
6. **Tier 4** — Claude vision escalation.
7. **Quarantine + Gold** — priority queue, specialist-grade promotion.
8. **Quality + costs** — metrics module, cost comparison.
9. **Dashboard** — Streamlit data-quality + asset browser.
10. **README** — file-by-file architecture walkthrough.

---

## 8. Decisions log

| Decision | Choice | Rationale |
|---|---|---|
| Dataset size | ~100 records (scaled up from 30–50) | Real images make the demo convincing; scraping is core to the job. |
| Ingestion | eBay Browse API **+** BeautifulSoup | Both requested; API = realistic comp data, BS4 = raw scraping skill. |
| CV tier | CLIP retrieval + Claude vision | Real, no training; open-set retrieval is the production-correct framing. |
| Embeddings | Local open_clip (not Anthropic) | Anthropic has no embeddings endpoint; local = offline-safe, no key. |
| Storage | SQLite (medallion) + JSONL (event log) | Queryable health metrics for the dashboard + simple walkable audit log. |
| LLM models | Sonnet 4.6 (text), Opus 4.8/Sonnet (vision) | Cost-efficient text tier; capable vision for the hard residual. |
| LLM reliability | Real + `--offline` deterministic mock | Demo must not depend on a live key/network. |
| Quarantine priority | `value × (1 − confidence)` | Expected-loss triage — focus scarce human review where $ risk is highest. |
| Dashboard | Streamlit, data-quality-first | Matches the interview's stated asset-health / on-call emphasis. |

---

## 9. Out of scope
- Real model training (open-set retrieval is the correct approach — see §1).
- Production auth, orchestration (Airflow/Dagster), real alerting/paging integrations — simulated in-dashboard.
- Build 1 (Gallery View) — complete, lives in `Alt/gallery-view/`.
- Stage-3 founder pitch (Alt Tablet partnership) — verbal only, no code.
