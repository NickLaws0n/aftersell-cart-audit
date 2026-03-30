# Cart Audit — Curl Pre-flight Refactor

## Context

The cart-audit skill uses browser-use for all data collection, including passive tasks (script detection, integration scanning, product URL discovery) that don't require JS or a browser session. This creates unnecessary fragility (bot detection risk), latency (~20-30s of avoidable navigation), and cost per audit. Shopify app embed blocks are server-rendered: every installed storefront app's `<script src>` is present in the first HTTP response. Curl captures this more reliably than browser DOM eval, with no bot risk, in ~200ms.

## Principles

1. Curl first, browser only when JS interaction or visual confirmation is genuinely required.
2. Install signals from curl are authoritative — don't re-check in browser.
3. Integration scan runs before the browser opens — no Phase F.
4. Feature confidence is derived from the combination of curl signals + browser confirmation, not browser alone.

## Design

### New Step 2: Curl Pre-flight (before any browser)

Three curl requests, run in sequence:

```bash
# 1. Homepage — install signals + integration scripts + CSP header
curl -s -A "Mozilla/5.0" -D /tmp/cart_audit_home_headers.txt "STORE_URL" -o /tmp/cart_audit_home.html

# 2. Cart page — secondary script coverage + CSP header
curl -s -A "Mozilla/5.0" -D /tmp/cart_audit_cart_headers.txt "STORE_URL/cart" -o /tmp/cart_audit_cart.html

# 3. Product discovery
curl -s "STORE_URL/products.json?limit=1" -o /tmp/cart_audit_products.json
```

Then parse:

```bash
python3 - << 'HEREDOC'
import re, json

home = open('/tmp/cart_audit_home.html').read()
cart = open('/tmp/cart_audit_cart.html').read()
home_headers = open('/tmp/cart_audit_home_headers.txt').read()
products = json.load(open('/tmp/cart_audit_products.json'))

# Script src tags from HTML
html_scripts = '\n'.join(re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', home + cart, re.I))

# CSP header script-src domains (catches lazy-loaded app scripts)
csp_match = re.search(r'content-security-policy:([^\r\n]+)', home_headers, re.I)
csp_scripts = csp_match.group(1) if csp_match else ''

all_scripts = html_scripts + '\n' + csp_scripts

# Install detection
aftersell = bool(re.search(r'aftersell|AftersellApp|cdn\.aftersell\.com', all_scripts, re.I))
upcart = bool(re.search(r'upcart|UpCart|cdn\.upcart\.com', all_scripts, re.I))

# Express checkout (container in /cart static HTML)
express_checkout = bool(re.search(r'data-shopify=["\']payment-button["\']', cart))

# Integration scan
integrations = {
    'Rebuy':         bool(re.search(r'rebuyengine\.com', all_scripts)),
    'Klaviyo':       bool(re.search(r'klaviyo\.com|klaviyo\.js', all_scripts)),
    'Okendo':        bool(re.search(r'okendo\.io', all_scripts)),
    'Yotpo':         bool(re.search(r'yotpo\.com', all_scripts)),
    'Attentive':     bool(re.search(r'attn\.tv', all_scripts)),
    'Recharge':      bool(re.search(r'recharge\.com|rechargeapps\.com', all_scripts)),
    'Stay.ai':       bool(re.search(r'stay\.ai', all_scripts)),
    'Skio':          bool(re.search(r'skio\.com', all_scripts)),
    'Rivo':          bool(re.search(r'rivo\.io', all_scripts)),
    'Nosto':         bool(re.search(r'nosto\.com', all_scripts)),
    'Bold':          bool(re.search(r'boldapps\.net', all_scripts)),
    'Inveterate':    bool(re.search(r'inveterate\.com', all_scripts)),
    'LoyaltyLion':   bool(re.search(r'loyaltylion\.net', all_scripts)),
    'Rise AI':       bool(re.search(r'rise-ai\.com', all_scripts)),
    'ReConvert':     bool(re.search(r'reconvert\.com|store_reconvert\.js', all_scripts)),
    'Zipify':        bool(re.search(r'zipify\.com', all_scripts)),
    'CartHook':      bool(re.search(r'carthook\.com', all_scripts)),
    'Monster Cart':  bool(re.search(r'monstercart\.io', all_scripts)),
    'Slide Cart':    bool(re.search(r'slide-cart\.app', all_scripts)),
}

# Product discovery
p = products['products'][0] if products.get('products') else None
product_url = f"STORE_URL/products/{p['handle']}" if p else None
variant_id = p['variants'][0]['id'] if p else None

print(json.dumps({
    'aftersell_installed': aftersell,
    'upcart_installed': upcart,
    'express_checkout_present': express_checkout,
    'integrations': integrations,
    'product_url': product_url,
    'variant_id': variant_id,
}, indent=2))
HEREDOC
```

