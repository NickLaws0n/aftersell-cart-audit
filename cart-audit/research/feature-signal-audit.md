# Feature Signal Audit — Curl vs. Browser Detection

For each of the 14 features, this file documents:
- Whether the detection signal is present in **static server-rendered HTML** (curl-accessible)
- The recommended detection method
- Confidence level per method

## Critical Background: How Shopify App Scripts Get into the Page

**App embed blocks (theme app extensions)** are the primary installation mechanism for storefront apps like Upcart, Aftersell, Rebuy, Klaviyo, etc. Shopify **server-renders and injects** these blocks before the closing `</head>` and `</body>` tags. This means:

✅ The `<script src="cdn.example.com/app.js">` tag IS in the static HTML returned by curl
✅ Script src patterns are reliable curl-detectable signals
❌ The **DOM elements created by those scripts** (drawers, widgets, upsell cards) are NOT in static HTML — they are injected after JS executes

**Checkout extensions** use Shopify's Remote DOM (not standard HTML). They do not add anything to the static checkout page HTML. Cannot be detected via curl.

---

## Feature Table

| # | Feature | Signal in Static HTML? | Curl Confidence | Browser Required? | Recommended Method |
|---|---|---|---|---|---|
| **Install** | Aftersell installed | ✅ Script src in `<head>`/`<body>` | HIGH | No | CURL_ONLY |
| **Install** | Upcart installed | ✅ Script src in `<head>`/`<body>` | HIGH | No | CURL_ONLY |
| 1 | Cart Drawer | ⚠️ Partial — theme-native drawer classes may be in HTML, but Upcart's drawer is JS-injected | LOW-MEDIUM | Yes (for reliable detection) | CURL_PRIMARY + BROWSER_CONFIRM |
| 2 | Tiered Rewards Bar | ❌ JS-injected by Upcart after load | NONE | Yes | BROWSER_ONLY |
| 3 | Cart Upsells / Recommendations | ❌ JS-injected | NONE | Yes | BROWSER_ONLY |
| 4 | Shipping Protection Add-On | ❌ JS-injected | NONE | Yes | BROWSER_ONLY |
| 5 | Product Add-On (toggle) | ❌ JS-injected | NONE | Yes | BROWSER_ONLY |
| 6 | Announcements / Countdown Timer | ❌ JS-injected | NONE | Yes | BROWSER_ONLY |
| 7 | Trust Badges (cart) | ❌ JS-injected | NONE | Yes | BROWSER_ONLY |
| 8 | Express Checkout Buttons | ✅ `<div data-shopify="payment-button">` in static HTML via Liquid `payment_button` filter | MEDIUM | No for presence; Yes for type | CURL_PRIMARY |
| 9 | PDP Upsell Widget | ❌ Aftersell widget is JS-injected post-load | NONE | Yes | BROWSER_ONLY |
| 10 | Checkout Upsell | ❌ Remote DOM, not in static HTML | NONE | Yes | BROWSER_ONLY |
| 11 | Checkout Trust Badges | ❌ Remote DOM | NONE | Yes | BROWSER_ONLY |
| 12 | Checkout Testimonials | ❌ Remote DOM | NONE | Yes | BROWSER_ONLY |
| 13 | Checkout Rewards Bar | ❌ Remote DOM | NONE | Yes | BROWSER_ONLY |
| 14 | Checkout Announcements | ❌ Remote DOM | NONE | Yes | BROWSER_ONLY |

---

## Integration Scan — Fully Curl-Detectable

All app detection that relies on script src patterns is **fully detectable from static HTML**. This is exactly how Wappalyzer and BuiltWith work.

| App | Script Pattern | Curl Detectable? |
|---|---|---|
| Aftersell | `aftersell`, `AftersellApp` | ✅ YES |
| Upcart | `upcart`, `UpCart` | ✅ YES |
| Rebuy | `cdn.rebuyengine.com/onsite/js/rebuy.js` | ✅ YES |
| Klaviyo | `klaviyo.com`, `klaviyo.js`, `static.klaviyo.com` | ✅ YES |
| Okendo | `okendo.io` | ✅ YES |
| Yotpo | `staticw2.yotpo.com`, `yotpo.com` | ✅ YES |
| Attentive | `attn.tv` | ✅ YES |
| Recharge | `recharge.com`, `rechargepayments.com`, `rechargeapps.com` | ✅ YES |
| ReConvert | `store_reconvert.js`, `reconvert.com` | ✅ YES |
| Monster Cart | `monstercart.io` | ✅ YES |
| Slide Cart | `slide-cart.app` | ✅ YES |
| Stay.ai | `stay.ai` | ✅ YES |
| Skio | `skio.com` | ✅ YES |
| Rivo | `rivo.io` | ✅ YES |
| Nosto | `nosto.com`, `connect.nosto.com` | ✅ YES |
| Bold | `boldapps.net` | ✅ YES |
| Inveterate | `inveterate.com` | ✅ YES |
| LoyaltyLion | `loyaltylion.net` | ✅ YES |
| Rise AI | `rise-ai.com` | ✅ YES |
| Zipify | `zipify.com` | ✅ YES |
| CartHook | `carthook.com` | ✅ YES |

---

## Cart Drawer — Special Case

The cart drawer detection is the most nuanced:

- **Theme-native drawers**: Some themes (Dawn, etc.) include a cart drawer in their `theme.liquid`. In this case, the HTML structure (with class names like `cart-drawer`, `CartDrawer`) IS present in the server-rendered HTML and IS curl-detectable.
- **Upcart's drawer**: Upcart replaces the native theme drawer. The Upcart script tag is in static HTML, but the actual drawer HTML is injected by JS. Curl can confirm Upcart is installed (HIGH), but cannot confirm the drawer is visible/active.
- **Recommendation**: Curl for "Upcart/Aftersell installed → likely has a cart drawer" inference, plus browser DOM check to confirm drawer is visible.

## Express Checkout Buttons — Special Case

- The `<div data-shopify="payment-button">` container is rendered by Liquid (`{{ form | payment_button }}`), so it IS in the static HTML of the /cart page.
- However, the actual buttons (Shop Pay, Apple Pay, Google Pay) are loaded inside a **closed shadow DOM** — their type is not visible in static HTML.
- **Recommendation**: Curl to confirm express checkout container is present (HIGH confidence it's enabled), browser to confirm which payment methods are shown.

---

## Summary

**Move to curl:** Install detection + full integration scan + product discovery + express checkout presence
**Keep in browser:** Cart drawer contents, all cart widgets (rewards, upsells, etc.), PDP upsell, checkout features

**Net impact**: ~35-40% of current browser-use steps become curl steps, with higher signal confidence.
