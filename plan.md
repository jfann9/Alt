# Project 1 — "Gallery View" Static React Mockup — Build Plan

> Status: **Planned, not yet executed.** This document is the agreed scope/file structure
> for Build 1 (recruiter "vibe check" demo). Build 2 (CV/NLP pipeline) is out of scope here.

---

## 1. Goal (recap)

A **static, no-backend, locally-hosted** Vite + React app that demos a **Gallery View** toggle
for Alt's "My Collection" dashboard. It reframes a collector's portfolio around **art and
emotional value** (characters, illustrations, albums) instead of pure finance/valuation —
while still looking like a real feature extension of Alt's existing product.

All data is hardcoded. No API calls, no persistence. Runs with `npm run dev` at localhost.

---

## 2. Assets available (already provided)

Located in `Alt/images/`:

| File | Use in build |
|---|---|
| `images/card_art/froakie.jpg` | Card tile — Evolution line + Water album |
| `images/card_art/frogadier.jpg` | Card tile — Evolution line + Water album |
| `images/card_art/greninja.jpg` | Mega Greninja ex (Water, HP 350) — hero card |
| `images/card_art/mega_charizard.png` | Mega Charizard EX — Nostalgia album hero |
| `images/card_art/ai_background.png` | **Showcase Mode** background (evolution line on ocean scene) |
| `images/card_art/ai_background_art.png` | Alt/secondary framed showcase variant |
| `images/alt_my_collection_ui.png` | Visual reference for **List View** (do not ship) |
| `images/alt_homepage.png` | Visual reference for **Gallery View** framed look (do not ship) |

Card images will be copied into `gallery-view/src/assets/` at build time so the Vite app
bundles them. The 4 real cards are the hero items; ~4–6 extra synthetic entries use
gradient placeholder tiles to give the collection realistic volume.

---

## 3. Visual identity (from the real Alt UI references)

**Header (matches `alt_my_collection_ui.png`):**
- `ALT` wordmark (left) · search bar "Search by name or cert #"
- Nav: ALL ITEMS · AUCTIONS (red **LIVE** badge) · MARKET TRENDS · MY COLLECTION (purple) · **SELL** button · hamburger
- Sub-nav tabs: **My collection** (active, purple underline) · Fixed price · Auction · Sold

**List View (replicate the My Collection table):**
- Top-right **TOTAL VALUE** card: `$XXX ▲ NN.NN% (all time)` in a pale-green pill
- "N ITEMS" count · "Filter By" dropdown (decorative)
- Columns: `ITEM | ALT VALUE | COST BASIS | GAIN/LOSS % | LAST COMP | STATUS | VAULTED DATE`
- Row: thumbnail + title, Alt value with low–high range, green/red gain%, ✓ Vaulted + SELL chip
- Clean white bg, gray header row, purple accents

**Gallery View (borrow the `Featured Auctions` aesthetic):**
- Larger card-forward grid; elevated "framed" tiles with soft shadow/glow
- Card name, grade, and value beneath each tile

**Theme tokens:** purple/violet accent `#7C5CFC`, white backgrounds, sans-serif typography,
rounded card-based elements.

---

## 4. Tech stack

- **Vite + React** (JS, not TS — keeps it readable for interview walkthrough)
- **Tailwind CSS v4** via the `@tailwindcss/vite` plugin (single `@import "tailwindcss"`;
  no `tailwind.config.js`/PostCSS dance). Theme tokens defined in `index.css`.
- No backend, no DB, no routing (single page).

### Prerequisite
- **Node.js LTS** must be installed (it was not present on this machine; installed via
  `winget install OpenJS.NodeJS.LTS` as part of environment setup).

---

## 5. File structure

