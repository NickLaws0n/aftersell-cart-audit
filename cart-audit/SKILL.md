---
name: cart-audit
description: Audits a Shopify Plus merchant's cart and checkout flow using curl pre-flight (install detection, integration scan, product discovery) followed by targeted browser-use (cart drawer, PDP upsell, checkout features). Evaluates 14 Aftersell/Upcart features with four-state status (ACTIVE_AFTERSELL, ACTIVE_OTHER, MISSING, UNVERIFIED), detects integrations and competing apps, and generates a self-contained HTML scorecard. Use when user says "cart audit", "/cart-audit [url]", "audit [store]", or "check aftersell features on [store]". Do NOT use for competitor A/B analysis (use competitor-ab-audit instead).
allowed-tools: Bash(browser-use:*), Bash(python3:*), Bash(curl:*)
compatibility: Requires browser-use CLI and curl. Claude Code only.
metadata:
  version: 3.1.0
---

# Skill: /cart-audit

Audit a Shopify Plus merchant for Aftersell/Upcart feature gaps. Primary output: **what's missing and with what confidence** — gap list first, no revenue estimates. Intended for Aftersell partner managers preparing targeted client conversations.

**Architecture:** Curl pre-flight handles install detection, integration scan, product discovery, and express checkout detection (~1s, no bot risk). Browser-use handles only what requires JS interaction: cart drawer, drawer contents, PDP upsell, and checkout features.

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
- Always runs via inline `python3 - << 'HEREDOC'` using `scripts/scorecard_template.py` as the base

---

## Step 1: Gather Inputs

Parse the URL from the invocation: `/cart-audit https://storename.com`

- `STORE_URL` — strip trailing slash
- `STORE_NAME` — derive from domain: `storename.com` → `Storename`

Confirm before crawling:
> "Starting cart audit of [STORE_NAME]. Running curl pre-flight (install detection, integrations, product discovery), then browser crawl (PDP → cart → checkout), scoring 14 features, then building the scorecard."

---

## Step 2: Curl Pre-flight

Three curl requests that resolve install detection, integration scan, product discovery, and express checkout — before any browser opens. No bot risk, ~1 second total.

```bash
# 1. Homepage — install signals + integration scripts + CSP header
curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" -D /tmp/cart_audit_home_headers.txt "STORE_URL" -o /tmp/cart_audit_home.html

# 2. Cart page — secondary script coverage + express checkout detection
curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" "STORE_URL/cart" -o /tmp/cart_audit_cart.html

# 3. Product discovery (may be blocked on some stores)
curl -s "STORE_URL/products.json?limit=1" -o /tmp/cart_audit_products.json
```

Parse all signals:

