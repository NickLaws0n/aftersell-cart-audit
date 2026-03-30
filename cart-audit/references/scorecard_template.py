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

# ── FEATURE VALUE PROPOSITIONS ───────────────────────────────────────────────

FEATURE_DESCRIPTIONS = {
    "Cart Drawer": "Side-panel cart keeps shoppers on-page and increases add-on attachment",
    "Tiered Rewards Bar": "Progress incentives like free shipping thresholds encourage larger orders",
    "Cart Upsells / Recommendations": "Contextual product suggestions in the cart drive AOV lift",
    "Shipping Protection Add-On": "One-click shipping protection generates incremental margin",
    "Product Add-On (toggle)": "Simple toggle add-ons capture impulse purchases at the cart",
    "Announcements / Countdown Timer": "Urgency messaging and promotions reduce cart abandonment",
    "Trust Badges (cart)": "Security and guarantee badges reduce purchase anxiety",
    "Express Checkout Buttons": "Apple Pay, Shop Pay, and Google Pay reduce mobile checkout friction",
    "PDP Upsell Widget": "Product page cross-sells capture buying intent before the cart",
    "Checkout Upsell": "Last-chance product offers capture high-intent buyers at checkout",
    "Checkout Trust Badges": "Trust signals at payment reduce abandonment at the final step",
    "Checkout Testimonials": "Social proof in checkout reinforces purchase confidence",
    "Checkout Rewards Bar": "Progress incentives in checkout encourage order upgrades",
    "Checkout Announcements": "Targeted messaging at checkout drives promotion awareness",
}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def embed_img(path):
    if path and os.path.exists(path):
        with open(path, 'rb') as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    return None


def feature_active_row(f):
    status = f["status"]
    if status == "ACTIVE_AFTERSELL":
        source, tag_cls = "AFTERSELL", "tag-aftersell"
    elif status == "ACTIVE_OTHER":
        source, tag_cls = "OTHER APP", "tag-other"
    else:  # ACTIVE_NATIVE
        source, tag_cls = "THEME / NATIVE", "tag-native"
    note = f.get("evidence", "")
    consolidation = ""
    if status == "ACTIVE_OTHER":
        consolidation = '<span class="tag-mono tag-consolidation">CONSOLIDATION OPPORTUNITY</span>'
    return f"""<div class="feature-row">
  <div class="feature-check"><svg width="14" height="14" fill="none" viewBox="0 0 16 16"><path d="M13.3 4.3a1 1 0 010 1.4l-6 6a1 1 0 01-1.4 0l-3-3a1 1 0 111.4-1.4L6.6 9.6l5.3-5.3a1 1 0 011.4 0z" fill="currentColor"/></svg></div>
  <div class="feature-body">
    <div class="feature-top">
      <span class="feature-name">{f["name"]}</span>
      <span class="tag-mono {tag_cls}">{source}</span>
      {consolidation}
    </div>
    <div class="feature-evidence">{note}</div>
  </div>
</div>"""


def feature_opportunity_row(f):
    desc = FEATURE_DESCRIPTIONS.get(f["name"], "")
    if f["status"] == "UNVERIFIED":
        evidence = f.get("evidence", "requires manual check")
        return f"""<div class="opportunity-card unverified">
  <div class="opp-icon opp-icon-unverified">?</div>
  <div class="opp-content">
    <div class="opp-name">{f["name"]}</div>
    <div class="opp-desc">{desc}</div>
    <div class="opp-caveat">Could not verify \u2014 {evidence}</div>
  </div>
</div>"""
    return f"""<div class="opportunity-card">
  <div class="opp-content">
    <div class="opp-name">{f["name"]}</div>
    <div class="opp-desc">{desc}</div>
  </div>
</div>"""


def coverage_bar_html(active, total, label):
    pct = round(active / total * 100) if total else 0
    return f"""<div class="coverage">
  <div class="coverage-top">
    <span class="coverage-label">{label}</span>
    <span class="coverage-count">{active} of {total} active</span>
  </div>
  <div class="coverage-track"><div class="coverage-fill" style="width:{pct}%"></div></div>
</div>"""


