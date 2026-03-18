---
name: agency-intel-digest
description: Scrapes a Shopify agency's LinkedIn company page and key contacts' recent activity, summarizes sales signals, and posts a structured digest to Slack. Use when user says "run agency digest for [agency]", "what's happening at [agency]", "agency intel for [domain]", "digest [agency]", "LinkedIn digest for [agency]", or "what is [agency] posting about".
allowed-tools: "Bash(browser-use:*) Bash(python3:*) Bash(curl:*)"
metadata:
  version: 1.0.0
  author: Nick Lawson
---

# Agency Intel Digest

Scrapes a Shopify agency's LinkedIn activity (company page + key BD/Sales contacts), summarizes into an actionable sales digest, and posts to Slack with direct source links.

Sell context: Aftersell is a post-purchase upsell and AOV optimization tool for Shopify merchants.

---

## Setup

This skill requires the following environment variables. Set them in `~/.claude/settings.json` (recommended) or `~/.zshrc`.

**`~/.claude/settings.json` (recommended):**
```json
{
  "env": {
    "LINKEDIN_EMAIL": "your-linkedin-email@example.com",
    "LINKEDIN_PASSWORD": "your-linkedin-password",
    "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  }
}
```

**`~/.zshrc` (alternative):**
```bash
export LINKEDIN_EMAIL="your-linkedin-email@example.com"
export LINKEDIN_PASSWORD="your-linkedin-password"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

| Variable | Description |
|---|---|
| `LINKEDIN_EMAIL` | LinkedIn account email |
| `LINKEDIN_PASSWORD` | LinkedIn account password |
| `SLACK_WEBHOOK_URL` | Incoming webhook URL from your Slack workspace ([create one here](https://api.slack.com/messaging/webhooks)) |

---

## CRITICAL — Must Read Before Running

**LinkedIn browser rules:**
- Always use `--browser real --headed` (requires real Chrome session)
- Read credentials from env: `EMAIL=$(bash -c 'echo $LINKEDIN_EMAIL')` and `PASS=$(bash -c 'echo $LINKEDIN_PASSWORD')`
- `eval` with multi-line functions returns None — use simple one-liner evals only
- Post URLs come from URN extraction via regex on page HTML, NOT querySelectorAll (post links are in shadow DOM)
- Always dismiss the "Allow Pages to see you visited" dialog before navigating to target pages
- Close browser when done: `browser-use --browser real server stop`

**Slack rules:**
- Use Python `urllib` to POST — not curl (escaping issues with complex JSON)
- Put source URLs on their own lines — raw URL, Slack auto-renders them clickable
- Do NOT use `<URL|text>` format — unreliable rendering

---

## Phase 1: LinkedIn Login (browser-use)

```bash
browser-use --browser real --headed open "https://www.linkedin.com/login"
sleep 3
```

Get login field indices:
```bash
browser-use --browser real --headed state | grep "input\|submit" | head -5
```

Read credentials and login (use actual indices from state output, typically 4/5/6):
```bash
EMAIL=$(bash -c 'echo $LINKEDIN_EMAIL')
PASS=$(bash -c 'echo $LINKEDIN_PASSWORD')
browser-use --browser real --headed input 4 "$EMAIL"
browser-use --browser real --headed input 6 "$PASS"
browser-use --browser real --headed click [submit-btn-index]
sleep 5
```

Verify login succeeded — page should show "notifications" not "Sign in":
```bash
browser-use --browser real --headed eval "document.body.innerText" | head -5
```

---

## Phase 2: Find the Agency's LinkedIn Slug

If not already known, search for it:
```bash
browser-use --browser real --headed open "https://www.linkedin.com/search/results/companies/?keywords=[AGENCY NAME]"
sleep 3
browser-use --browser real --headed eval "document.body.innerText" | grep -i "linkedin.com/company" | head -5
```

The slug is the path segment after `/company/` in their LinkedIn URL.

---

## Phase 3: Find Key Contacts to Monitor

Navigate to the agency's people page:
```bash
browser-use --browser real --headed open "https://www.linkedin.com/company/[SLUG]/people/"
sleep 4
```

Dismiss "Allow Pages to see you visited" if it appears:
```bash
browser-use --browser real --headed state | grep "Don't allow\|Allow$" | head -3
# Click "Don't allow" button if present
```

Get the "What they do" filter indices:
```bash
browser-use --browser real --headed state | grep -A30 "What they do" | head -35
```

Click Business Development filter, extract names + titles:
```bash
browser-use --browser real --headed click [BD-BUTTON-INDEX]
sleep 4
browser-use --browser real --headed eval "document.body.innerText" | grep -E "Message$" -B 2 | grep -v "^\-\-$" | grep -v "^Message$"
```

Turn off BD, click Sales filter, extract:
```bash
browser-use --browser real --headed click [BD-BUTTON-INDEX]  # turn off
sleep 1
browser-use --browser real --headed click [SALES-BUTTON-INDEX]
sleep 4
browser-use --browser real --headed eval "document.body.innerText" | grep -E "Message$" -B 2 | grep -v "^\-\-$" | grep -v "^Message$"
```

**Keep contacts matching these roles:** CEO, President, COO, VP/Director Sales, GTM, Head of BD, Client Strategy, Account Director, CRO, Retention, Growth, Partnerships
**Skip:** developers, engineers, ops, marketing coordinators, customer support, designers

---

## Phase 4: Scrape Company Page Posts

```bash
browser-use --browser real --headed open "https://www.linkedin.com/company/[SLUG]/posts/?feedView=all&sortBy=recency"
sleep 4
```

Click "Show more results" if present:
```bash
browser-use --browser real --headed eval "var btn=Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('Show more'));if(btn)btn.click();"
sleep 3
```

Extract post text (up to 3000 chars):
```bash
browser-use --browser real --headed eval "document.body.innerText" | grep -v "^$\|Skip to\|Keyboard\|^Home$\|My Network\|^Jobs$\|^Notifications$\|^Me$\|For Business\|Try Premium\|^Follow$\|^Like$\|^Comment$\|^Repost$\|^Send$" | head -200
```

Extract post URNs for source links:
```bash
browser-use --browser real --headed eval "var urns=document.documentElement.innerHTML.match(/urn:li:activity:\d+/g)||[];return [...new Set(urns)].slice(0,8).join('\n')"
```

URN → post URL: `https://www.linkedin.com/feed/update/urn:li:activity:XXXXXXXXX/`