```bash
python3 - << 'HEREDOC'
import re, json, html as html_lib

home = open('/tmp/cart_audit_home.html').read()
cart = open('/tmp/cart_audit_cart.html').read()
headers = open('/tmp/cart_audit_home_headers.txt').read()

try:
    products = json.load(open('/tmp/cart_audit_products.json'))
except (json.JSONDecodeError, Exception):
    products = {}

# Script src tags from HTML
html_scripts = '\n'.join(re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', home + cart, re.I))

# CSP header script-src domains (catches lazy-loaded app scripts)
csp_match = re.search(r'content-security-policy:([^\r\n]+)', headers, re.I)
csp_scripts = csp_match.group(1) if csp_match else ''

all_scripts = html_scripts + '\n' + csp_scripts

# === INSTALL DETECTION ===
aftersell = bool(re.search(r'aftersell|AftersellApp|cdn\.aftersell\.com', all_scripts, re.I))
upcart = bool(re.search(r'upcart|UpCart|cdn\.upcart\.com', all_scripts, re.I))

# === EXPRESS CHECKOUT (Feature #8) ===
express_checkout = bool(re.search(
    r'data-shopify=["\']dynamic-checkout-cart["\']|shopify-accelerated-checkout|additional-checkout-buttons',
    cart
))

# Payment methods (best-effort — wallet-configs attr not always present)
wallet_match = re.search(r'wallet-configs="([^"]+)"', cart)
payment_methods = []
if wallet_match:
    try:
        wallet_json = html_lib.unescape(wallet_match.group(1))
        wallets = json.loads(wallet_json)
        payment_methods = [w.get('name', '') for w in wallets]
    except:
        pass

# === INTEGRATION SCAN ===
compatible = {
    'Yotpo':       bool(re.search(r'yotpo\.com', all_scripts)),
    'Okendo':      bool(re.search(r'okendo\.io', all_scripts)),
    'Junip':       bool(re.search(r'junip\.co', all_scripts)),
    'Nosto':       bool(re.search(r'nosto\.com', all_scripts)),
    'Stay.ai':     bool(re.search(r'stay\.ai', all_scripts)),
    'Skio':        bool(re.search(r'skio\.com', all_scripts)),
    'Recharge':    bool(re.search(r'recharge\.com|rechargeapps\.com|rechargepayments\.com', all_scripts)),
    'Inveterate':  bool(re.search(r'inveterate\.com', all_scripts)),
    'Rivo':        bool(re.search(r'rivo\.io', all_scripts)),
    'Klaviyo':     bool(re.search(r'klaviyo\.com|klaviyo\.js', all_scripts)),
    'Attentive':   bool(re.search(r'attn\.tv', all_scripts)),
    'Bold Subs':   bool(re.search(r'boldapps\.net', all_scripts)),
}

competing = {
    'Rebuy':        bool(re.search(r'rebuyengine\.com', all_scripts)),
    'ReConvert':    bool(re.search(r'reconvert\.com|store_reconvert\.js', all_scripts)),
    'Zipify':       bool(re.search(r'zipify\.com', all_scripts)),
    'CartHook':     bool(re.search(r'carthook\.com', all_scripts)),
    'Bold Upsell':  bool(re.search(r'boldapps\.net', all_scripts)),
    'Monster Cart': bool(re.search(r'monstercart\.io', all_scripts)),
    'Slide Cart':   bool(re.search(r'slide-cart\.app', all_scripts)),
    'LoyaltyLion':  bool(re.search(r'loyaltylion\.net', all_scripts)),
    'Rise AI':      bool(re.search(r'rise-ai\.com', all_scripts)),
}

# === PRODUCT DISCOVERY ===
p = products.get('products', [None])[0] if products.get('products') else None
if p:
    product_url = f"STORE_URL/products/{p['handle']}"
    variant_id = p['variants'][0]['id']
else:
    # Fallback: parse product links from homepage HTML
    product_links = list(set(re.findall(r'href=["\'](/products/[a-z0-9-]+)["\'\?]', home)))
    product_url = f"STORE_URL{product_links[0]}" if product_links else None
    variant_id = None

# === OUTPUT ===
print(json.dumps({
    'aftersell_installed': aftersell,
    'upcart_installed': upcart,
    'express_checkout': express_checkout,
    'payment_methods': payment_methods,
    'compatible_integrations': [k for k, v in compatible.items() if v],
    'competing_integrations': [k for k, v in competing.items() if v],
    'product_url': product_url,
    'variant_id': variant_id,
}, indent=2))
HEREDOC
```

### Pre-flight Outputs

Save all outputs — they feed directly into feature evaluation and the scorecard:

| Finding | Action |
|---|---|
| `aftersell_installed: true` | Set `AFTERSELL_STATUS = "INSTALLED"` (HIGH confidence) |
| `upcart_installed: true` | Set `UPCART_STATUS = "INSTALLED"` (HIGH confidence); Feature #1 Cart Drawer = ACTIVE_AFTERSELL at MEDIUM (browser confirms) |
| `express_checkout: true` | Feature #8 = ACTIVE at MEDIUM confidence; if `payment_methods` available, note which ones |
| Compatible integrations | Pre-populate `COMPATIBLE_INTEGRATIONS` list |
| Competing integrations | Pre-populate `COMPETING_INTEGRATIONS` list; use to attribute ACTIVE_OTHER features |
| `product_url` | Use directly in Phase B — no /collections/all navigation needed |

### Pre-flight Failure Handling

