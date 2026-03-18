---
name: cart-audit
description: Crawls a Shopify Plus merchant's cart and checkout flow with browser-use, evaluates 14 Aftersell/Upcart features with four-state status (ACTIVE_AFTERSELL, ACTIVE_OTHER, MISSING, UNVERIFIED), detects integrations and competing apps, and generates a self-contained HTML scorecard. Use when user says "cart audit", "/cart-audit [url]", "audit [store]", or "check aftersell features on [store]". Do NOT use for competitor A/B analysis (use competitor-ab-audit instead).
allowed-tools: Bash(browser-use:*), Bash(python3:*)
metadata:
  version: 2.1.0
---

# Skill: /cart-audit

Audit a Shopify Plus merchant for Aftersell/Upcart feature gaps. Primary output: **what's missing and with what confidence** — gap list first, no revenue estimates. Intended for Aftersell partner managers preparing targeted client conversations.

---

## CRITICAL: Rules That Must Not Be Broken

**Cart Drawer:**
- Run the DOM check (`querySelector` for `cart-drawer`, `CartDrawer`, `side-cart`, `mini-cart`) BEFORE screenshotting — drawers are in the DOM before animation completes
- A toast/snackbar/badge that says "item added" is NOT a cart drawer
- A real drawer is a substantial side panel containing cart items that overlays the page

**Cart Upsells:**
- Check for upsells in the cart DRAWER (Phase C) AND on the /cart page (Phase D) — either counts
- Do not navigate away from the drawer before running the HTML eval

**Checkout:**
- All brands are assumed Shopify Plus — checkout features are always in scope
- Evaluate from screenshots + DOM — mark MISSING if not visible, not UNVERIFIED
- UNVERIFIED is only for checkout login walls

**Scorecard:**
- No revenue numbers anywhere in output
- Always runs via inline `python3 - << 'HEREDOC'` using `references/scorecard_template.py` as the base

---

## Step 1: Gather Inputs

Parse the URL from the invocation: `/cart-audit https://storename.com`

- `STORE_URL` — strip trailing slash
- `STORE_NAME` — derive from domain: `storename.com` → `Storename`

Confirm before crawling:
> "Starting cart audit of [STORE_NAME]. Crawling homepage → PDP → cart → checkout, scoring 14 features, detecting integrations, then building the scorecard."

---

## Step 2: Browser Crawl

Session name: `cart-audit`. **Read every screenshot immediately after capture** — visual signals are faster than HTML parsing.

### Phase A: Collect Install Signals & Homepage Scripts

```bash
browser-use --session cart-audit open STORE_URL
browser-use --session cart-audit screenshot /tmp/cart_audit_home1.png
```

Read `/tmp/cart_audit_home1.png`. Dismiss any cookie banner or geo-redirect before proceeding.

```bash
browser-use --session cart-audit scroll down
browser-use --session cart-audit screenshot /tmp/cart_audit_home2.png
```

Collect all script srcs and check install signals:

```bash
browser-use --session cart-audit eval "Array.from(document.querySelectorAll('script[src]')).map(s=>s.src).filter(s=>s.includes('aftersell')||s.includes('AftersellApp')).join(', ') || 'none'"
browser-use --session cart-audit eval "Array.from(document.querySelectorAll('script[src]')).map(s=>s.src).filter(s=>s.includes('upcart')||s.includes('UpCart')).join(', ') || 'none'"
browser-use --session cart-audit eval "Array.from(document.querySelectorAll('script[src]')).map(s=>s.src).join('\n')"
```

Save all script srcs — they're used in Phase F for the full integration scan.

### Phase B: Navigate to Product Page & Check PDP Upsell

```bash
browser-use --session cart-audit open STORE_URL/collections/all
browser-use --session cart-audit state
# Click first available product
browser-use --session cart-audit click INDEX
browser-use --session cart-audit screenshot /tmp/cart_audit_pdp.png
```

Read screenshot immediately. Look for any upsell/recommendation block below the ATC button.

```bash
browser-use --session cart-audit eval "document.documentElement.innerHTML.includes('aftersell-pdp') || document.documentElement.innerHTML.includes('product-page-upsell') ? 'FOUND' : 'NOT_FOUND'"
```

If `/collections/all` 404s: try `/shop`, `/products`, or scan homepage links.

If variants are required: select first option before proceeding to Phase C.

### Phase C: Add to Cart & Detect Drawer + Contents

```bash
browser-use --session cart-audit state
browser-use --session cart-audit click ATC_INDEX
```

**Wait 2 seconds, then run DOM check BEFORE screenshotting:**