def install_chip(label, status):
    cls = "chip-on" if status == "INSTALLED" else "chip-off"
    display = "Installed" if status == "INSTALLED" else "Not installed"
    return f'<div class="install-chip {cls}"><span class="install-chip-dot"></span><span class="install-chip-name">{label}</span><span class="install-chip-status">{display}</span></div>'


def app_chip(name, cls):
    return f'<span class="app-chip {cls}">{name}</span>'


def screenshot_gallery():
    out = []
    for i, (path, caption) in enumerate(SCREENSHOTS):
        data = embed_img(path)
        if data:
            out.append(f"""<label class="ss-thumb" for="lb-{i}">
  <img src="{data}" alt="{caption}"><span class="ss-cap">{caption}</span>
</label>
<input type="checkbox" id="lb-{i}" class="lb-toggle" aria-hidden="true">
<div class="lb-overlay"><label for="lb-{i}" class="lb-close">\u00d7</label>
  <img src="{data}" alt="{caption}"><div class="lb-caption">{caption}</div>
</div>""")
    return "\n".join(out)


# ── COMPUTE ───────────────────────────────────────────────────────────────────

cart_pdp_all = [f for f in FEATURES if f["category"] in ("cart", "pdp")]
checkout_all = [f for f in FEATURES if f["category"] == "checkout"]

ACTIVE_STATUSES = ("ACTIVE_AFTERSELL", "ACTIVE_OTHER", "ACTIVE_NATIVE")

cart_active    = [f for f in cart_pdp_all if f["status"] in ACTIVE_STATUSES]
cart_opps      = [f for f in cart_pdp_all if f["status"] in ("MISSING", "UNVERIFIED")]
checkout_active = [f for f in checkout_all if f["status"] in ACTIVE_STATUSES]
checkout_opps   = [f for f in checkout_all if f["status"] in ("MISSING", "UNVERIFIED")]

n_total       = len(FEATURES)
n_active_all  = len(cart_active) + len(checkout_active)
n_opps_all    = len(cart_opps) + len(checkout_opps)
n_aftersell   = sum(1 for f in FEATURES if f["status"] == "ACTIVE_AFTERSELL")
n_other       = sum(1 for f in FEATURES if f["status"] == "ACTIVE_OTHER")
n_native      = sum(1 for f in FEATURES if f["status"] == "ACTIVE_NATIVE")

needs_verify = [f for f in FEATURES if f.get("confidence") in ("LOW", "MEDIUM") or f["status"] == "UNVERIFIED"]

VERIFY_HINTS = {
    "Tiered Rewards Bar":             "add a low-value item and check if the progress bar appears — it may only show above a spend threshold",
    "Cart Upsells / Recommendations": "add a product from a different category and confirm no recommendation cards appear in the cart",
    "Shipping Protection Add-On":     "check cart with a high-value item — protection toggle may only appear above a certain order value",
    "Product Add-On (toggle)":        "confirm whether the add-on appears consistently across different products, or only for specific SKUs",
    "Announcements / Countdown Timer":"visit the cart at a different time or in an incognito session — may be time-gated or A/B tested",
    "Trust Badges (cart)":            "scroll the full cart page in a real browser session to confirm no badge widget is present",
    "Express Checkout Buttons":       "check in a real browser with Apple Pay or Google Pay enabled — button availability depends on the browser",
    "PDP Upsell Widget":              "visit 2–3 different product pages to confirm no recommendation block appears below the Add to Cart button",
}

checklist_items = []
for f in needs_verify:
    conf = f.get("confidence") or "UNVERIFIED"
    hint = VERIFY_HINTS.get(f["name"], "verify manually in a real browser session")
    checklist_items.append(f'<li><strong>{f["name"]}</strong> <span class="verify-tag">({conf})</span> \u2014 {hint}</li>')
checklist_html = "\n".join(checklist_items) if checklist_items else \
    '<li class="all-good">All detections were high confidence.</li>'

blocked_note = (
    '<div class="blocked-note">'
    'Checkout was login-gated \u2014 features could not be verified</div>'
) if CHECKOUT_BLOCKED else ""

