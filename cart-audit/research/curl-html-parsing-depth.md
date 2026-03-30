# Curl HTML Parsing Depth — How Deep Can We Go?

## The Core Mechanism: App Embed Blocks

Shopify's app embed blocks are the standard installation mechanism for storefront-facing apps. When an app uses an app embed block:

1. The merchant enables it in theme settings
2. Shopify Liquid renders it server-side
3. The resulting `<script src="...">` tag is **injected before `</head>` or `</body>`** in the final HTML
4. This tag is present in the **first HTTP response** — no JS execution needed

This means any app that uses an app embed block is **curl-detectable via its script src URL**.

Apps that are backend-only (webhooks, order editing, etc.) will NOT appear in page HTML.

## Confirmed Script Patterns

### Aftersell / Upcart
- Aftersell CDN: `cdn.aftersell.com`
- Upcart CDN: `cdn.upcart.com`
- Also matches: `AftersellApp`, `UpCart` in src
- Also detectable: `window.aftersell` global or inline JS config blocks in `<script>` (no src)

### Rebuy
```
https://cdn.rebuyengine.com/onsite/js/rebuy.js?shop={store-domain}
```
Highly distinctive, detectable via `rebuyengine.com` domain.

### Klaviyo
```
https://static.klaviyo.com/onsite/js/klaviyo.js?company_id={id}
```
Or: `klaviyo.js` anywhere in the src. Very consistent pattern.

### Yotpo
```
https://staticw2.yotpo.com/{app-key}/widget.js
```
Pattern: `staticw2.yotpo.com` or `yotpo.com`

### Recharge
```
https://rechargeassets-bootstrapheroes-rechargeapps.netdna-ssl.com/...
```
Or: `recharge.com`, `rechargeapps.com`, `rechargepayments.com`

### ReConvert
Pattern: `store_reconvert.js` or `reconvert.com`

### Attentive
Pattern: `attn.tv` (their CDN domain)

### Others (Okendo, Stay.ai, Skio, etc.)
All use their brand domain in script src — detectable by matching on the domain name.

## Bonus Signal: Content-Security-Policy Header

Most Shopify stores emit a `Content-Security-Policy` header listing all allowed `script-src` domains. This exposes app CDNs even when scripts are lazy-loaded after the initial HTML response:

```bash
curl -sI "https://STORE_URL" | grep -i content-security-policy | tr ';' '\n' | grep script-src
```

This is the most comprehensive app detection signal available via curl — it catches apps that dynamically inject their scripts post-load, which wouldn't appear in the HTML `<script>` tags. Run this on every curl request as a supplemental signal.

---

## What Curl Gives You That Browser-Use Doesn't (Signal Quality Comparison)

| Signal | Curl | Browser-use `eval` |
|---|---|---|
| All script tags in page | ✅ Complete — every tag in initial HTML | ⚠️ Only `document.querySelectorAll('script[src]')` — misses dynamically added scripts or scripts removed from DOM |
| Script tags loaded after JS runs | ❌ Misses dynamically imported scripts | ✅ Captures these |
| Inline `<script>` block contents | ✅ Full text available for grep | ⚠️ Must eval specific patterns |
| Speed | ⚡ ~100-300ms per page | 🐢 2-5s+ per page load |
| Bot detection risk | ✅ None — looks like normal HTTP | ❌ Headless fingerprint risk |
| Session dependency | ✅ None | ❌ Requires active browser session |

**Key insight**: For script src detection, curl actually provides MORE reliable signal than browser-use DOM eval, because `querySelectorAll('script[src]')` only captures scripts present in the DOM at eval time. Scripts removed after execution, or added then removed, may be missed. `curl | grep` on raw HTML catches everything that was in the initial payload.

## What Curl CANNOT Tell You

1. **Whether a feature is enabled**: Script present ≠ feature active. Upcart may be installed but cart drawer disabled. Aftersell may be installed but rewards bar not configured.
2. **Cart drawer contents**: These are JS-injected. Not in static HTML.
3. **Any widget rendered by Aftersell/Upcart**: All their UI is client-side rendered.
4. **Checkout extension features**: Shopify checkout uses Remote DOM — no standard HTML, nothing detectable via curl.
5. **Dynamic scripts**: Some apps use `document.createElement('script')` to lazy-load. These won't be in the curl response.
6. **Session-dependent content**: Personalization, geo-gating, cart-state-dependent features.

## App Installed vs. Feature Active

This is the most important distinction for confidence scoring:

| Signal | Meaning | Confidence |
|---|---|---|
| Script src in curl HTML | App is **installed and enabled** in the theme | HIGH for app presence |
| Script src present + no competing app | Feature is **likely active** (not just installed) | MEDIUM |
| DOM element with app class (from browser) | Feature is **rendering** | HIGH for feature active |
| Screenshot shows feature visually | Feature is **rendering and visible** | HIGH |

For Aftersell/Upcart specifically: script src presence is strong evidence the app is actively installed (merchants rarely leave disabled apps in theme). But a specific feature (e.g., rewards bar) may be off even if the app is on.

## Multi-Page Curl Strategy

Different scripts appear on different pages. Recommended page order for script collection:

1. **Homepage** (`/`) — app embed blocks, marketing apps (Klaviyo, Attentive)
2. **Cart page** (`/cart`) — cart-specific apps (Upcart, Rebuy cart widget, express checkout)
3. **Product page** (`/products/{handle}`) — PDP-specific apps (Aftersell PDP, Yotpo reviews)

Most apps load on all pages via app embed. Collecting from homepage + cart covers ~95% of integration signals.

## Sources
- [Shopify App Embed Block Configuration](https://shopify.dev/docs/apps/build/online-store/theme-app-extensions/configuration)
- [Rebuy Manual Installation](https://developers.rebuyengine.com/reference/manual-installation)
- [FeraCommerce Shopify App Detector](https://github.com/feracommerce/shopify_app_detector)
- [Nozzlegear: Developer Guide to Shopify Script Tags](https://nozzlegear.com/shopify/the-developers-guide-to-shopify-script-tags)
