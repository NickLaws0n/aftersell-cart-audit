#!/usr/bin/env python3
"""
Cart Audit HTML Scorecard Generator
====================================
Do NOT run this file directly. Claude fills in the data variables
below and runs it inline via: python3 - << 'HEREDOC' ... HEREDOC

All {{PLACEHOLDER}} values must be replaced before execution.
"""
import base64, os
from datetime import datetime

# ── AUDIT DATA (fill these in before running) ─────────────────────────────────

STORE_NAME = "{{STORE_NAME}}"          # e.g. "Away Travel"
STORE_URL   = "{{STORE_URL}}"          # e.g. "https://awaytravel.com"
AUDIT_DATE  = "{{AUDIT_DATE}}"         # e.g. "March 15, 2026"

UPCART_STATUS    = "{{UPCART_STATUS}}"     # "INSTALLED" | "NOT DETECTED"
AFTERSELL_STATUS = "{{AFTERSELL_STATUS}}"  # "INSTALLED" | "NOT DETECTED"
CHECKOUT_BLOCKED = {{CHECKOUT_BLOCKED}}    # True | False

# Each feature dict:
# {
#   "name": str,
#   "category": "cart" | "pdp" | "checkout",
#   "status": "ACTIVE_AFTERSELL" | "ACTIVE_OTHER" | "MISSING" | "UNVERIFIED",
#   "confidence": "HIGH" | "MEDIUM" | "LOW" | None,
#   "evidence": str   — 1-line note; include app name if ACTIVE_OTHER
# }
FEATURES = {{FEATURES_JSON}}

COMPATIBLE_INTEGRATIONS = {{COMPATIBLE_JSON}}   # list of app name strings
COMPETING_INTEGRATIONS  = {{COMPETING_JSON}}    # list of app name strings

SCREENSHOTS = [
    ("/tmp/cart_audit_home1.png",     "Homepage"),
    ("/tmp/cart_audit_pdp.png",       "Product page"),
    ("/tmp/cart_audit_atc.png",       "After add to cart"),
    ("/tmp/cart_audit_cart1.png",     "Cart — above fold"),
    ("/tmp/cart_audit_cart2.png",     "Cart — scrolled"),
    ("/tmp/cart_audit_checkout1.png", "Checkout — above fold"),
    ("/tmp/cart_audit_checkout2.png", "Checkout — scrolled"),
]

# ── HELPERS ───────────────────────────────────────────────────────────────────

def embed_img(path):
    if path and os.path.exists(path):
        with open(path, 'rb') as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    return None

STATUS_META = {
    "ACTIVE_AFTERSELL": ("\u2713", "#22C55E"),
    "ACTIVE_OTHER":     ("\u2260", "#3B82F6"),
    "MISSING":          ("\u2717", "#EF4444"),
    "UNVERIFIED":       ("\u26a0", "#F59E0B"),
}
CONF_COLORS = {"HIGH": "#22C55E", "MEDIUM": "#F59E0B", "LOW": "#6B7280"}

def conf_badge(conf):
    if not conf: return ""
    c = CONF_COLORS.get(conf, "#6B7280")
    return f'<span style="background:{c}22;color:{c};padding:2px 7px;border-radius:99px;font-size:10px;font-weight:700;letter-spacing:.5px">{conf}</span>'

def feature_row(f, dimmed=False):
    icon, color = STATUS_META.get(f["status"], ("?", "#6B7280"))
    badge = conf_badge(f.get("confidence"))
    note = f.get("evidence", "")
    if f["status"] == "ACTIVE_OTHER":
        note = f'{note} <span style="color:#3B82F6;font-weight:600">\u2014 consolidation opportunity</span>'
    opacity = "opacity:0.55;" if dimmed else ""
    return f"""<div style="display:flex;align-items:center;gap:12px;padding:11px 18px;border-bottom:1px solid #1E1E1E;{opacity}">
  <span style="width:24px;height:24px;border-radius:50%;background:{color}22;color:{color};display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;flex-shrink:0">{icon}</span>
  <div style="flex:1;min-width:0">
    <span style="color:#FFFFFF;font-weight:600;font-size:13px">{f["name"]}</span>
    <span style="color:#555;font-size:11px;margin-left:10px">{note}</span>
  </div>
  <div style="flex-shrink:0">{badge}</div>
</div>"""

def install_chip(label, status):
    color = "#22C55E" if status == "INSTALLED" else "#444"
    return f'<span style="display:inline-flex;align-items:center;gap:5px;background:{color}18;color:{color};border:1px solid {color}30;padding:5px 12px;border-radius:6px;font-size:12px;font-weight:600"><span style="font-size:7px">\u25cf</span>{label}: {status}</span>'

def app_chip(name, color):
    return f'<span style="background:{color}18;color:{color};border:1px solid {color}30;padding:3px 10px;border-radius:99px;font-size:12px;font-weight:600">{name}</span>'

