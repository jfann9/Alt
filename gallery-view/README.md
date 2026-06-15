# Alt — Gallery View Concept

Static React mockup of a **Gallery View** for Alt's "My Collection" dashboard.
Reframes a collector's portfolio around the art and emotional value of cards
(albums, showcase backgrounds, community) while still matching Alt's real UI.

No backend, no API calls — all data is hardcoded in `src/data/mockData.js`.

## Run

```bash
npm install
npm run dev
```

Then open the printed localhost URL.

## What to demo

- **List ⇄ Gallery toggle** (top-right of the sub-nav) — List View recreates Alt's
  finance table; Gallery View shows the art large.
- **Albums** — seed albums "Pokémon" and "Basketball" filter the view. "+ Create
  Album" opens an interactive modal (name it, click cards to add, save).
- **Showcase Mode** — in Gallery View with the Pokémon album active, click
  "Generate Background" for the AI-themed ocean backdrop.
- **Featured Albums** — community section with fake users + like counts.
- **Business callout** — footer rationale.

## Structure

- `src/App.jsx` — state + layout
- `src/components/*` — one small component per feature
- `src/data/mockData.js` — cards, albums, featured albums
- `public/card_art/` — card images
