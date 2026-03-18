# Integration Reference

Scan all collected script srcs from all crawl phases. Match against patterns below.

## Aftersell-Compatible Integrations

Report each as DETECTED / NOT DETECTED. If DETECTED, include in `COMPATIBLE_INTEGRATIONS` list.

| App | Script pattern | Why it matters |
|---|---|---|
| Yotpo | `yotpo.com`, `staticw2.yotpo.com` | Aftersell shows Yotpo reviews on upsells |
| Okendo | `okendo.io` | Aftersell shows Okendo reviews on upsells |
| Junip | `junip.co` | Aftersell shows Junip reviews on upsells |
| Nosto | `nosto.com`, `connect.nosto.com` | Powers Aftersell product recommendations |
| Stay.ai | `stay.ai` | Subscription upsell integration |
| Skio | `skio.com` | Subscription upsell integration |
| Recharge | `recharge.com`, `rechargepayments.com` | Subscription platform — compatible |
| Inveterate | `inveterate.com` | Membership upsell integration |
| Rivo | `rivo.io` | Loyalty/membership — compatible |
| LoyaltyLion | `loyaltylion.net` | Loyalty — Aftersell integrates with it |
| Rise AI | `rise-ai.com` | Rewards/store credit — Aftersell integrates with it |
| Klaviyo | `klaviyo.com` | Email/SMS — retention relevance |
| Attentive | `attn.tv` | SMS platform |
| Bold Subscriptions | `boldapps.net` | Subscription platform |

## Competing / Conflicting Apps

Report each as DETECTED / NOT DETECTED. If DETECTED, include in `COMPETING_INTEGRATIONS` list.

When a competing app is detected AND the corresponding feature is visually present → status = `ACTIVE_OTHER`. Include the app name in evidence: `"Feature active via [App Name] — consolidation opportunity"`.

| App | Script pattern | Competes with |
|---|---|---|
| Rebuy | `rebuyengine.com` | Cart drawer, PDP upsells, cart upsells, checkout upsells |
| ReConvert | `reconvert.com` | Post-purchase, thank you page |
| Zipify | `zipify.com` | PDP upsells, post-purchase |
| CartHook | `carthook.com` | Post-purchase, checkout |
| Bold Upsell | `boldapps.net` | PDP/cart upsells (separate from Bold Subscriptions) |
| Monster Cart | `monstercart.io` | Cart drawer |
| Slide Cart | `slide-cart.app` | Cart drawer |

## Detection Script

Run on cart page (most scripts loaded). Combine with homepage scripts collected in Phase A.

```bash
browser-use --session cart-audit eval "Array.from(document.querySelectorAll('script[src]')).map(s=>s.src).join('
')"
```

Scan the output string against each pattern above.
