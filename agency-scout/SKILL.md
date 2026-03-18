---
name: agency-scout
description: Discovers and scores net-new Shopify agencies for Aftersell fit, deduplicates against the existing contact sheet, and writes a ranked list to a Google Sheets "Discovery" tab. Use when user says "discover agencies", "find new agencies", "/agency-scout", "build my agency list", "top of funnel agencies", "shopify agency list", "agency outreach", or "find agencies".
metadata:
  version: 2.0.0
  author: Nick Lawson
---

# Agency Scout

Scrapes the Shopify Partner Directory and ecosystem partner pages, enriches top candidates via LinkedIn, scores each agency 0–100 for Aftersell fit, deduplicates against the existing contact sheet, and writes a ranked "Discovery" tab ready for hand-off to agency-contact-mapper.

**Target output:** 20–50 net-new agencies scored ≥50, sorted descending by fit score.

---

## Setup

This skill requires the following environment variables. Set them in `~/.claude/settings.json` (recommended) or `~/.zshrc`.

**`~/.claude/settings.json` (recommended):**
```json
{
  "env": {
    "LINKEDIN_EMAIL": "your-linkedin-email@example.com",
    "LINKEDIN_PASSWORD": "your-linkedin-password",
    "AFTERSELL_SHEET_ID": "your-google-sheet-id",
    "GOOGLE_MCP_EMAIL": "your-gmail-address@gmail.com"
  }
}
```

**`~/.zshrc` (alternative):**
```bash
export LINKEDIN_EMAIL="your-linkedin-email@example.com"
export LINKEDIN_PASSWORD="your-linkedin-password"
export AFTERSELL_SHEET_ID="your-google-sheet-id"
export GOOGLE_MCP_EMAIL="your-gmail-address@gmail.com"
```

| Variable | Description |
|---|---|
| `LINKEDIN_EMAIL` | LinkedIn account email |
| `LINKEDIN_PASSWORD` | LinkedIn account password |
| `AFTERSELL_SHEET_ID` | Google Sheet ID for your agency tracking sheet |
| `GOOGLE_MCP_EMAIL` | Gmail address used to authenticate Google Workspace MCP |

---

## Sell Context

Aftersell is a post-purchase upsell and AOV optimization tool for Shopify merchants. Agencies use it to add a high-margin managed service to their client offerings. Best-fit agencies manage 10K+ order/month Shopify Plus merchants and have a CRO/growth service line.

---

## Step 0 — Ask for Target Count

Before doing anything else, ask the user:

> "How many agencies do you want to evaluate? Default is 50."

Store the answer as `TARGET`. If the user doesn't respond or says "default", use `TARGET = 50`.

Tell the user: "Got it — targeting [TARGET] agencies. Scraping the Shopify Partner Directory now."

---

## Phase 1 — Shopify Partner Directory Scrape

Scrape agency listings directly from the Shopify Partner Directory. Use the WebFetch → browser-use fallback chain for each page.

**Target geographies:** United States, Canada, Australia, United Kingdom

**Step 1 — Attempt WebFetch first:**

```
WebFetch: https://www.shopify.com/partners/directory?services[]=store-optimization&location=United+States
```

If WebFetch returns meaningful agency listings (names, tiers, ratings visible), parse the data and continue paginating.

**Step 2 — If WebFetch returns empty, JS-only, or 403:**

```bash
browser-use --browser real --headed open "https://www.shopify.com/partners/directory?services[]=store-optimization&location=United+States"
sleep 5
browser-use --browser real --headed eval "document.body.innerText" | grep -i "plus\|platinum\|premier\|select\|review\|partner\|agency\|studio" | head -200
```

**Step 3 — Paginate until TARGET * 2 reached:**

The directory paginates via "Load more" button or URL page parameter. Continue fetching pages until you have `TARGET * 2` agencies (over-fetch to account for deduplication loss).

For each page, click "Load more" or increment the page parameter:
```bash
browser-use --browser real --headed eval "var btn=Array.from(document.querySelectorAll('button')).find(b=>b.textContent.toLowerCase().includes('load more')||b.textContent.toLowerCase().includes('show more'));if(btn)btn.click();"
sleep 4
browser-use --browser real --headed eval "document.body.innerText" | grep -i "plus\|platinum\|premier\|select\|review" | head -200
```

**Step 4 — Try additional service filters if count is low:**

If raw count < TARGET after main scrape, also fetch these URLs (same WebFetch → browser-use approach):
```
https://www.shopify.com/partners/directory?services[]=conversion-rate-optimization&location=United+States
https://www.shopify.com/partners/directory?services[]=store-optimization&location=Canada
https://www.shopify.com/partners/directory?services[]=store-optimization&location=Australia
```