# Build section HTML
cart_active_html = "".join(feature_active_row(f) for f in cart_active)
cart_opp_html    = "".join(feature_opportunity_row(f) for f in cart_opps)
checkout_active_html = "".join(feature_active_row(f) for f in checkout_active)
checkout_opp_html    = "".join(feature_opportunity_row(f) for f in checkout_opps)

# TLDR conclusion sentence
_n_not_aftersell = n_active_all - n_aftersell
_n_compat = len(COMPATIBLE_INTEGRATIONS)
_n_competing = len(COMPETING_INTEGRATIONS)

if AFTERSELL_STATUS == "NOT DETECTED" and _n_competing == 0:
    _pitch = "Strong opportunity"
    _body = f"{STORE_NAME} has {_n_not_aftersell} feature{'s' if _n_not_aftersell != 1 else ''} in place but none are powered by Aftersell, and {n_opps_all} remain untouched."
    if _n_compat:
        _body += f" With {_n_compat} compatible app{'s' if _n_compat != 1 else ''} already installed, this is a clean install with no disruption to the existing stack."
elif AFTERSELL_STATUS == "NOT DETECTED" and _n_competing > 0:
    _pitch = "Consolidation opportunity"
    _body = f"{_n_competing} competing app{'s' if _n_competing != 1 else ''} detected across {_n_not_aftersell} active feature{'s' if _n_not_aftersell != 1 else ''}. Replacing {'them' if _n_competing > 1 else 'it'} with Aftersell opens up {n_opps_all} additional {'opportunities' if n_opps_all != 1 else 'opportunity'}."
elif AFTERSELL_STATUS == "INSTALLED" and n_opps_all > 0:
    _pitch = "Expansion opportunity"
    _body = f"Aftersell is installed but {n_opps_all} feature{'s are' if n_opps_all != 1 else ' is'} not yet configured."
else:
    _pitch = "Full coverage"
    _body = "All audited features are active and powered by Aftersell."

tldr_conclusion = f"<strong>{_pitch}.</strong> {_body}"

# ── HTML ──────────────────────────────────────────────────────────────────────

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cart Audit \u2014 {STORE_NAME}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --brand-bg: #FFFFFF;
  --brand-surface: #FAFAFA;
  --brand-border: rgba(0,0,0,0.06);
  --brand-primary: #FF5F1F;
  --brand-muted: rgba(0,0,0,0.4);
  --brand-text: #18181B;
  --brand-heading: #09090B;
  --brand-evidence: rgba(113,113,122,0.65);
  --brand-subtle: rgba(0,0,0,0.55);
  --brand-faint: rgba(0,0,0,0.15);
  --brand-ghost: rgba(0,0,0,0.2);
  --brand-chip-on-border: rgba(0,0,0,0.12);
  --brand-tag-aftersell-border: rgba(255,95,31,0.2);
  --font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: "JetBrains Mono", "SF Mono", ui-monospace, Menlo, Monaco, Consolas, monospace;
}}

html.dark {{
  --brand-bg: #0C0C0C;
  --brand-surface: #141414;
  --brand-border: rgba(255,255,255,0.07);
  --brand-primary: #FF6D2E;
  --brand-muted: rgba(255,255,255,0.4);
  --brand-text: #E4E4E7;
  --brand-heading: #FAFAFA;
  --brand-evidence: rgba(161,161,170,0.6);
  --brand-subtle: rgba(255,255,255,0.5);
  --brand-faint: rgba(255,255,255,0.12);
  --brand-ghost: rgba(255,255,255,0.15);
  --brand-chip-on-border: rgba(255,255,255,0.15);
  --brand-tag-aftersell-border: rgba(255,109,46,0.25);
}}

*,*::before,*::after {{ box-sizing:border-box; margin:0; padding:0 }}

body {{
  background: var(--brand-bg);
  color: var(--brand-text);
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition: background 0.2s ease, color 0.2s ease;
}}

.wrap {{ max-width: 700px; margin: 0 auto; padding: 56px 24px 72px }}

