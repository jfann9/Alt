# Alt Interview Prep — Claude Code Project Prompt

Use this as your starting prompt in Claude Code (VS Code terminal). Paste the whole thing as your first message in a fresh project folder. Adjust the bracketed notes as needed.

---

## Project Context

I'm preparing for a Senior Data Engineer interview process at Alt (a platform for vaulting, trading, and valuing high-end collectible cards — sports cards, Pokémon, TCG). The process has three stages over ~2-3 weeks:

1. **Recruiter "vibe check"** (next week, non-technical) — I want to demo a UI concept
2. **Technical interview** (2+ weeks out) — data engineering / ML pipeline design
3. **Founder/business interview** (later) — strategic pitch (not part of this build)

This Claude Code project covers builds for stage 1 and stage 2 only. Stage 3 is a verbal pitch and not part of this codebase — **do not build anything for it**, just keep it noted as a future to-do (see bottom of this prompt).

---

## Build 1: "Gallery View" — Static React Mockup (Priority: HIGH, build first)

### Goal
Alt's current collection dashboard is data/finance-heavy (think a Zillow-style "Zestimate" table: cost basis, gain/loss %, vaulted status). I want to demo a **Gallery View** toggle that reframes a collector's portfolio around the *art and emotional value* of their cards — for the audience that cares about characters, illustrations, and personal collections, not just valuation.

This is a **static, no-backend, locally-hosted React app**. All data should be hardcoded/mocked — no API calls, no persistence needed. It needs to look and feel like a real feature extension of Alt's existing product, not a standalone concept page.

### Required Features

**1. Dual-view dashboard**
- Recreate a simplified version of Alt's existing "My Collection" table view (item, Alt Value, cost basis, gain/loss %, vaulted status — similar to Alt's real dashboard)
- Add a prominent toggle (e.g., "List View" / "Gallery View") at the top
- Gallery View replaces the table with a visual grid/card-based layout showing card images large and prominently
- Toggling should feel instant and polished (smooth transition is a nice-to-have, not required)

**2. Albums / Collections**
- Users can group cards into custom albums (e.g., "Water-type favorites," "Evolution lines," "Childhood nostalgia")
- Include a "Create Album" modal/flow — doesn't need to persist data, but should be interactive (opens, lets you name an album, lets you "add" a card via click, closes)
- Show at least 2-3 pre-populated example albums on load

**3. Showcase / Themed Background Mode**
- For at least one album, demo a "Showcase Mode" — a custom background that complements the card art (this is the AI-generated background concept)
- I have a reference image of a Pokémon evolution line (Froakie → Frogadier → Mega Greninja ex) displayed against a matching water/ocean-themed background — recreate this concept as one example showcase
- Pre-render or hardcode this background image; the demo should show a "Generate Background" or "Showcase" button that swaps in this pre-made image (faked AI generation — instant swap is fine)

**4. Community touch**
- Add a small "Featured Albums" or "Explore" section/carousel with 3-4 hardcoded example albums from "other users" (fake usernames are fine)
- Optional: a simple "likes" count display (static numbers, no interactivity needed)

**5. Business framing callout**
- Include a small text callout (footer or sidebar) framing the business rationale, e.g.: "Concept: gallery and album features increase session time and emotional attachment to collections, which correlates with higher marketplace engagement and listing rates."