```
Alt/gallery-view/
├── index.html
├── package.json
├── vite.config.js               # React + @tailwindcss/vite
├── README.md                    # how to run
└── src/
    ├── main.jsx                 # React entry
    ├── App.jsx                  # top-level state + layout
    ├── index.css                # @import "tailwindcss" + theme tokens
    ├── data/
    │   └── mockData.js          # cards, user albums, featured albums, usernames
    ├── assets/                  # copied card images + showcase backgrounds
    └── components/
        ├── Header.jsx           # Alt nav + List/Gallery toggle
        ├── CollectionSummary.jsx# TOTAL VALUE pill + item count + filter
        ├── ListView.jsx         # My Collection table
        ├── GalleryView.jsx      # responsive framed image grid
        ├── CardTile.jsx         # single card tile (image, name, value, album add)
        ├── AlbumStrip.jsx       # user's albums row (chips/cards)
        ├── CreateAlbumModal.jsx # interactive create-album flow
        ├── ShowcaseMode.jsx     # "Generate Background" → swaps in ai_background.png
        ├── FeaturedAlbums.jsx   # community carousel + static likes
        └── BusinessCallout.jsx  # footer rationale text
```

---

## 6. Feature → file mapping (covers all 5 required features)

| # | Required feature | Implementation |
|---|---|---|
| 1 | Dual-view dashboard + prominent toggle | `App.jsx` holds `view` state; `Header.jsx` toggle switches `ListView` ⇄ `GalleryView` (instant, light CSS transition) |
| 2 | Albums + Create Album modal | `AlbumStrip.jsx` shows 3 pre-populated albums; `CreateAlbumModal.jsx` opens, names an album, click-to-"add" cards, closes (in-memory only) |
| 3 | Showcase / themed background | `ShowcaseMode.jsx` on the "Evolution lines" album: "Generate Background" button swaps in `ai_background.png` (faked AI, instant) |
| 4 | Community "Featured Albums" + likes | `FeaturedAlbums.jsx` carousel: 3–4 albums from fake users + static like counts |
| 5 | Business framing callout | `BusinessCallout.jsx` footer: session-time / emotional-attachment → engagement rationale |

---

## 7. Mock data design (`mockData.js`)

- **Cards (~8–10):** the 4 real cards (Froakie, Frogadier, Mega Greninja ex, Mega Charizard EX)
  + synthetic placeholders. Each: `id, name, image, grade, altValue, valueLow, valueHigh,
  costBasis, gainLossPct, lastComp, vaulted, vaultedDate, type, albumIds`.
- **User albums (3):**
  - `Evolution lines` → Froakie, Frogadier, Mega Greninja ex  *(has Showcase Mode)*
  - `Water-type favorites` → Froakie, Frogadier, Greninja
  - `Childhood nostalgia` → Charizard + placeholders
- **Featured albums (3–4):** fake usernames (e.g. `@vault_king`, `@pokeart_jenny`), titles,
  cover image, static like counts.

---

## 8. Build order (execution checklist — do not run until approved)

1. Install Node.js LTS (prerequisite). *(done as env setup)*
2. Scaffold `gallery-view/` (Vite React) + Tailwind v4; confirm `npm run dev` serves localhost.
3. Copy card images into `src/assets/`.
4. Build `mockData.js`.
5. `Header.jsx` + `CollectionSummary.jsx` + `ListView.jsx` (replicate My Collection table).
6. `GalleryView.jsx` + `CardTile.jsx`; wire the List/Gallery toggle in `App.jsx`.
7. `AlbumStrip.jsx` + `CreateAlbumModal.jsx` (interactive, in-memory).
8. `ShowcaseMode.jsx` (evolution-line background swap).
9. `FeaturedAlbums.jsx` + `BusinessCallout.jsx`.
10. Polish: theme tokens, spacing, transitions; final `npm run dev` smoke test.

---

## 9. Constraints / working style

- Demoable + explainable over production-grade. Small, well-commented components.
- Single page, desktop-first. No refactors, no multi-agent approaches.
- Build 1 to full working/demoable state before any Build 2 work.

---

## 10. Out of scope (noted, do not build)

- **Build 2** (Conditional CV/NLP card classification pipeline) — separate effort.
- **Stage 3** Alt Tablet partnership pitch — verbal only, no code.