### Pre-flight Outputs → Feature Pre-population

| Curl finding | Feature impact |
|---|---|
| `aftersell_installed: true` | AFTERSELL_STATUS = "INSTALLED" (HIGH) |
| `upcart_installed: true` | UPCART_STATUS = "INSTALLED" (HIGH); Feature #1 Cart Drawer = ACTIVE_AFTERSELL MEDIUM |
| `express_checkout_present: true` | Feature #8 = ACTIVE_OTHER (MEDIUM) — no browser step needed |
| Integration app detected | Pre-populate competing/compatible lists |
| `product_url` | Use directly in Phase B — skip /collections/all navigation |

### Browser Phases (Simplified)

**Phase A: ELIMINATED** — install signals now from curl.

**Phase B (PDP):** Navigate directly to `product_url` from curl. No more /collections/all visual click pattern. Check PDP upsell.

**Phase C (ATC + Drawer):** Unchanged. Click ATC, DOM check for drawer, read drawer contents.

**Phase D (/cart screenshots):** Navigate /cart for screenshots. Skip script collection (already done via curl). Focus on layout features.

**Phase E (Checkout):** Unchanged.

**Phase F: ELIMINATED** — integration scan complete from curl pre-flight.

### Confidence Logic Changes

- **Install detection**: Curl script match → HIGH. No browser re-check.
- **Cart Drawer** (if Upcart installed from curl): Start at ACTIVE_AFTERSELL MEDIUM. Browser DOM check upgrades to HIGH if drawer visible, downgrades to MISSING LOW if not found.
- **Express Checkout**: Curl container present → ACTIVE at MEDIUM. Skip browser step entirely.
- **All other features**: Browser-only, confidence logic unchanged.

## Alternatives Considered

**Curl-only for everything**: Not feasible. Cart drawer contents, all Upcart widgets, PDP upsells, and all 5 checkout features require JS execution or session state. Cannot curl these.

**Curl product discovery only**: Too conservative. Misses the much larger win of eliminating Phase A and Phase F entirely.

## Open Questions

- **Aftersell-specific feature inference**: If Aftersell is confirmed installed via curl, should we pre-populate checkout feature likelihood? (e.g., "Aftersell installed → checkout upsell probably active") — Risky, could over-claim. Not included in this design.
- **Curl failure handling**: What if the store returns a Cloudflare challenge page to curl? The pre-flight should detect this (no `<script src>` tags found, or challenge page HTML detected) and fall through to browser-only mode.

## Validation Plan

1. Run curl pre-flight against 3-5 known stores (one with Upcart, one with Rebuy, one with Aftersell) and verify script detection matches expected.
2. Compare integration scan results between curl pre-flight and current Phase F browser eval — they should match or curl should be a superset.
3. Measure wall-clock time savings per audit with the new pre-flight step.

## Implementation Plan

1. Update SKILL.md: add Step 2 (Curl Pre-flight) before Step 2 (Browser Crawl), renumber steps
2. Add pre-flight python parsing block to SKILL.md
3. Update Phase A instructions: mark ELIMINATED, link to curl step
4. Update Phase B: replace /collections/all navigation with direct product URL from curl
5. Update Phase D: remove script collection eval (already done), keep screenshots
6. Update Phase F: mark ELIMINATED, replace with "integration scan complete from pre-flight"
7. Update Feature Evaluation section: add curl-derived confidence logic for install, cart drawer, express checkout