```bash
browser-use --session cart-audit eval "
var drawerEl = document.querySelector('[class*=\"cart-drawer\"],[id*=\"cart-drawer\"],[class*=\"CartDrawer\"],[id*=\"CartDrawer\"],[class*=\"ajax-cart\"],[class*=\"side-cart\"],[class*=\"fly-out-cart\"],[class*=\"mini-cart\"]');
var drawerVisible = drawerEl && (drawerEl.style.display !== 'none') && (drawerEl.offsetParent !== null || drawerEl.style.visibility !== 'hidden');
JSON.stringify({drawer_element: !!drawerEl, drawer_visible: drawerVisible, url: window.location.href, drawer_class: drawerEl ? drawerEl.className.substring(0,80) : null})
"
```

```bash
browser-use --session cart-audit screenshot /tmp/cart_audit_atc.png
```

Read screenshot. If drawer is PRESENT, check its contents:

```bash
browser-use --session cart-audit eval "
var html = document.documentElement.innerHTML;
JSON.stringify({
  drawer_upsell: html.includes('upcart-upsell') || html.includes('aftersell-recommendations') || html.includes('upsell-widget') || html.includes('upsell_widget'),
  drawer_rewards: html.includes('upcart-rewards') || html.includes('rewards-tier') || html.includes('free-shipping-bar') || html.includes('shipping-progress'),
  drawer_announcement: html.includes('upcart-announcement') || html.includes('cart-announcement'),
  drawer_shipping_protection: html.includes('upcart-shipping-protection') || html.includes('shipping-protection'),
  drawer_trust: html.includes('upcart-trust') || html.includes('trust-badge'),
  drawer_addon: html.includes('upcart-addon') || html.includes('cart-addon'),
  upcart_elements: document.querySelectorAll('[class*=\"upcart\"],[id*=\"upcart\"]').length,
  aftersell_elements: document.querySelectorAll('[class*=\"aftersell\"],[id*=\"aftersell\"]').length
})"
```

```bash
browser-use --session cart-audit scroll down
browser-use --session cart-audit screenshot /tmp/cart_audit_atc2.png
```

### Phase D: Check /cart Page & Scan HTML Signals

```bash
browser-use --session cart-audit open STORE_URL/cart
browser-use --session cart-audit screenshot /tmp/cart_audit_cart1.png
browser-use --session cart-audit scroll down
browser-use --session cart-audit screenshot /tmp/cart_audit_cart2.png
```

Read both screenshots. Note: some stores only use a cart drawer and redirect /cart to homepage — this is fine.

```bash
browser-use --session cart-audit eval "document.querySelectorAll('[class*=\"upcart\"],[id*=\"upcart\"],[class*=\"aftersell\"],[id*=\"aftersell\"],[data-aftersell]').length + ' aftersell/upcart elements'"
```

Collect cart page scripts (integration scan):
```bash
browser-use --session cart-audit eval "Array.from(document.querySelectorAll('script[src]')).map(s=>s.src).join('\n')"
```

### Phase E: Proceed to Checkout & Evaluate Features

Click the checkout button from cart state, or navigate directly if needed.

```bash
browser-use --session cart-audit screenshot /tmp/cart_audit_checkout1.png
```

Read screenshot immediately. If login wall: set `CHECKOUT_BLOCKED = True`, mark all checkout features UNVERIFIED.

```bash
browser-use --session cart-audit scroll down
browser-use --session cart-audit screenshot /tmp/cart_audit_checkout2.png
```

Check for Aftersell checkout extensions in the DOM:
```bash
browser-use --session cart-audit eval "
var html = document.documentElement.innerHTML;
var idx = html.indexOf('aftersell');
idx >= 0 ? html.substring(idx-20, idx+200).replace(/&quot;/g,'\"') : 'not found'
"
```

Evaluate each checkout feature from screenshots:
- **Checkout Upsell** — product cards with Add buttons in the order summary panel?
- **Checkout Trust Badges** — security/guarantee badge images (not native payment card icons)?
- **Checkout Testimonials** — star ratings + review text visible?
- **Checkout Rewards Bar** — progress bar visible anywhere in checkout?
- **Checkout Announcements** — banner at the very top of the checkout page?

### Phase F: Complete Integration Scan

Combine scripts from all phases. Scan against patterns in `references/integrations.md`.

```bash
browser-use --session cart-audit eval "Array.from(document.querySelectorAll('script[src]')).map(s=>s.src).join('\n')"
```

### Phase G: Close Session

```bash
browser-use --session cart-audit close
```

---

## Step 3: Feature Evaluation

### Install Detection

**Aftersell INSTALLED if:** script src contains `aftersell` or `AftersellApp`, OR `window.aftersell` defined, OR inline JS contains aftersell config, OR checkout HTML contains `"appName":"Aftersell`.

**Upcart INSTALLED if:** script src contains `upcart` or `UpCart`, OR DOM has elements with `upcart-*` classes.

### Feature Status — Four States