---

## Phase 5: Scrape Key Contact Activity

For each priority contact identified (max 4 contacts to keep runtime reasonable):

```bash
browser-use --browser real --headed open "https://www.linkedin.com/in/[PROFILE-SLUG]/recent-activity/all/"
sleep 4
browser-use --browser real --headed eval "document.body.innerText" | grep -v "^$\|Skip to\|Keyboard\|^Home$\|My Network\|^Jobs$\|^Notifications$\|^Me$\|For Business\|Try Premium\|^Follow$\|^Like$\|^Comment$\|^Repost$\|^Send$" | head -120
```

Extract URNs per contact:
```bash
browser-use --browser real --headed eval "var urns=document.documentElement.innerHTML.match(/urn:li:activity:\d+/g)||[];return [...new Set(urns)].slice(0,4).join('\n')"
```

---

## Phase 6: Check Twitter/X (optional)

```bash
browser-use --browser real --headed open "https://x.com/[HANDLE]"
sleep 3
browser-use --browser real --headed eval "document.body.innerText" | head -50
```

If "This account doesn't exist" appears, skip. Otherwise extract top 5 posts.

---

## Phase 7: Close Browser

```bash
browser-use --browser real server stop
```

---

## Phase 8: Summarize (Claude inline)

With all scraped content in context, summarize into this structure:

**Signals to watch for:**
- New hires in CRO, retention, growth, BD, or GTM roles
- Job postings signaling investment areas
- Case studies or client wins (especially mentioning AOV, upsell, retention)
- Posts explicitly mentioning post-purchase, upsell, conversion, or AOV
- Event appearances (conferences, panels) — warm outreach opportunity
- Tech stack mentions or app partnerships

**Output format:**
```
🔥 Top Signals
[2-4 bullets, each tied to a specific post with source URL on next line]

💬 Outreach Hooks
[1-3 ready-to-use openers tied to specific activity, format: Name — "opener"]

📌 Agency Focus Right Now
[1-2 sentences on what the agency is prioritizing this week]

⚠️ Nothing Notable (if applicable)
[Say so clearly if nothing signal-worthy was found]
```

---

## Phase 9: Post to Slack (Python)

Build and send the Block Kit payload using Python urllib. Put source URLs on their own lines within mrkdwn text blocks — Slack auto-renders them as clickable links.

```python
import json, os, urllib.request

WEBHOOK = os.environ["SLACK_WEBHOOK_URL"]

payload = {
  "blocks": [
    {
      "type": "header",
      "text": {"type": "plain_text", "text": "📡 [AGENCY] — Intel Digest  |  [DATE]", "emoji": True}
    },
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "*🔥 Top Signals*\n\n[signal 1 text]\n[source URL]\n\n[signal 2 text]\n[source URL]"}
    },
    {"type": "divider"},
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "*💬 Outreach Hooks*\n\n[hooks]"}
    },
    {"type": "divider"},
    {
      "type": "section",
      "text": {"type": "mrkdwn", "text": "*📌 Agency Focus Right Now*\n[summary]"}
    },
    {
      "type": "context",
      "elements": [{"type": "mrkdwn", "text": "Sources: LinkedIn company page + [contact names] • Generated by Claude"}]
    }
  ]
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(WEBHOOK, data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(resp.read().decode())
```

Run with `python3 [script]` or via inline Bash heredoc.

---

## Examples

### Example: "run agency digest for Example Agency"

1. Login to LinkedIn
2. Navigate to `linkedin.com/company/example-agency/people/` → filter BD + Sales → identify key contacts (e.g. Head of BD, VP Sales)
3. Scrape company page posts → extract URNs
4. Scrape each contact's recent activity → extract URNs
5. Close browser
6. Summarize: find hiring signals, AOV/retention posts, event appearances
7. Post to Slack with source URLs

### Example: "what's happening at Agency B this week"

Same flow using that agency's LinkedIn slug.

---

## Troubleshooting

### Login page shows after navigating to people page
Session expired. Re-run Phase 1 login steps before continuing.

### "Allow Pages to see you visited" dialog blocks navigation
Find button index with `state | grep "Don't allow"` then click it before proceeding.

### `eval` returns `None` for complex functions
Break into simple one-liners. Multi-line arrow functions and complex closures silently fail. Use `document.body.innerText` + grep pipeline instead.

### URN extraction returns empty array
The page may not have loaded posts yet. Run `browser-use scroll down` + `sleep 2` + click "Show more results" before extracting.

### Slack message sends `ok` but links aren't clickable
URLs must be on their own line with no surrounding text or markdown. Do not use `<URL|text>` format — use plain URL on a newline.

### People page shows very few contacts
Your account may have limited network visibility. Use "What they do" filters (BD, Sales) which surface more results than the default view. Also try: `linkedin.com/search/results/people/?keywords=[agency name]`
