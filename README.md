# Aftersell Claude Skills

A collection of Claude Code skills built for an **SMB Agency Partner Manager** workflow at Aftersell by Rokt. Each skill automates a core part of the agency partnership workflow — from identifying who to talk to, to walking into a conversation with a fully prepared audit of their client's store.

---

## Skills

### 🔍 [`cart-audit`](./cart-audit/)
**Audits a Shopify merchant's cart and checkout flow for Aftersell feature gaps.**

Crawls a live store with browser-use, evaluates 14 Aftersell/UpCart features (cart drawer, checkout extensions, post-purchase upsell, Rokt Thanks, etc.), detects competing apps, and generates a self-contained HTML scorecard. Built for walking into agency conversations with proof — not guesses — about what's missing.

```
/cart-audit freeflyapparel.com
```

---

### 🗂️ [`agency-contact-mapper`](./agency-contact-mapper/)
**Maps sales-relevant contacts at Shopify agencies for outreach.**

Takes an agency domain, searches the web and browses their LinkedIn people page, finds and verifies emails via Hunter.io, and writes contacts to a master Google Sheet — with priority ratings and tailored sell angles for each role. Filters out developers, ops, and support; targets CEOs, BD leads, client strategy, CRO, and GTM roles.

```
map contacts at example-agency.com
```

### 🧭 [`agency-scout`](./agency-scout/)
**Discovers and scores net-new Shopify agencies for Aftersell fit.**

Scrapes the Shopify Partner Directory and ecosystem partner pages (Klaviyo, Gorgias, Okendo, Rebuy), enriches with LinkedIn data, scores each agency 0–100 against a fit model (partner tier, ecosystem signals, size, geography, CRO language), deduplicates against your existing contact sheet, and writes a ranked list to a Google Sheets "Discovery" tab — ready to hand off to agency-contact-mapper.

```
/agency-scout
find new agencies
build my agency list
```

---

### 📡 [`agency-intel-digest`](./agency-intel-digest/)
**Monitors a Shopify agency's LinkedIn activity and delivers a sales intelligence digest to Slack.**

Logs into LinkedIn, finds the agency's most relevant BD and Sales contacts dynamically, scrapes their recent posts and company page activity, extracts direct source links, and posts a structured digest to Slack — Top Signals, Outreach Hooks, and Agency Focus Right Now.

```
run agency digest for example-agency
what's happening at agency-b this week
```

---

## Setup

### 1. Install skills

```bash
git clone https://github.com/NickLaws0n/aftersell-skills.git
cp -r aftersell-skills/cart-audit ~/.claude/skills/
cp -r aftersell-skills/agency-contact-mapper ~/.claude/skills/
cp -r aftersell-skills/agency-intel-digest ~/.claude/skills/
cp -r aftersell-skills/agency-scout ~/.claude/skills/
```

Skills are picked up automatically by Claude Code on next session start.

### 2. Configure credentials

Add to `~/.claude/settings.json` (recommended — most reliable with Claude Code's Bash tool):

```json
{
  "env": {
    "LINKEDIN_EMAIL": "your-linkedin-email@example.com",
    "LINKEDIN_PASSWORD": "your-linkedin-password",
    "HUNTER_API_KEY": "your-hunter-io-api-key",
    "AFTERSELL_SHEET_ID": "your-google-sheet-id",
    "GOOGLE_MCP_EMAIL": "your-gmail-address@gmail.com",
    "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  }
}
```

Alternatively, export from `~/.zshrc` — but note that Claude Code's Bash tool does not always inherit shell env vars reliably. The `settings.json` approach is preferred.

See `.env.example` for a full variable reference.

### 3. Required accounts / tools

| Skill | Requires |
|---|---|
| All LinkedIn skills | LinkedIn account |
| `agency-contact-mapper` | [Hunter.io](https://hunter.io) API key (free tier works) |
| `agency-contact-mapper`, `agency-scout` | Google Sheet + [Google Workspace MCP](https://github.com/anthropics/mcp-google-workspace) configured |
| `agency-intel-digest` | Slack incoming webhook ([setup guide](https://api.slack.com/messaging/webhooks)) |
| All skills | [browser-use](https://github.com/browser-use/browser-use) installed |

---

## Why These Skills

The goal was to demonstrate how AI/automation can increase leverage and consistency in a partnership sales role. Each skill came out of a real workflow gap:

- **cart-audit** — showing up to an agency conversation with a live audit of their client's store is more effective than a generic pitch
- **agency-contact-mapper** — building a target contact list shouldn't require hours on LinkedIn
- **agency-scout** — systematic top-of-funnel discovery and scoring before any manual research begins
- **agency-intel-digest** — warm outreach based on what an agency is actually doing this week beats cold templates

All four are designed to be improved iteratively. The scorecard template, feature checklist, scoring model, and signal detection logic are all works in progress.
