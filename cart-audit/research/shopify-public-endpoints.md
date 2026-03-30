# Shopify Public Endpoints — No Auth Required

All endpoints below are accessible via plain curl on any public Shopify store. No API key, token, or session required unless noted.

## Ajax API (JSON endpoints)

| Endpoint | Method | Returns | Notes |
|---|---|---|---|
| `/products.json` | GET | Array of all products (paginated) | `?limit=250` for max per page; `?page=N` for pagination |
| `/products/{handle}.js` | GET | Full product object (id, title, variants, images, price, tags) | Max 250 variants |
| `/collections/{handle}/products.json` | GET | Products in a collection | `?limit=250` supported |
| `/collections/all/products.json` | GET | All products via "all" collection | Most reliable for product discovery |
| `/cart.js` | GET | Current session cart contents | Session-scoped — empty for a fresh curl without cookies |
| `/cart/counts.json` | GET | `{"count": N}` item count | |
| `/search/suggest.json?q={term}&resources[type]=product` | GET | Product search suggestions | |
| `/pages/{handle}.json` | GET | Page content | |
| `/meta.json` | GET | Store metadata (theme name, currency, country) | Does NOT reveal installed apps |
| `/browsing_context_suggestions.json` | GET | Geolocation / currency redirect suggestions | |
| `/sitemap.xml` | GET | Links to all product/collection/page sitemaps | |
| `/sitemap_products_1.xml` | GET | All product URLs | Useful for finding a valid product handle |
| `/variants/{variant-id}` | GET | Redirect to product page for that variant | |

## Key Limitations

- **`/cart.js` is session-scoped**: A fresh curl (no cookies) returns an empty cart. It cannot be used to inspect a store's cart features without a browser session.
- **`/meta.json` does NOT list installed apps**: It returns store-level metadata (currency, language, theme name) but not app configuration.
- **No endpoint reveals checkout extensions**: Shopify's checkout extension API is admin-only. There is no public endpoint to enumerate installed checkout apps.
- **Rate limits**: No hard limits on Ajax API, but Shopify's abuse prevention applies at scale.

## Practical Use for Cart Audit

### Product discovery (replaces Phase B visual navigation)
```bash
curl -s "https://STORE_URL/products.json?limit=1" | python3 -c "
import json, sys
p = json.load(sys.stdin)['products'][0]
print(f'Handle: {p[\"handle\"]}')
print(f'Title: {p[\"title\"]}')
print(f'Variant ID: {p[\"variants\"][0][\"id\"]}')
print(f'Available: {p[\"variants\"][0][\"available\"]}')
"
```

### Sitemap for product URL
```bash
curl -s "https://STORE_URL/sitemap_products_1.xml" | grep -o '<loc>[^<]*</loc>' | head -5
```

## Sources
- [Shopify Ajax API](https://shopify.dev/docs/api/ajax)
- [Shopify Ajax Product API Reference](https://shopify.dev/docs/api/ajax/reference/product)
- [haroldao/shopify-url-parameters-and-endpoints](https://github.com/haroldao/shopify-url-parameters-and-endpoints)