Merge results, deduplicating by agency name.

**Per agency, extract:**
- Agency name
- Partner tier (Platinum / Premier / Plus / Select)
- Star rating (if shown)
- Review count
- Location / geography
- Website domain
- Services listed
- Description snippet

Store as working list in memory — merge Phase 2 ecosystem signals into it.

Tell the user when Phase 1 completes: "Phase 1 complete — [N] agencies collected. Checking ecosystem partner pages now."

---

## Phase 2 — Ecosystem Partner Pages

After Phase 1, check if raw count has reached `TARGET`. If yes, skip to Phase 3. If not, continue pulling from ecosystem pages until `TARGET` is reached.

**Source priority for each page: WebFetch → browser-use → web search (last resort)**

| App | URL | Signal |
|:----|:----|:-------|
| Klaviyo | https://connect.klaviyo.com/ | Gold/Platinum/Elite = high-volume merchants |
| Gorgias | https://agencies.gorgias.com | Premier/Elite = enterprise CX work |
| Okendo | https://www.okendo.io/partners | Any listing = reviews-focused, Shopify-native |
| Rebuy | https://www.rebuy.com/shopify-partners | Any listing = personalization/upsell focus, adjacent to Aftersell |

**For each page, try in order:**

**Step 1 — WebFetch:**
Use the WebFetch tool on the URL. If it returns meaningful agency listings (names + tiers visible), use that data.

**Step 2 — If WebFetch returns empty, 403, 404, or only CSS/JS:**
```bash
browser-use --browser real --headed open "URL"
sleep 5
browser-use --browser real --headed eval "document.body.innerText" | grep -i "agency\|partner\|studio\|commerce\|tier\|gold\|platinum\|elite\|premier" | head -100
```

**Step 3 — If browser-use also fails (Cloudflare block, login wall):**
Fall back to WebSearch:
```
"[app name] partner agency list" OR "[app name] Gold Elite partner shopify 2025"
```
Extract agency names and inferred tier from search snippets. Note source as "web search" in working list.

Keep pulling pages/sources until raw count hits `TARGET`. Track running count and tell the user when each phase completes: "Phase 2 complete — [N] agencies collected so far."

Per listing extract: agency name, tier/badge, website domain.

**Merge rules:**
- If an agency from Phase 2 already appears in the Phase 1 list → add ecosystem signal (e.g. `klaviyo_gold: true`) to their record
- If net-new (not in Phase 1) → add to the working list with source = "ecosystem"

---

## Phase 3 — LinkedIn Enrichment

Cap at **30 agencies** to avoid rate limits. Prioritize Plus/Premier/Platinum tier agencies first — they score highest and benefit most from enrichment.

**Login first:**

```bash
browser-use --browser real --headed open "https://www.linkedin.com/login"
sleep 3
browser-use --browser real --headed state | grep "input\|submit" | head -5
EMAIL=$(bash -c 'echo $LINKEDIN_EMAIL')
PASS=$(bash -c 'echo $LINKEDIN_PASSWORD')
browser-use --browser real --headed input 4 "$EMAIL"
browser-use --browser real --headed input 6 "$PASS"
browser-use --browser real --headed click [submit-btn-index]
sleep 5
browser-use --browser real --headed eval "document.body.innerText" | head -5
# Should show "notifications" not "Sign in"
```

For each agency (search by name if no LinkedIn URL found):

```bash
browser-use --browser real --headed open "https://www.linkedin.com/search/results/companies/?keywords=[AGENCY NAME] shopify"
sleep 3
browser-use --browser real --headed eval "document.body.innerText" | grep -i "employees\|shopify\|about\|agency" | head -20
```

Navigate to the company page and extract from the About section:

```bash
browser-use --browser real --headed open "https://www.linkedin.com/company/[SLUG]/about/"
sleep 3
browser-use --browser real --headed eval "document.body.innerText" | grep -i "employees\|shopify plus\|checkout\|hydrogen\|bfcm\|retainer\|migration\|upsell" | head -30
```

Per agency, capture:
- Employee count (look for "X employees on LinkedIn")
- Whether "Shopify Plus" or Plus-specific language appears in About section
- LinkedIn company URL

**Close browser when done:**

```bash
browser-use --browser real server stop
```

---

## Phase 4 — Deduplication

Read all existing agency names from the contact sheet dynamically:

1. Call `mcp__google_workspace__get_spreadsheet_info` with Sheet ID `$AFTERSELL_SHEET_ID` to get all tab names
2. For each tab found, read column A: `mcp__google_workspace__read_sheet_values` with range `[TAB NAME]!A:A`
3. Build a set of known agency names (normalize: lowercase, strip punctuation)