/* ── Header ─────────────────────────────────────────── */
.header {{ margin-bottom: 48px; }}
.header-eyebrow {{
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--brand-primary);
  margin-bottom: 10px;
}}
.header-title {{
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -0.025em;
  color: var(--brand-heading);
  margin-bottom: 4px;
}}
.header-meta {{
  font-size: 13px;
  color: var(--brand-muted);
}}
.header-meta a {{ color: var(--brand-muted); text-decoration: none; }}
.header-meta a:hover {{ color: var(--brand-text); }}
.header-right {{
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 20px;
}}
.header-right .draft-badge {{
  margin-left: auto;
}}

/* ── Install status ─────────────────────────────────── */
.install-status {{
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 20px;
  margin-bottom: 20px;
}}
.install-chip {{
  display: flex;
  align-items: center;
  gap: 10px;
}}
.install-chip-dot {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}}
.chip-on .install-chip-dot {{ background: #4ade80; }}
.chip-off .install-chip-dot {{ background: #ef4444; }}
.install-chip-name {{
  font-size: 14px;
  font-weight: 500;
  color: var(--brand-text);
}}
.install-chip-status {{
  font-size: 13px;
  color: var(--brand-muted);
}}
.draft-badge {{
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.04em;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid var(--brand-border);
  color: var(--brand-muted);
  background: transparent;
}}

/* ── Summary ────────────────────────────────────────── */
.summary-bar {{
  background: var(--brand-surface);
  border: 1px solid var(--brand-border);
  border-radius: 8px;
  padding: 28px 32px;
  margin-bottom: 40px;
}}
.summary-stats {{
  display: flex;
  gap: 0;
  margin-bottom: 24px;
}}
.summary-stat {{
  flex: 1;
  padding-right: 32px;
  border-right: 1px solid var(--brand-border);
  margin-right: 32px;
}}
.summary-stat:last-child {{
  border-right: none;
  padding-right: 0;
  margin-right: 0;
}}
.stat-num {{
  font-family: var(--font-mono);
  font-size: 40px;
  font-weight: 600;
  letter-spacing: -0.04em;
  line-height: 1;
  margin-bottom: 8px;
}}
.stat-num.orange {{ color: var(--brand-primary); }}
.stat-num.green  {{ color: #4ade80; }}
.stat-num.white  {{ color: var(--brand-heading); }}
.stat-label {{
  font-size: 12px;
  color: var(--brand-muted);
  line-height: 1.5;
}}
.stat-label strong {{
  display: block;
  font-size: 13px;
  color: var(--brand-text);
  font-weight: 500;
  margin-bottom: 2px;
}}
.summary-conclusion {{
  font-size: 13px;
  color: var(--brand-muted);
  border-top: 1px solid var(--brand-border);
  padding-top: 20px;
  line-height: 1.6;
}}
.summary-conclusion strong {{
  color: var(--brand-primary);
  font-weight: 500;
}}

/* ── Sections ───────────────────────────────────────── */
.section {{ margin-bottom: 40px; }}
.section-header {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;
}}
.section-title {{
  font-size: 16px;
  font-weight: 600;
  color: var(--brand-heading);
  letter-spacing: -0.01em;
}}
.section-subtitle {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--brand-muted);
}}

/* ── Coverage bar ───────────────────────────────────── */
.coverage {{ margin-bottom: 20px; }}
.coverage-top {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}}
.coverage-label {{
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  color: var(--brand-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}}
.coverage-count {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--brand-muted);
}}
.coverage-track {{
  height: 4px;
  background: var(--brand-border);
  border-radius: 2px;
  overflow: hidden;
}}
.coverage-fill {{
  height: 100%;
  background: var(--brand-primary);
  border-radius: 2px;
}}

/* ── Feature rows (active) ──────────────────────────── */
.active-list {{
  background: var(--brand-surface);
  border: 1px solid var(--brand-border);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}}
.feature-row {{
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--brand-border);
}}
.feature-row:last-child {{ border-bottom: none; }}
.feature-check {{
  width: 20px;
  height: 20px;
  color: var(--brand-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}}
.feature-body {{ flex: 1; min-width: 0; }}
.feature-top {{
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 2px;
}}
.feature-name {{
  font-weight: 500;
  font-size: 14px;
  color: var(--brand-text);
}}
.feature-evidence {{
  font-size: 12px;
  color: var(--brand-evidence);
  line-height: 1.4;
}}

/* ── Mono tags (ghosted) ────────────────────────────── */
.tag-mono {{
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid var(--brand-border);
  background: transparent;
  color: var(--brand-muted);
  white-space: nowrap;
}}
.tag-aftersell {{
  color: var(--brand-primary);
  border-color: var(--brand-tag-aftersell-border);
}}
.tag-other {{ color: var(--brand-muted); }}
.tag-native {{ color: var(--brand-faint); border-color: transparent; }}
.tag-consolidation {{ color: var(--brand-muted); }}

/* ── Opportunity cards ──────────────────────────────── */
.opp-group-label {{
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  color: var(--brand-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 12px;
  margin-top: 4px;
}}
.opportunity-card {{
  display: flex;
  gap: 14px;
  padding: 16px 20px;
  background: var(--brand-surface);
  border: 1px solid var(--brand-border);
  border-radius: 8px;
  margin-bottom: 6px;
  transition: border-color 0.15s ease;
  cursor: default;
}}
.opportunity-card:hover {{
  border-color: var(--brand-primary);
}}
.opportunity-card.unverified {{
  border-color: var(--brand-border);
  background: var(--brand-surface);
}}
.opportunity-card.unverified:hover {{
  border-color: var(--brand-faint);
}}
.opp-icon {{
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: transparent;
  color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
  margin-top: 1px;
  transition: color 0.15s ease;
}}
.opportunity-card:hover .opp-icon {{
  color: var(--brand-primary);
}}
.opp-icon-unverified {{
  color: var(--brand-muted) !important;
}}
.opp-content {{ flex: 1; min-width: 0; }}
.opp-name {{
  font-weight: 500;
  font-size: 14px;
  color: var(--brand-text);
  margin-bottom: 2px;
}}
.opp-desc {{
  font-size: 12px;
  color: var(--brand-muted);
  line-height: 1.45;
}}
.opp-caveat {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--brand-muted);
  margin-top: 4px;
}}