| Status | Icon | Meaning | When to use |
|---|---|---|---|
| `ACTIVE_AFTERSELL` | ✓ green | Present, powered by Aftersell/Upcart | Feature visible + Aftersell/Upcart confirmed |
| `ACTIVE_OTHER` | ≠ blue | Present, powered by another app | Feature visible + no Aftersell/Upcart script |
| `MISSING` | ✗ red | Not detected | Feature checked, not found, detection reliable |
| `UNVERIFIED` | ⚠ amber | Could not check | Login wall, bot block only |

Evidence for `ACTIVE_OTHER`: `"Feature active via [App Name] — consolidation opportunity"`

### Confidence Levels

- **HIGH** — observed in screenshot AND confirmed in HTML/DOM
- **MEDIUM** — one signal only (screenshot OR HTML), OR ambiguous
- **LOW** — not detected, but could be explained by store state (below threshold, geo-gated, product-specific)

### Feature List — 14 Features

#### Cart & PDP

| # | Feature | Key detection signals |
|---|---|---|
| 1 | Cart Drawer | DOM: `cart-drawer`/`CartDrawer`/`side-cart`/`mini-cart` visible; Screenshot: side panel overlaying page |
| 2 | Tiered Rewards Bar | `upcart-rewards`/`rewards-tier`/`free-shipping-bar`/`shipping-progress` in HTML; progress bar in screenshot |
| 3 | Cart Upsells / Recommendations | `upcart-upsell`/`aftersell-recommendations`/`upsell-widget` in HTML; product cards in drawer OR /cart |
| 4 | Shipping Protection Add-On | `upcart-shipping-protection`/`shipping-protection` in HTML; checkbox in cart footer |
| 5 | Product Add-On (toggle) | `upcart-addon`/`cart-addon` in HTML; toggle in cart footer |
| 6 | Announcements / Countdown Timer | `upcart-announcement`/`cart-announcement` in HTML; banner in cart drawer |
| 7 | Trust Badges (cart) | `upcart-trust`/`trust-badge` in HTML; security badges in cart screenshot |
| 8 | Express Checkout Buttons | `.shopify-payment-button`/`apple-pay-button` in HTML; Shop Pay/Apple Pay/Google Pay in cart |
| 9 | PDP Upsell Widget | `aftersell-pdp`/`product-page-upsell` in HTML; upsell block below ATC button in screenshot |

#### Checkout (always in scope — Shopify Plus assumed)

| # | Feature | Key detection signals |
|---|---|---|
| 10 | Checkout Upsell | Product cards with Add buttons in order summary; Aftersell upsell extension in DOM |
| 11 | Checkout Trust Badges | Security/guarantee badge images in screenshot (not payment card icons) |
| 12 | Checkout Testimonials | Star ratings + review text in screenshot |
| 13 | Checkout Rewards Bar | Progress bar visible in checkout screenshot |
| 14 | Checkout Announcements | Banner at top of checkout screenshot |

See `references/integrations.md` for the full integration detection table.

---

## Step 4: Generate HTML Scorecard

Use `references/scorecard_template.py` as the base. Fill in all data variables and run inline:

```bash
python3 - << 'HEREDOC'
# Paste scorecard_template.py here with all {{PLACEHOLDER}} values replaced:
# STORE_NAME, STORE_URL, AUDIT_DATE
# UPCART_STATUS, AFTERSELL_STATUS, CHECKOUT_BLOCKED
# FEATURES (list of 14 feature dicts)
# COMPATIBLE_INTEGRATIONS, COMPETING_INTEGRATIONS
HEREDOC
```

Capture the output path from `OUTPUT:[path]`.

### Data Variable Reference

| Variable | Type | Values |
|---|---|---|
| `STORE_NAME` | str | e.g. `"Away Travel"` |
| `STORE_URL` | str | e.g. `"https://awaytravel.com"` |
| `AUDIT_DATE` | str | e.g. `"March 15, 2026"` |
| `UPCART_STATUS` | str | `"INSTALLED"` \| `"NOT DETECTED"` |
| `AFTERSELL_STATUS` | str | `"INSTALLED"` \| `"NOT DETECTED"` |
| `CHECKOUT_BLOCKED` | bool | `True` \| `False` |
| `FEATURES` | list | 14 feature dicts (see template) |
| `COMPATIBLE_INTEGRATIONS` | list | e.g. `["Klaviyo", "Okendo"]` |
| `COMPETING_INTEGRATIONS` | list | e.g. `["Rebuy"]` |

---

## Step 5: Open & Summarise

```bash
open [OUTPUT_PATH]
```

Print terminal summary:

```
Cart Audit Complete — [STORE_NAME]

Install:  Upcart [STATUS] · Aftersell [STATUS]
Gaps:     [X] missing · [Y] via other app · [Z] unverified

Top missing (HIGH confidence):
  ✗ [Feature] — [evidence]
  ✗ [Feature] — [evidence]

Competing apps: [list or none]
Compatible integrations: [list or none]

Scorecard: [PATH]
⚠ DRAFT — human review required
```