Exclude any agency from the final output where the name fuzzy-matches a known agency.

---

## Phase 5 — Score + Write to Google Sheet

### Scoring Model (0–100)

Apply the scoring rubric from `references/scoring-rubric.md` to each agency using data from Phases 1–3.

**Add ecosystem signals from Phase 2 and LinkedIn signals from Phase 3 on top of base scores.**

**Only write agencies scoring ≥50 to the sheet.** Sort descending by fit score.

---

### Writing to Google Sheet

First check if "Discovery" tab exists:

```
mcp__google_workspace__get_spreadsheet_info
  spreadsheetId: $AFTERSELL_SHEET_ID
```

If "Discovery" tab does not exist, **ask the user to create it manually** in the sheet before proceeding — the Google Workspace MCP cannot create new sheet tabs via a write operation (it will throw "Unable to parse range"). The user just needs to open the sheet and add a tab named "Discovery".

Write header row first if the tab is new:

```
mcp__google_workspace__modify_sheet_values
  spreadsheetId: $AFTERSELL_SHEET_ID
  range: Discovery!A1:J1
  values: [["Agency Name", "Domain", "Location", "Partner Tier", "Ecosystem Partners", "Employee Count", "Fit Score", "Score Breakdown", "LinkedIn URL", "Notes"]]
```

Then write all qualifying agencies (score ≥50), sorted descending by Fit Score:

```
mcp__google_workspace__modify_sheet_values
  spreadsheetId: $AFTERSELL_SHEET_ID
  range: Discovery!A2:J[last_row]
  values: [[row1], [row2], ...]
```

**Output columns:**

| Col | Field | Example |
|-----|-------|---------|
| A | Agency Name | Fuel Made |
| B | Domain | fuelmade.com |
| C | Location | Vancouver, CA |
| D | Partner Tier | Plus |
| E | Ecosystem Partners | Klaviyo Gold, Gorgias Premier |
| F | Employee Count | 42 |
| G | Fit Score | 75 |
| H | Score Breakdown | Tier:+20 Reviews:+10 Geo:+10 Rating:+10 Services:+5 |
| I | LinkedIn URL | https://www.linkedin.com/company/fuel-made/ |
| J | Notes | Strong CRO language; BFCM case study in description |

---

## Verification

After writing:
1. Call `mcp__google_workspace__read_sheet_values` on `Discovery!A1:J5` to confirm the header + first 4 rows look correct
2. Report summary to user: "X agencies written to Discovery tab. Top 3: [name, score], [name, score], [name, score]."
3. Suggest: "Run `/agency-contact-mapper` on [top agency name] to start building contacts."

---

## Examples

### Example: "/agency-scout"

1. Ask user for target count — default 50
2. Scrape Shopify Partner Directory (WebFetch → browser-use) with service + location filters — collect agency names, tiers, ratings
3. Paginate until TARGET * 2 agencies collected
4. WebFetch Klaviyo, Gorgias, Okendo, Rebuy partner pages — add ecosystem signals to working list
5. Login to LinkedIn, enrich top 30 agencies by Plus tier — add employee count + Plus language signals
6. Call get_spreadsheet_info to get all sheet tabs — build deduplication exclusion set
7. Apply scoring rubric, keep agencies ≥50
8. Create/update Discovery tab — write sorted results with Score Breakdown column
9. Report summary

---

## Troubleshooting

### Shopify Partner Directory returns empty or JS-only via WebFetch
Switch to browser-use. The directory requires JS rendering for agency listings.

### LinkedIn rate limit / "You've reached the limit"
Stop LinkedIn enrichment immediately. Use whatever data was collected. Skip LinkedIn score component for un-enriched agencies — they'll still score via tier + ecosystem signals.

### WebFetch returns empty on ecosystem pages
The page requires JS rendering. Switch to:
```bash
browser-use --browser real --headed open "[URL]"
sleep 5
browser-use --browser real --headed eval "document.body.innerText" | grep -i "agency\|studio\|partner\|tier\|gold\|elite\|premier" | head -80
```

### Google Sheet tab name error ("Unable to parse range")
Always call `get_spreadsheet_info` first to get exact tab names. The Discovery tab may not exist yet — ask the user to create it manually before writing.

### Working list has <20 agencies after dedup
Lower the score threshold to ≥40 for this run, note in the Notes column "borderline — verify before outreach." Still exclude agencies already in the contact sheet.

---

> See `references/scaling-notes.md` for architecture notes and scale paths.