If curl returns a Cloudflare challenge page (no `<script src>` tags, or HTML contains `cf-challenge`):
- **Fall through to browser-only mode** — open browser, run the old Phase A install detection and Phase F integration scan manually
- Note in scorecard: "Pre-flight blocked by bot protection, fell back to browser detection"

---

## Step 3: Browser Crawl

Session name: `cart-audit`. **Read every screenshot immediately after capture** — visual signals are faster than HTML parsing.

> **Phase A is handled by the curl pre-flight.** Install detection and integration scanning are complete before the browser opens. Do NOT re-run script collection in the browser unless pre-flight failed.

### Phase B: Navigate to Product Page & Check PDP Upsell

Navigate directly to the product URL from the pre-flight — no /collections/all visual click pattern needed:

```bash
browser-use --session cart-audit open PRODUCT_URL
browser-use --session cart-audit screenshot /tmp/cart_audit_pdp.png
```

Read screenshot immediately. Look for any upsell/recommendation block below the ATC button.

```bash
browser-use --session cart-audit eval "document.documentElement.innerHTML.includes('aftersell-pdp') || document.documentElement.innerHTML.includes('product-page-upsell') ? 'FOUND' : 'NOT_FOUND'"
```

If the pre-flight product URL is unavailable: fall back to `/collections/all` visual navigation.

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

### Phase D: Check /cart Page Layout

> **Script collection is handled by the curl pre-flight.** This phase is for visual feature detection only.

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

### Phase F: Integration Scan — COMPLETE

> **Integration scan is handled by the curl pre-flight.** `COMPATIBLE_INTEGRATIONS` and `COMPETING_INTEGRATIONS` are already populated. Do NOT re-run script collection in the browser. See `references/integrations.md` for the pattern reference.

### Phase G: Close Session

```bash
browser-use --session cart-audit close
```

---

## Step 4: Feature Evaluation

### Install Detection

Install detection is resolved by the **curl pre-flight** (Step 2). Script src matching on static HTML is the authoritative signal — it is more reliable than browser DOM eval because it captures every tag in the initial HTTP response with no bot risk.

**Aftersell INSTALLED if:** curl pre-flight finds script src matching `aftersell`, `AftersellApp`, or `cdn.aftersell.com`. Also detectable in checkout DOM: `"appName":"Aftersell` (browser-only, checkout phase).

**Upcart INSTALLED if:** curl pre-flight finds script src matching `upcart`, `UpCart`, or `cdn.upcart.com`.

**Note:** Aftersell can be checkout-only (no storefront script). If curl pre-flight does not detect Aftersell but checkout DOM contains `"appName":"Aftersell"`, set AFTERSELL_STATUS = "INSTALLED" at that point.

### Feature Status — Four States

| Status | Icon | Meaning | When to use |
|---|---|---|---|
| `ACTIVE_AFTERSELL` | ✓ green | Present, powered by Aftersell/Upcart | Feature visible + Aftersell/Upcart confirmed |
| `ACTIVE_OTHER` | ≠ blue | Present, powered by another app | Feature visible + no Aftersell/Upcart script |
| `MISSING` | ✗ red | Not detected | Feature checked, not found, detection reliable |
| `UNVERIFIED` | ⚠ amber | Could not check | Login wall, bot block only |

Evidence for `ACTIVE_OTHER`: `"Feature active via [App Name] — consolidation opportunity"`

### Confidence Levels

- **HIGH** — observed in screenshot AND confirmed in HTML/DOM, OR curl pre-flight script match (for install/integration detection)
- **MEDIUM** — one signal only (screenshot OR HTML), OR inferred from install signal (e.g., Upcart installed → cart drawer likely), OR curl pre-flight detects feature container (e.g., express checkout)
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
| 8 | Express Checkout Buttons | Curl pre-flight: `additional-checkout-buttons`/`shopify-accelerated-checkout`/`dynamic-checkout-cart` in /cart HTML; `wallet-configs` attr may list specific methods (Shop Pay, PayPal, Apple Pay) |
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

## Step 5: Generate HTML Scorecard

Use `scripts/scorecard_template.py` as the base. Fill in all data variables and run inline:

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