---

## Examples

### Example 1: Greenfield store (no Aftersell, no Upcart)

**User says:** `cart audit https://awaytravel.com`

**Actions:**
1. Crawl homepage → collect scripts → no aftersell/upcart found
2. Navigate PDP → ATC → DOM check finds no `cart-drawer` element → full-page /cart redirect
3. /cart page shows bare checkout button, no upsells, no express pay
4. Checkout loads → no Aftersell extension names in DOM → all checkout features evaluated from screenshots

**Result:** Scorecard shows 12 MISSING (HIGH), 2 ACTIVE_OTHER (native Shopify express pay, Xgen recommendations)

---

### Example 2: Store with cart drawer and competing apps

**User says:** `audit kitsch.com`

**Actions:**
1. Crawl homepage → no aftersell/upcart scripts → Klaviyo + Okendo + Rivo detected
2. ATC → DOM check returns `{"drawer_element": true, "drawer_visible": true, "drawer_class": "fixed inset-0 z-[1020] h-full cart-drawer"}`
3. Drawer HTML eval shows upsells + rewards bar → `upcart_elements: 0` → ACTIVE_OTHER (custom theme)
4. Checkout → DOM reveals `"appName":"Echo: Checkout Blocks & Bundle"` → trust badges = ACTIVE_OTHER; `"appName":"Order Editing"` → upsell = ACTIVE_OTHER

**Result:** 4 MISSING, 10 ACTIVE_OTHER — pure consolidation pitch (replace 2+ apps with Aftersell)

---

### Example 3: Aftersell partially installed

**User says:** `check aftersell features on ridge.com`

**Actions:**
1. No aftersell scripts on homepage; no upcart
2. Cart is bare — no drawer, no express pay, no upsells
3. Checkout → DOM search finds `"appName":"Aftersell by Rokt"` with trust badges + upsell + testimonials extensions

**Result:** Cart = all MISSING; Checkout trust badges = ACTIVE_AFTERSELL; Checkout upsell = ACTIVE_AFTERSELL (MEDIUM — registered but not visibly rendering)

---

## Troubleshooting

### Cookie / consent banner blocks crawl
**Cause:** Banner intercepts clicks and screenshots.
**Fix:** Use `browser-use state` to find the Accept button index, click it before Phase B.

### Variant required before ATC
**Cause:** Product requires color/size selection.
**Fix:** `browser-use state` shows selector — pick first available option, retry ATC.

### Checkout login wall
**Cause:** Store requires account to checkout.
**Fix:** Screenshot it, set `CHECKOUT_BLOCKED = True`, mark all checkout features UNVERIFIED.

### Cart drawer detected in DOM but screenshot is empty / popup in the way
**Cause:** A modal or marketing popup is covering the drawer.
**Fix:** Find the popup element and hide it: `document.querySelector('[class*="popup"],[id*="ps__widget"]').style.display = 'none'`, then re-screenshot.

### /cart URL redirects to homepage
**Cause:** Store uses cart drawer only — no traditional cart page.
**Fix:** This is fine. Open the cart via the cart icon button, evaluate from the drawer in Phase C.

### Bot detection / Cloudflare blocks page
**Cause:** Headless browser fingerprint detected.
**Fix:** Retry with `--browser real`. If still blocked, note in scorecard as UNVERIFIED for affected features.

### `python3` script raises SyntaxError
**Cause:** Unescaped quotes or f-string nesting in evidence strings.
**Fix:** Escape single quotes in evidence strings, or wrap strings in double quotes. Re-run.

### `browser-use` session unresponsive
**Cause:** Session hung from a previous run.
**Fix:** `browser-use server stop` then retry `browser-use --session cart-audit open URL`.

---

## Notes & Calibration

- **Cart drawer**: DOM check is the authoritative signal. Screenshot confirms visually. If DOM says drawer exists and is visible, it's PRESENT regardless of how sparse it looks.
- **Cart upsells**: Check drawer HTML eval in Phase C. Upsells inside the drawer count even if /cart page has none.
- **ACTIVE_OTHER vs MISSING**: Any feature that is visually present but not Aftersell/Upcart-powered = ACTIVE_OTHER. Name the app.
- **LOW confidence**: Use when feature could plausibly exist but wasn't triggered (e.g., rewards bar only shows above $50 cart value, tested at $20).
- **Checkout extensions**: Search for `appName` in the checkout DOM to identify which apps are powering each checkout feature. This often reveals Aftersell even when no storefront scripts exist.
- **Integration scan**: Combine scripts from all phases. Cart page typically has the most loaded. See `references/integrations.md` for all patterns.
