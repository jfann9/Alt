"""Pipeline orchestrator (Build: Tier 1).

Bronze -> [Tier 1 regex extract] -> [route] -> Silver, logging every step.
Later builds plug Tier 2 (LLM text), Tier 3 (CLIP), Tier 4 (vision), and the
human quarantine into the same loop. Run from the project root:

    python run_pipeline.py
"""
from __future__ import annotations

import io
import sys

# Synthesized titles contain emoji; force UTF-8 so Windows console prints don't crash.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

import config as C
from pipeline import ingestion, logging_store, medallion, routing, text_extract


# --------------------------------------------------------------------------- #
# Ground-truth scoring (we only have truth because we synthesized from a source;
# real eBay data won't, which is exactly why the human-review loop exists later).
# --------------------------------------------------------------------------- #
def _field_checks(extracted: dict, gt: dict) -> dict:
    def player_ok():
        ep = {t for t in (extracted.get("player") or "").lower().split()}
        gp = {t for t in (gt.get("player") or "").lower().split()}
        return bool(ep & gp) if gp else None

    def parallel_ok():
        ep, gp = extracted.get("parallel"), gt.get("parallel")
        if not gp and not ep:
            return True
        return bool(ep and gp and ep.lower() == gp.lower())

    return {
        "player": player_ok(),
        "year": (extracted.get("year") == gt.get("year")) if gt.get("year") else None,
        "card_number": (str(extracted.get("card_number")) == str(gt.get("card_number")))
        if gt.get("card_number") else None,
        "parallel": parallel_ok(),
    }


def main() -> None:
    print("Loading Bronze layer...")
    listings = ingestion.load_listings()
    print(f"  {len(listings)} listings\n")

    conn = medallion.connect()
    medallion.init_db(conn, reset=True)
    logging_store.reset()

    # Tallies for the summary
    by_decision: dict[str, int] = {}
    by_next: dict[str, int] = {}
    crosstab: dict[tuple[str, str], int] = {}
    resolved_records: list[tuple[dict, dict]] = []  # (extracted_fields, ground_truth)

    for listing in listings:
        lid = listing["listing_id"]
        logging_store.log("ingested", lid, title=listing.get("title"))

        extraction = text_extract.extract(listing["title"], listing.get("description", ""))
        logging_store.log(
            "tier1_extract", lid,
            confidence=extraction["confidence"],
            parallel_status=extraction["parallel_status"],
            fields=extraction["fields"],
        )

        decision = routing.route(extraction)
        logging_store.log(
            "routed", lid,
            decision=decision["decision"], next_tier=decision["next_tier"],
            reason=decision["reason"],
        )

        medallion.upsert_silver(conn, listing, extraction, decision)

        # Tally
        by_decision[decision["decision"]] = by_decision.get(decision["decision"], 0) + 1
        key = decision["next_tier"] or "resolved_text"
        by_next[key] = by_next.get(key, 0) + 1
        diff = listing.get("_synthetic", {}).get("difficulty", "?")
        crosstab[(diff, key)] = crosstab.get((diff, key), 0) + 1
        if decision["decision"] == "resolved":
            resolved_records.append((extraction["fields"], listing.get("ground_truth", {})))

    conn.commit()
    conn.close()
    _summary(len(listings), by_decision, by_next, crosstab, resolved_records)


def _summary(total, by_decision, by_next, crosstab, resolved_records) -> None:
    print("=" * 64)
    print("TIER 1 — REGEX EXTRACTION + ROUTING")
    print("=" * 64)
    print(f"Records processed : {total}")
    res = by_next.get("resolved_text", 0)
    print(f"Resolved by text  : {res} ({res / total:.0%})  -> Silver (resolved)")
    for tier in ("llm_text", "cv_retrieval"):
        n = by_next.get(tier, 0)
        print(f"Escalated -> {tier:<12}: {n} ({n / total:.0%})")

    print("\nRouting by synthetic difficulty (sanity check):")
    diffs = ["clean", "ambiguous_text", "ambiguous_image"]
    routes = ["resolved_text", "llm_text", "cv_retrieval"]
    print(f"  {'difficulty':<18}" + "".join(f"{r:>15}" for r in routes))
    for d in diffs:
        row = "".join(f"{crosstab.get((d, r), 0):>15}" for r in routes)
        print(f"  {d:<18}{row}")

    # Text-resolution accuracy vs ground truth (resolved records only)
    print("\nText-resolution accuracy vs ground truth (resolved records only):")
    if resolved_records:
        agg: dict[str, list[int]] = {}
        fully_correct = 0
        for extracted, gt in resolved_records:
            checks = _field_checks(extracted, gt)
            applicable = [v for v in checks.values() if v is not None]
            if applicable and all(applicable):
                fully_correct += 1
            for field, ok in checks.items():
                if ok is not None:
                    agg.setdefault(field, []).append(1 if ok else 0)
        for field, vals in agg.items():
            print(f"  {field:<14}: {sum(vals)}/{len(vals)} ({sum(vals)/len(vals):.0%})")
        print(f"  {'all fields':<14}: {fully_correct}/{len(resolved_records)} "
              f"({fully_correct/len(resolved_records):.0%}) fully correct")
    else:
        print("  (none resolved)")

    # Cost note — the real comparison lands once the paid tiers exist.
    print("\nTier-1 spend: $0.00 (regex is free).")
    escalated = total - by_next.get("resolved_text", 0)
    naive = total * C.TIER_COSTS["llm_text"]
    actual = escalated * C.TIER_COSTS["llm_text"]
    print(f"Projected text-tier cost  — LLM on 100%: ${naive:.3f}  |  "
          f"conditional ({escalated} escalated): ${actual:.3f}  "
          f"({(1 - actual/naive) if naive else 0:.0%} saved so far)")
    print(f"\nSilver layer written -> {C.DB_PATH}")
    print(f"Event log written    -> {C.EVENTS_LOG}")


if __name__ == "__main__":
    main()