/* ── Empty states ───────────────────────────────────── */
.empty-state {{
  text-align: center;
  padding: 20px;
  color: var(--brand-muted);
  font-size: 13px;
}}

/* ── Blocked note ───────────────────────────────────── */
.blocked-note {{
  background: var(--brand-surface);
  border: 1px solid var(--brand-border);
  border-radius: 6px;
  padding: 12px 16px;
  font-size: 12px;
  color: var(--brand-muted);
  margin-bottom: 16px;
  font-family: var(--font-mono);
}}

/* ── App ecosystem ──────────────────────────────────── */
.eco-section {{
  background: var(--brand-surface);
  border: 1px solid var(--brand-border);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}}
.eco-block {{ padding: 16px 20px; }}
.eco-block + .eco-block {{ border-top: 1px solid var(--brand-border); }}
.eco-label {{
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  color: var(--brand-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 8px;
}}
.app-chip {{
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 4px;
  border: 1px solid var(--brand-border);
  background: transparent;
  color: var(--brand-text);
  margin-right: 4px;
  margin-bottom: 4px;
}}
.app-chip.compatible {{ color: var(--brand-text); }}
.app-chip.competing {{
  color: var(--brand-muted);
  border-color: var(--brand-border);
}}
.eco-empty {{ color: var(--brand-muted); font-size: 12px; }}

/* ── Out of scope ───────────────────────────────────── */
.oos-section {{
  background: var(--brand-surface);
  border: 1px solid var(--brand-border);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 16px;
}}
.oos-section h3 {{
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  color: var(--brand-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 10px;
}}
.oos-item {{
  font-size: 13px;
  color: var(--brand-muted);
  margin-bottom: 4px;
}}
.oos-item strong {{
  color: var(--brand-subtle);
  font-weight: 500;
}}

/* ── Screenshots ────────────────────────────────────── */
.screenshots {{ margin-bottom: 16px; }}
.ss-grid {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}}
.ss-thumb {{
  display: block;
  width: 140px;
  background: var(--brand-surface);
  border: 1px solid var(--brand-border);
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.15s ease;
}}
.ss-thumb:hover {{ border-color: var(--brand-primary); }}
.ss-thumb img {{ width: 100%; display: block; }}
.ss-cap {{
  display: block;
  padding: 6px 8px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--brand-muted);
}}

