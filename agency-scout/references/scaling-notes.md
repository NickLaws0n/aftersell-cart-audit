# Scaling Notes

> Architectural notes for the skill owner. Not used during execution.

## Data Source

Phase 1 scrapes the Shopify Partner Directory live on each run via WebFetch → browser-use. Agencies are collected fresh per session — no local database required.

**Scale path:** For high-frequency runs (daily or more), consider adding a local cache layer (SQLite or JSON file) so the directory scrape only runs when the cache is stale (e.g. >15 days old). This mirrors the original architecture but keeps the dependency local rather than assumed.

## Scoring Model

Base scores are computed from directory data (tier, rating, review count, geo, services description). LinkedIn enrichment adds employee count signal for agencies in the top results. Description-based signals (Plus language, competitor mentions) activate after scraping the agency's LinkedIn About section.

## Full GTM Pipeline (current architecture)

```
Shopify Partner Directory (live scrape, Phase 1)
        ↓
Ecosystem partner pages: Klaviyo, Gorgias, Okendo, Rebuy (Phase 2)
        ↓
LinkedIn enrichment — top 30 agencies (Phase 3)
        ↓
Scoring + deduplication + sheet write (Phases 4–5)
        ↓
agency-contact-mapper (contacts per qualified agency)
        ↓
agency-intel-digest (LinkedIn signals before outreach)
```