### Design Notes
- Match Alt's visual identity loosely: clean, modern, purple/violet accent color (#7C5CFC-ish), white backgrounds, sans-serif typography, card-based UI elements
- Mobile-friendly is a bonus but not required — desktop-first is fine since I'll be demoing on a laptop
- Use placeholder card images (I'll provide a few real card images, or use simple colored rectangles with labels if none provided)
- Keep it to a **single page** with the view toggle — don't build multi-page routing unless it's trivial

### Tech Stack
- Vite + React
- Tailwind CSS for styling
- No backend, no database, no API calls
- Should run with `npm run dev` and be viewable at localhost

---

## Build 2: Conditional CV/NLP Card Classification Pipeline (Priority: HIGH, build second)

### Goal
Demonstrate a **cost-aware data pipeline architecture** for Alt's core entity resolution problem: given a raw transaction/listing (title + description + image), determine the exact card (set, year, number, parallel, grade) it represents.

The key architectural insight to demonstrate: **run cheap text-based classification first; only escalate to computer vision when text confidence is low.** This shows I understand cost/scale tradeoffs in ML pipeline design — not just "call an API for everything."

### Required Features

**1. Sample/synthetic dataset**
- Create ~30-50 synthetic listing records as JSON, each with: `title`, `description`, optional `image_path` (can be placeholder/sample card images), and a "ground truth" card ID for validation
- Mix of clear listings (e.g., "2025 Pokemon Mega Evolution Illustration Rare Vulpix #138 PSA 10") and ambiguous ones (e.g., "Special Edition Pikachu Pokemon Card")

**2. Text-based extraction/classification stage**
- A function/module that parses title + description and attempts to extract: set name, year, card number, parallel/variant, grade, language
- Use regex/rule-based extraction for structured patterns (years, card numbers, grade strings like "PSA 10")
- For fuzzy/ambiguous text, use an LLM call (Claude API via the Anthropic SDK) to attempt extraction and return a structured JSON response with a confidence score
- Output: extracted fields + a confidence score (0-1)

**3. Confidence-based routing**
- Define a confidence threshold (e.g., 0.75)
- If confidence ≥ threshold → route to "resolved" bucket, log the result
- If confidence < threshold → flag for CV escalation, route to "CV queue"

**4. Mock CV stage**
- For items in the CV queue, simulate a computer vision classification step (this can be a stubbed/mocked function — doesn't need a real trained model; could use a simple image hash/lookup against a small reference set of sample card images, or just simulate with a delay + canned response)
- Output: refined classification + updated confidence

**5. Logging/output**
- Log every record's journey through the pipeline (text-stage result, routing decision, CV-stage result if applicable, final classification) to a structured output (JSON lines file or SQLite table)
- Build a small summary/dashboard (can be a simple CLI printout, a Jupyter-style notebook, or a tiny Streamlit/React dashboard) showing:
  - Total records processed
  - % resolved via text alone
  - % escalated to CV
  - Estimated cost comparison: "cost if CV ran on 100% of records" vs. "actual cost with conditional routing"

### Design Notes
- This is primarily a **backend/data pipeline demo** — visual polish matters less than clarity of architecture and logs/output
- If time allows, a minimal dashboard (even a simple HTML page or Streamlit app) showing the routing stats would be a strong visual artifact for the interview
- Keep the code modular: separate files/modules for ingestion, text extraction, routing logic, CV stub, and logging — I want to be able to walk through the architecture file-by-file in the interview

### Tech Stack
- Python (preferred for this one — data engineering interviews often expect Python/SQL fluency)
- Anthropic SDK for the LLM extraction step (use Claude Sonnet 4.6 for cost efficiency)
- SQLite or JSON Lines for output storage
- Optional: Streamlit for a quick dashboard, or keep it to a CLI summary + a Jupyter notebook walkthrough

---

## Working Style / Constraints

- I'm on Claude Pro — please default to efficient, scoped tasks. Don't propose large refactors or multi-agent approaches.
- Build Project 1 (Gallery View) to completion first, fully working and demoable, before starting Project 2.
- For each project, start with a brief plan/file structure before writing code, so I can confirm scope.
- Keep components/modules small and well-commented — I need to be able to explain every part of this in interviews.
- Prioritize "demoable and explainable" over "production-grade" — this is interview prep, not a real product.

---

## To-Do / Save for Later (Do NOT build)

- **Alt Tablet partnership pitch** (founder/business interview, stage 3): brick-and-mortar data collection via in-store tablets at card shops, positioned as a data moat / first-mover advantage in offline transaction data. This is a verbal pitch only — no code needed. Revisit closer to that interview date for talking points and slide prep.