def section_divider(label):
    return f'<div style="padding:7px 18px;background:#141414;border-bottom:1px solid #1E1E1E"><span style="color:#444;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase">{label}</span></div>'

def screenshot_gallery():
    out = []
    for path, caption in SCREENSHOTS:
        data = embed_img(path)
        if data:
            out.append(f'<div style="background:#141414;border:1px solid #222;border-radius:6px;overflow:hidden;display:inline-block"><img src="{data}" style="width:190px;display:block" alt="{caption}"><div style="padding:5px 8px;color:#444;font-size:10px">{caption}</div></div>')
    return "\n".join(out)

# ── COMPUTE ───────────────────────────────────────────────────────────────────

STATUS_ORDER = {"MISSING": 0, "ACTIVE_OTHER": 1, "UNVERIFIED": 2, "ACTIVE_AFTERSELL": 3}
cart_features     = sorted([f for f in FEATURES if f["category"] in ("cart", "pdp")],
                            key=lambda f: STATUS_ORDER.get(f["status"], 9))
checkout_features = sorted([f for f in FEATURES if f["category"] == "checkout"],
                            key=lambda f: STATUS_ORDER.get(f["status"], 9))

n_missing    = sum(1 for f in FEATURES if f["status"] == "MISSING")
n_other      = sum(1 for f in FEATURES if f["status"] == "ACTIVE_OTHER")
n_unverified = sum(1 for f in FEATURES if f["status"] == "UNVERIFIED")
n_active     = sum(1 for f in FEATURES if f["status"] == "ACTIVE_AFTERSELL")

needs_verify = [f for f in FEATURES if f.get("confidence") in ("LOW", "MEDIUM") or f["status"] == "UNVERIFIED"]

VERIFY_HINTS = {
    "Tiered Rewards Bar":             "may only appear above a cart spend threshold",
    "Cart Upsells / Recommendations": "may require specific products/collections in cart",
    "Shipping Protection Add-On":     "may be product- or order-value-gated",
    "Product Add-On (toggle)":        "may require specific products in cart",
    "Announcements / Countdown Timer":"may be time-gated or A/B tested",
    "Trust Badges (cart)":            "may appear only at certain cart stages",
    "Express Checkout Buttons":       "may depend on browser payment method availability",
    "PDP Upsell Widget":              "may only appear on specific products/collections",
}

checklist_items = []
for f in needs_verify:
    conf = f.get("confidence") or "UNVERIFIED"
    hint = VERIFY_HINTS.get(f["name"], "verify manually in a real browser session")
    checklist_items.append(
        f'<li style="margin-bottom:7px">\u2610 <strong>{f["name"]}</strong> '
        f'<span style="color:#F59E0B">({conf})</span> \u2014 {hint}</li>'
    )
checklist_html = "\n".join(checklist_items) if checklist_items else \
    '<li style="color:#444">All detections were HIGH confidence.</li>'

blocked_note = (
    '<div style="padding:12px 18px;color:#F59E0B;font-size:12px;'
    'background:#F59E0B0A;border-bottom:1px solid #1E1E1E">'
    '\u26a0 Checkout was login-gated \u2014 features could not be verified</div>'
) if CHECKOUT_BLOCKED else ""

# Gap summary: only show non-zero counts
gap_stats = []
if n_missing:    gap_stats.append(f'<div><span style="font-size:30px;font-weight:800;color:#EF4444">{n_missing}</span><span style="color:#555;font-size:12px;margin-left:5px">missing</span></div>')
if n_other:      gap_stats.append(f'<div><span style="font-size:30px;font-weight:800;color:#3B82F6">{n_other}</span><span style="color:#555;font-size:12px;margin-left:5px">via other app</span></div>')
if n_unverified: gap_stats.append(f'<div><span style="font-size:30px;font-weight:800;color:#F59E0B">{n_unverified}</span><span style="color:#555;font-size:12px;margin-left:5px">unverified</span></div>')
if n_active:     gap_stats.append(f'<div><span style="font-size:30px;font-weight:800;color:#22C55E">{n_active}</span><span style="color:#555;font-size:12px;margin-left:5px">active via Aftersell</span></div>')