## Step 6: Open & Summarise

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
1. Curl pre-flight → no aftersell/upcart scripts → express checkout not detected → no competing apps → product URL found
2. Browser: navigate PDP → ATC → DOM check finds no `cart-drawer` element → full-page /cart redirect
3. /cart page shows bare checkout button, no upsells, no express pay
4. Checkout loads → no Aftersell extension names in DOM → all checkout features evaluated from screenshots

**Result:** Scorecard shows 12 MISSING (HIGH), 2 ACTIVE_OTHER (native Shopify express pay, Xgen recommendations)

---

### Example 2: Store with cart drawer and competing apps

**User says:** `audit kitsch.com`

**Actions:**
1. Curl pre-flight → no aftersell/upcart scripts → Klaviyo + Okendo detected → products.json blocked → product URL extracted from homepage HTML links
2. Browser: navigate to PDP → ATC → DOM check returns `{"drawer_element": true, "drawer_visible": true, "drawer_class": "fixed inset-0 z-[1020] h-full cart-drawer"}`
3. Drawer HTML eval shows upsells + rewards bar → `upcart_elements: 0` → ACTIVE_OTHER (custom theme)
4. Checkout → DOM reveals `"appName":"Echo: Checkout Blocks & Bundle"` → trust badges = ACTIVE_OTHER; `"appName":"Order Editing"` → upsell = ACTIVE_OTHER

**Result:** 4 MISSING, 10 ACTIVE_OTHER — pure consolidation pitch (replace 2+ apps with Aftersell)

---

### Example 3: Aftersell partially installed (checkout only)

**User says:** `check aftersell features on ridge.com`

**Actions:**
1. Curl pre-flight → no aftersell/upcart scripts on storefront (checkout-only install) → Klaviyo + Okendo detected → express checkout detected → product URL found
2. Browser: navigate to PDP → ATC → no cart drawer → /cart page is bare
3. Checkout → DOM search finds `"appName":"Aftersell by Rokt"` with trust badges + upsell + testimonials extensions → update AFTERSELL_STATUS = "INSTALLED"

**Result:** Cart = all MISSING; Checkout trust badges = ACTIVE_AFTERSELL; Checkout upsell = ACTIVE_AFTERSELL (MEDIUM — registered but not visibly rendering)

---

### Example 4: Upcart installed (curl pre-populates cart drawer)

**User says:** `cart audit https://gruns.co`

**Actions:**
1. Curl pre-flight → Upcart script detected (HIGH) → Klaviyo + Skio detected → express checkout detected (Shop Pay + PayPal) → product URL found
2. Pre-populate: UPCART_STATUS = "INSTALLED", Feature #1 Cart Drawer = ACTIVE_AFTERSELL at MEDIUM, Feature #8 Express Checkout = ACTIVE at MEDIUM
3. Browser: navigate to PDP → ATC → cart drawer opens → browser confirms drawer visible (upgrade to HIGH) → check drawer contents
4. Checkout → evaluate checkout features from screenshots + DOM

**Result:** Cart Drawer = ACTIVE_AFTERSELL (HIGH), Express Checkout = ACTIVE (MEDIUM), remaining features evaluated from browser

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

### Curl pre-flight returns Cloudflare challenge page
**Cause:** Store has aggressive bot protection that blocks curl.
**Fix:** Check if HTML contains `cf-challenge` or has no `<script src>` tags. Fall through to browser-only mode — run install detection and integration scan via browser `eval` as the old Phase A and Phase F would. Note in scorecard: "Pre-flight blocked by bot protection."

### Bot detection / Cloudflare blocks browser
**Cause:** Headless browser fingerprint detected.
**Fix:** Retry with `--browser real`. If still blocked, note in scorecard as UNVERIFIED for affected features.

### products.json blocked or empty
**Cause:** Some stores disable the public JSON API.
**Fix:** The pre-flight parser falls back to extracting `/products/` links from the homepage HTML. If that also fails, fall back to browser `/collections/all` navigation in Phase B.

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
- **Integration scan**: Resolved by curl pre-flight (Step 2). Homepage + /cart page HTML covers ~95% of installed app scripts. See `references/integrations.md` for all patterns.
