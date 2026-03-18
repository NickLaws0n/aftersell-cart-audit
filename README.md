# Aftersell Claude Skills

A Claude Code skill built for an **SMB Agency Partner Manager** workflow at Aftersell by Rokt.

---

## Skills

### 🔍 [`cart-audit`](./cart-audit/)
**Audits a Shopify merchant's cart and checkout flow for Aftersell feature gaps.**

Crawls a live store with browser-use, evaluates 14 Aftersell/UpCart features (cart drawer, checkout extensions, post-purchase upsell, Rokt Thanks, etc.), detects competing apps, and generates a self-contained HTML scorecard. Built for walking into agency conversations with proof — not guesses — about what's missing.

```
/cart-audit freeflyapparel.com
```

---

## Install

```bash
git clone https://github.com/NickLaws0n/aftersell-skills-public.git
cp -r aftersell-skills-public/cart-audit ~/.claude/skills/
```

Skills are picked up automatically by Claude Code on next session start.

### Requirements

- [Claude Code](https://claude.ai/code)
- [browser-use](https://github.com/browser-use/browser-use) installed
- `python3` (standard on macOS/Linux)

No API keys or credentials required.

---

## Why This Skill

Showing up to an agency conversation with a live audit of their client's store is more effective than a generic pitch. This skill came out of wanting a repeatable, verifiable way to identify what's missing — so conversations start from proof, not assumptions.

The scorecard template, feature checklist, and detection patterns are all works in progress and designed to be improved iteratively.