# ── HTML ──────────────────────────────────────────────────────────────────────

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cart Audit \u2014 {STORE_NAME}</title>
<style>
* {{ box-sizing:border-box;margin:0;padding:0 }}
body {{ background:#0F0F0F;color:#FFF;font-family:system-ui,-apple-system,sans-serif;font-size:14px;line-height:1.5 }}
.wrap {{ max-width:780px;margin:0 auto;padding:36px 24px }}
.card {{ background:#1A1A1A;border:1px solid #252525;border-radius:10px;overflow:hidden;margin-bottom:16px }}
.card-header {{ padding:12px 18px;border-bottom:1px solid #1E1E1E;display:flex;align-items:center;justify-content:space-between }}
.card-header h2 {{ font-size:13px;font-weight:700;color:#DDD;letter-spacing:.3px }}
</style>
</head>
<body>
<div class="wrap">

  <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px;padding-bottom:18px;border-bottom:1px solid #1E1E1E">
    <div>
      <div style="color:#FF6B35;font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px">AFTERSELL CART AUDIT</div>
      <div style="font-size:22px;font-weight:800">{STORE_NAME}</div>
      <div style="color:#444;font-size:12px;margin-top:2px">{STORE_URL}</div>
    </div>
    <div style="text-align:right">
      <div style="color:#444;font-size:11px;margin-bottom:6px">{AUDIT_DATE}</div>
      <div style="background:#F59E0B;color:#000;padding:4px 10px;border-radius:4px;font-size:10px;font-weight:800;letter-spacing:1px">\u26a0 DRAFT</div>
    </div>
  </div>

  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">
    {install_chip("Upcart", UPCART_STATUS)}
    {install_chip("Aftersell", AFTERSELL_STATUS)}
  </div>

  <div style="background:#FF6B350A;border:1px solid #FF6B3520;border-radius:10px;padding:16px 20px;margin-bottom:16px;display:flex;gap:28px;flex-wrap:wrap;align-items:baseline">
    {"".join(gap_stats)}
  </div>

  <div class="card">
    <div class="card-header"><h2>Features</h2><span style="color:#444;font-size:11px">{len(FEATURES)} checked</span></div>
    {section_divider("Cart & PDP")}
    {"".join(feature_row(f, dimmed=(f["status"] == "ACTIVE_AFTERSELL")) for f in cart_features)}
    {section_divider("Checkout")}
    {blocked_note}
    {"".join(feature_row(f, dimmed=(f["status"] == "ACTIVE_AFTERSELL")) for f in checkout_features)}
  </div>

  <div class="card">
    <div class="card-header"><h2>Integrations</h2></div>
    <div style="padding:12px 18px;border-bottom:1px solid #1E1E1E">
      <div style="color:#444;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:7px">Compatible with Aftersell</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px">{" ".join(app_chip(a, "#22C55E") for a in COMPATIBLE_INTEGRATIONS) if COMPATIBLE_INTEGRATIONS else '<span style="color:#444;font-size:12px">None detected</span>'}</div>
    </div>
    <div style="padding:12px 18px">
      <div style="color:#444;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:7px">Competing apps</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px">{" ".join(app_chip(a, "#F59E0B") for a in COMPETING_INTEGRATIONS) if COMPETING_INTEGRATIONS else '<span style="color:#444;font-size:12px">None detected</span>'}</div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><h2>Out of Scope</h2><span style="color:#444;font-size:11px">Requires live purchase</span></div>
    <div style="padding:12px 18px;color:#444;font-size:12px;display:flex;flex-direction:column;gap:6px">
      <div>\u2022 <strong style="color:#666">Post-Purchase Upsells</strong> \u2014 one-click upsells after order confirmation</div>
      <div>\u2022 <strong style="color:#666">Thank You Page Widgets</strong> \u2014 order confirmation page widgets</div>
      <div>\u2022 <strong style="color:#666">Rokt Thanks</strong> \u2014 third-party offer monetization on TY page</div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><h2>Verification Screenshots</h2></div>
    <div style="padding:12px 18px;display:flex;flex-wrap:wrap;gap:8px">{screenshot_gallery()}</div>
  </div>

  <div style="background:#F59E0B08;border:1px solid #F59E0B25;border-radius:10px;padding:18px">
    <div style="background:#F59E0B;color:#000;font-weight:800;font-size:10px;letter-spacing:1px;padding:6px 12px;border-radius:4px;text-align:center;margin-bottom:14px">\u26a0 HUMAN REVIEW REQUIRED \u2014 DRAFT</div>
    <div style="font-size:11px;font-weight:700;margin-bottom:9px;color:#888;text-transform:uppercase;letter-spacing:.5px">Before sharing:</div>
    <ul style="color:#555;font-size:12px;list-style:none;padding:0;display:flex;flex-direction:column">
      {checklist_html}
      <li style="margin-bottom:6px">\u2610 Aftersell/Upcart install confirmed via Shopify app store</li>
      <li style="margin-bottom:6px">\u2610 Store not in maintenance or preview mode during crawl</li>
      <li style="margin-bottom:6px">\u2610 Competing app detections spot-checked for false positives</li>
    </ul>
    <p style="color:#333;font-size:11px;margin-top:12px">Auto-generated via browser crawl. Not reviewed by an Aftersell account manager.</p>
  </div>

</div>
</body>
</html>"""

safe = STORE_NAME.lower().replace(" ", "_").replace(".", "_")
out  = f"/tmp/cart_audit_{safe}_{datetime.now().strftime('%Y%m%d')}.html"
open(out, "w").write(HTML)
print(f"OUTPUT:{out}")
