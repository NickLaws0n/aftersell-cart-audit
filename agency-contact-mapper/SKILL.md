---
name: agency-contact-mapper
description: Researches and maps sales contacts at Shopify agencies for Aftersell outreach. Searches the web, browses LinkedIn company people pages, finds and verifies emails via Hunter.io, and writes results to Google Sheets. Use when user says "research agency contacts", "map contacts at [agency]", "find contacts at [domain]", "add [agency] to the contact sheet", "agency contact research", or "who should I reach out to at [agency]".
metadata:
  version: 1.0.0
  author: Nick Lawson
---

# Agency Contact Mapper

Maps sales-relevant contacts at Shopify agencies for Aftersell outreach. For each agency: searches the web for leadership/BD/strategy contacts, browses their LinkedIn people page, finds and verifies emails via Hunter.io, and writes results to the master Google Sheet.

## Setup

This skill requires the following environment variables. Set them in `~/.claude/settings.json` (recommended) or `~/.zshrc`.

**`~/.claude/settings.json` (recommended):**
```json
{
  "env": {
    "LINKEDIN_EMAIL": "your-linkedin-email@example.com",
    "LINKEDIN_PASSWORD": "your-linkedin-password",
    "HUNTER_API_KEY": "your-hunter-io-api-key",
    "AFTERSELL_SHEET_ID": "your-google-sheet-id",
    "GOOGLE_MCP_EMAIL": "your-gmail-address@gmail.com"
  }
}
```

**`~/.zshrc` (alternative):**
```bash
export LINKEDIN_EMAIL="your-linkedin-email@example.com"
export LINKEDIN_PASSWORD="your-linkedin-password"
export HUNTER_API_KEY="your-hunter-io-api-key"
export AFTERSELL_SHEET_ID="your-google-sheet-id"
export GOOGLE_MCP_EMAIL="your-gmail-address@gmail.com"
```