/* ── Lightbox (CSS-only) ────────────────────────────── */
.lb-toggle {{ display: none; }}
.lb-overlay {{
  display: none;
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0,0,0,0.8);
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 24px;
}}
.lb-toggle:checked + .lb-overlay {{ display: flex; }}
.lb-overlay img {{
  max-width: 90vw;
  max-height: 80vh;
  border-radius: 6px;
}}
.lb-close {{
  position: absolute;
  top: 20px;
  right: 28px;
  font-size: 28px;
  color: rgba(255,255,255,0.6);
  cursor: pointer;
  line-height: 1;
}}
.lb-close:hover {{ color: #FFF; }}
.lb-caption {{
  font-family: var(--font-mono);
  color: rgba(255,255,255,0.5);
  font-size: 11px;
  margin-top: 12px;
}}

/* ── Review notes ───────────────────────────────────── */
.review-box {{
  background: var(--brand-surface);
  border: 1px solid var(--brand-border);
  border-radius: 8px;
  padding: 20px 24px;
}}
.review-label {{
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.06em;
  color: var(--brand-muted);
  padding: 3px 8px;
  border: 1px solid var(--brand-border);
  border-radius: 3px;
  margin-bottom: 14px;
}}
.review-box h3 {{
  font-size: 13px;
  font-weight: 500;
  color: var(--brand-text);
  margin-bottom: 10px;
}}
.review-box ul {{ list-style: none; padding: 0; }}
.review-box li {{
  font-size: 12px;
  color: var(--brand-muted);
  margin-bottom: 6px;
  padding-left: 20px;
  position: relative;
  line-height: 1.5;
}}
.review-box li::before {{
  content: "\u25a1";
  position: absolute;
  left: 0;
  color: var(--brand-faint);
  font-size: 11px;
}}
.verify-tag {{
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--brand-muted);
  font-weight: 500;
}}
.review-box li.all-good {{
  color: var(--brand-text);
  padding-left: 0;
}}
.review-box li.all-good::before {{ content: none; }}
.review-footer {{
  font-size: 11px;
  color: var(--brand-ghost);
  margin-top: 16px;
}}

/* ── Theme toggle ───────────────────────────────────── */
.theme-toggle {{
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 100;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid var(--brand-border);
  background: var(--brand-surface);
  color: var(--brand-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.15s ease, background 0.15s ease;
  padding: 0;
}}
.theme-toggle:hover {{
  border-color: var(--brand-primary);
  color: var(--brand-primary);
}}
.theme-toggle svg {{ width: 16px; height: 16px; }}
.theme-toggle .icon-sun {{ display: none; }}
.theme-toggle .icon-moon {{ display: block; }}
html.dark .theme-toggle .icon-sun {{ display: block; }}
html.dark .theme-toggle .icon-moon {{ display: none; }}

/* ── Print ──────────────────────────────────────────── */
@media print {{
  body {{ background: #FFF; }}
  .wrap {{ padding: 24px 0; }}
  .ss-thumb {{ break-inside: avoid; }}
  .lb-overlay {{ display: none !important; }}
  .opportunity-card:hover {{ border-color: var(--brand-border); }}
  .theme-toggle {{ display: none; }}
}}
</style>
</head>
<body>
<button class="theme-toggle" onclick="document.documentElement.classList.toggle('dark')" aria-label="Toggle dark mode">
  <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
  <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
</button>
<div class="wrap">

  <!-- Header -->
  <div class="header">
    <div class="header-eyebrow">Aftersell Cart Audit</div>
    <div style="display:flex;align-items:flex-start;justify-content:space-between;">
      <div class="header-title">{STORE_NAME}</div>
      <span class="draft-badge">Draft</span>
    </div>
    <div class="install-status">
      {install_chip("Upcart", UPCART_STATUS)}
      {install_chip("Aftersell", AFTERSELL_STATUS)}
    </div>
    <div class="header-meta"><a href="{STORE_URL}">{STORE_URL}</a> &middot; {AUDIT_DATE}</div>
  </div>

  <!-- Summary / TLDR -->
  <div class="summary-bar">
    <div class="summary-stats">
      <div class="summary-stat">
        <div class="stat-num green">{n_opps_all}</div>
        <div class="stat-label"><strong>Aftersell features</strong>Not yet in place</div>
      </div>
      <div class="summary-stat">
        <div class="stat-num orange">{_n_not_aftersell}</div>
        <div class="stat-label"><strong>Features active</strong>None powered by Aftersell</div>
      </div>
      <div class="summary-stat">
        <div class="stat-num white">{_n_compat}</div>
        <div class="stat-label"><strong>Installed apps</strong>Integrate with Aftersell</div>
      </div>
    </div>
    <div class="summary-conclusion">{tldr_conclusion}</div>
  </div>

  <!-- Cart & Product Page -->
  <div class="section">
    <h2 class="section-title">Cart &amp; Product Page</h2>
    {"" if not cart_active_html else f'<div class="opp-group-label">Active ({len(cart_active)})</div><div class="active-list">{cart_active_html}</div>'}
    {"" if not cart_opp_html else f'<div class="opp-group-label">Opportunities ({len(cart_opps)})</div>{cart_opp_html}'}
    {"" if cart_active_html or cart_opp_html else '<div class="empty-state">No cart features evaluated</div>'}
  </div>

  <!-- Checkout -->
  <div class="section">
    <h2 class="section-title">Checkout</h2>
    {blocked_note}
    {"" if not checkout_active_html else f'<div class="opp-group-label">Active ({len(checkout_active)})</div><div class="active-list">{checkout_active_html}</div>'}
    {"" if not checkout_opp_html else f'<div class="opp-group-label">Opportunities ({len(checkout_opps)})</div>{checkout_opp_html}'}
    {"" if checkout_active_html or checkout_opp_html else '<div class="empty-state">No checkout features evaluated</div>'}
  </div>

  <!-- App Ecosystem -->
  <div class="section">
    <h2 class="section-title" style="margin-bottom:12px">Installed Apps</h2>
    <div class="eco-section">
      <div class="eco-block">
        <div class="eco-label">Integrates with Aftersell</div>
        <div>{" ".join(app_chip(a, "compatible") for a in COMPATIBLE_INTEGRATIONS) if COMPATIBLE_INTEGRATIONS else '<span class="eco-empty">None detected</span>'}</div>
      </div>
      <div class="eco-block">
        <div class="eco-label">Competing apps</div>
        <div>{" ".join(app_chip(a, "competing") for a in COMPETING_INTEGRATIONS) if COMPETING_INTEGRATIONS else '<span class="eco-empty">None detected</span>'}</div>
      </div>
    </div>
  </div>

  <!-- Review Notes -->
  <div class="review-box">
    <span class="review-label">DRAFT \u2014 REVIEW BEFORE SHARING</span>
    <h3>Verification checklist</h3>
    <ul>
      {checklist_html}
      <li>Confirm Aftersell/Upcart install status directly with the merchant or via the Aftersell partner portal before your call</li>
    </ul>
    <div class="review-footer">Auto-generated via browser crawl. Not reviewed by an Aftersell account manager.</div>
  </div>

  <!-- Screenshots -->
  <div class="section screenshots">
    <h2 class="section-title" style="margin-bottom:12px">Screenshots</h2>
    <div class="ss-grid">{screenshot_gallery()}</div>
  </div>

  <!-- Out of Scope -->
  <div class="oos-section">
    <h3>Not evaluated (requires live purchase)</h3>
    <div class="oos-item"><strong>Post-Purchase Upsells</strong> \u2014 one-click upsells after order confirmation</div>
    <div class="oos-item"><strong>Thank You Page Widgets</strong> \u2014 order confirmation page widgets</div>
    <div class="oos-item"><strong>Rokt Thanks</strong> \u2014 third-party offer monetization on TY page</div>
  </div>

</div>
</body>
</html>"""

safe = STORE_NAME.lower().replace(" ", "_").replace(".", "_")
out  = f"/tmp/cart_audit_{safe}_{datetime.now().strftime('%Y%m%d')}.html"
open(out, "w").write(HTML)
print(f"OUTPUT:{out}")