| Variable | Description |
|---|---|
| `LINKEDIN_EMAIL` | LinkedIn account email for browsing company people pages |
| `LINKEDIN_PASSWORD` | LinkedIn account password |
| `HUNTER_API_KEY` | [Hunter.io](https://hunter.io) API key for email finding/verification |
| `AFTERSELL_SHEET_ID` | Google Sheet ID for your contact tracking sheet |
| `GOOGLE_MCP_EMAIL` | Gmail address used to authenticate Google Workspace MCP |

## CRITICAL — Who to Target vs. Skip

**INCLUDE (priority contacts):**
- CEO, President, COO, Founder, Managing Director
- VP / Director of Sales, Head of Sales, Sales Director
- GTM Lead, Head of Growth, VP Growth
- Head of Business Development, BD Manager
- Client Strategy, Client Engagement Director, Account Director
- Director of CRO, Retention Marketing lead
- VP / Director of Strategy
- Strategic Alliances / Partner Marketing

**ALWAYS SKIP:**
- Developers, Engineers, Tech Leads, CTOs (unless they own client revenue)
- Operations staff
- Marketing coordinators / Marketing Managers (not Director level)
- Customer Support / Customer Success (execution-only roles)
- Designers, UX, Creative
- Finance, HR, Legal

## Sell Context

Aftersell is a post-purchase upsell and AOV optimization tool for Shopify merchants. Agencies use it to add a high-margin managed service to their client offerings.

**Sell angle by role:**
- **CEO / Founder / President:** Agency differentiation + retainer revenue opportunity from a new managed service line
- **Head of BD / GTM:** New service line they can pitch into existing client base
- **Head of Sales / Sales Director:** Partner tool that helps close and expand client revenue
- **Client Strategy / Account Director:** Fast client wins on AOV/retention; reduces churn risk
- **CRO / Retention lead:** AOV lift + complements their existing lifecycle/email work
- **COO:** High-margin service layer; hard to offshore; improves client delivery outcomes
- **Strategic Alliances / Partner Marketing:** Agency partner program opportunity

## Workflow

### Phase 1: Web Research (WebSearch)

For each agency domain:

1. Run two WebSearch queries:
   - `site:linkedin.com "[agency name]" CEO OR President OR "head of" OR "VP" OR "director" OR "GTM" OR "growth" OR "strategy" OR "account"`
   - `"[agency name]" shopify agency leadership team "director" OR "VP" OR "head of" site:linkedin.com`
2. Also fetch their press release page or news for recent hires: `"[agency name]" new leadership OR "joins as" OR "appointed"`
3. Capture all named contacts with titles. Note LinkedIn URLs when found.
4. Also fetch their `/news` or `/about` page via WebFetch if relevant results appear.

### Phase 2: LinkedIn People Page (browser-use)

1. Open `browser-use --browser real --headed open https://www.linkedin.com/login`
2. Read env vars and login:
   ```bash
   EMAIL=$(bash -c 'echo $LINKEDIN_EMAIL')
   PASS=$(bash -c 'echo $LINKEDIN_PASSWORD')
   ```
   Then: `input 4 "$EMAIL"`, `input 6 "$PASS"`, `click` submit, wait 5 seconds
3. Navigate to `https://www.linkedin.com/company/[company-slug]/people/`
   - Find the slug from the LinkedIn URL in web search results
4. Dismiss any "Allow Pages to see you visited" dialog — click "Don't allow"
5. Scroll down, click "Show more results" if present
6. In the "What they do" filter section, click **Business Development** — extract all names + titles
7. Turn off Business Development, click **Sales** — extract all names + titles
8. Apply filters one at a time. Record: Name, Title
9. Close browser: `browser-use --browser real server stop`

**Tip:** Use `eval "document.body.innerText"` and grep for "Message$" -B 2 to extract names efficiently.

### Phase 3: Email Discovery (Hunter.io API via Bash)

For each contact identified:

**Step 1 — Email finder:**
```bash
curl -s "https://api.hunter.io/v2/email-finder?domain=DOMAIN&first_name=FIRST&last_name=LAST&api_key=$HUNTER_API_KEY"
```
Extract `.data.email` and `.data.score`.

**Step 2 — If email not found, guess from pattern:**
- Check what pattern confirmed emails use (e.g. `firstname@domain.com` or `firstname.lastname@domain.com`)
- Verify guessed emails:
```bash
curl -s "https://api.hunter.io/v2/email-verifier?email=EMAIL&api_key=$HUNTER_API_KEY"
```
Extract `.data.status` (`valid` / `invalid`) and `.data.score`.

**Only include emails where status = `valid` OR Hunter finder score >= 85.**

### Phase 4: Write to Google Sheet (Google Workspace MCP)

1. First call `mcp__google_workspace__get_spreadsheet_info` with sheet ID `$AFTERSELL_SHEET_ID` to find the correct sheet tab name and last used row.
2. Write contacts using `mcp__google_workspace__modify_sheet_values` starting after the last row of data.
3. Use the sheet tab that matches the agency name. If no matching tab exists, append to the main contacts tab.

**Columns (A through I):**
| Col | Field | Example |
|-----|-------|---------|
| A | Agency | Example Agency |
| B | Name | Jane Smith |
| C | Title | VP of Sales |
| D | LinkedIn URL | https://www.linkedin.com/in/janesmith/ |
| E | Priority | ⭐⭐⭐ |
| F | Sell Angle | Owns sales — partner tools that help close client revenue |
| G | Email | jane.smith@example-agency.com |
| H | Email Confidence | 96 - verified |
| I | Notes | Found via LinkedIn BD filter |

**Priority scoring:**
- ⭐⭐⭐ = Direct revenue owner or C-suite; will influence buy decision
- ⭐⭐ = Relevant role but not primary decision maker
- ⭐ = Worth knowing but low priority (e.g. ops, lower-level BD)

## Examples

### Example: "Research contacts at [domain]"

User says: "map contacts at example-agency.com"

Actions:
1. WebSearch for leadership at Example Agency
2. Browse `https://www.linkedin.com/company/example-agency/people/` — filter BD + Sales
3. Run Hunter.io email-finder for each contact found
4. Verify any guessed emails
5. Write to sheet tab matching agency, or append to main tab

Result: Contacts written to sheet with emails, priorities, and sell angles.

### Example: "Add multiple agencies"

User says: "research contacts at agency-a.com and agency-b.com"

Actions: Run the full workflow for each agency sequentially. Write each agency's contacts in one batch call per agency.

## Troubleshooting

### LinkedIn shows "Sign in" after navigation
The session expired. Re-run the login steps (Phase 2, steps 1–2) before navigating to the people page.

### LinkedIn people page shows no results / few people
Your account may have limited network visibility. Use the "What they do" filters (Business Development, Sales) which tend to surface more results than the default view. Also try the LinkedIn search approach: `https://www.linkedin.com/search/results/people/?keywords=[agency+name]`

### Hunter.io returns empty for domain search
The domain may not be indexed. Skip domain search and go straight to email-finder per person. If email-finder also returns nothing, try common patterns (firstname@, firstname.lastname@) and verify each.

### Google Sheet tab name error ("Unable to parse range")
The tab name in the sheet may differ from what you expect. Always call `get_spreadsheet_info` first to get exact tab names before writing.

### Contact title is blurred on LinkedIn (3rd degree connection)
Note "title redacted — confirm before outreach" in the Notes column. Use web search for their name + agency to find the title from press releases, their personal website, or RocketReach/ZoomInfo.
