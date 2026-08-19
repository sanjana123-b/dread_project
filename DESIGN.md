# ThreatScope — Implementation Spec (DESIGN.md)

Complete, literal translation of the approved Figma design system into the existing
Django app. Every number in this document is taken from the design export — do not
round, substitute, or "improve" values. Where a value is not listed here, it is not
in the design and must not be invented.

**Target project:** `dread_project/` — Django, server-rendered templates in
`templates/analysis/`, stylesheet in `static/analysis/css/`.

---

## 0. Ground rules for the implementing agent

1. **Do not change behaviour.** No model fields added or removed, no view logic
   rewritten, no URL names changed, no form field names changed. This is a
   presentation-layer overhaul only. If a template change would require a view
   change, stop and flag it instead of doing it.
2. **Keep every existing feature working:** signup, login, logout, project CRUD,
   threat CRUD, search/status/risk filtering, CSV export, Django admin,
   per-user project isolation.
3. **Keep `{% csrf_token %}` in every POST form.** Keep Django's `{{ form.field }}`
   rendering wired to the real field names.
4. **Server-rendered, not an SPA.** No client-side routing, no build step, no npm.
   Vanilla CSS + a small amount of vanilla JS only. No Tailwind, no React —
   the Figma export is React, but the deliverable is Django templates.
5. **One stylesheet, no frameworks.** All CSS goes in
   `static/analysis/css/threatscope.css`. Do not add Bootstrap or any CDN CSS
   besides the Google Fonts import.
6. **Every colour, size, and radius comes from a CSS custom property** defined in
   §2. No raw hex values anywhere below `:root`.
7. **Work on a branch.** `feat/ui-overhaul`. Commit in reviewable chunks
   (tokens → base → components → pages). Open a PR against `main`; do not push
   to `main` directly.

---

## 1. File plan

```
static/analysis/css/
└── threatscope.css          # single stylesheet — replaces the existing one

templates/analysis/
├── base.html                # shell: fonts, nav, flash region, skip link, footer
├── _nav.html                # top navigation bar (include)
├── _flash.html              # Django messages → flash banners (include)
├── _dread_spine_micro.html  # 24×16 inline SVG (include, takes `segments`)
├── _dread_spine_card.html   # 120×54 SVG with letter labels (include)
├── _dread_spine_hero.html   # full-width 160px div-based spine (include)
├── _threat_row.html         # one desktop table row (include)
├── _threat_card_row.html    # one mobile card row (include)
├── _risk_bar.html           # stacked risk distribution bar + legend (include)
├── _empty_state.html        # headline + guidance + action (include)
├── _pagination.html         # pagination control (include)
├── dashboard.html
├── project_list.html
├── project_detail.html
├── project_form.html
├── threat_detail.html
├── threat_form.html
├── confirm_delete.html
├── login.html
├── signup.html
├── 404.html                 # place at templates/404.html
└── 500.html                 # place at templates/500.html

analysis/templatetags/
├── __init__.py
└── threatscope.py           # filters + inclusion tags (§4)
```

**Before writing anything:** list the existing files in `templates/analysis/` and
map them to the names above. Reuse the existing filenames if they differ — the
view code references them. Rename only if you also update the view, and prefer
not to.

---

## 2. Design tokens — paste verbatim

This is the top of `static/analysis/css/threatscope.css`. Do not edit any value.

```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&family=Plus+Jakarta+Sans:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap');

:root {
  /* Surfaces */
  --surface-base: #090A0F;
  --surface-base2: #0F1320;
  --surface-raised: rgba(255, 255, 255, 0.04);
  --surface-overlay: rgba(14, 17, 28, 0.82);
  --surface-sunken: rgba(0, 0, 0, 0.25);

  /* Borders */
  --border-hairline: rgba(255, 255, 255, 0.08);
  --border-strong: rgba(255, 255, 255, 0.16);
  --border-focus: #4c8dff;

  /* Text */
  --text-primary: #f2f5fa;
  --text-secondary: #b4becd;
  --text-muted: #94a3b8;
  --text-disabled: #5a6478;

  /* Accent */
  --accent-primary: #3b82f6;
  --accent-hover: #60a5fa;
  --accent-glow: rgba(59, 130, 246, 0.35);

  /* Risk scale — DATA colours only, never UI chrome */
  --risk-critical: #ff3d71;
  --risk-high: #ff8a3d;
  --risk-medium: #ffc53d;
  --risk-low: #22d3a5;

  /* Status */
  --status-open: #8b9cb8;
  --status-mitigated: #22d3a5;
  --status-accepted: #a78bfa;
  --status-fp: #5a6478;

  /* Type */
  --font-display: "Space Grotesk", system-ui, sans-serif;
  --font-body: "Plus Jakarta Sans", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", "Courier New", monospace;

  --gradient-accent: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899);

  /* Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;

  /* Elevation */
  --shadow-e1: 0 1px 2px rgba(0, 0, 0, 0.4);
  --shadow-e2: 0 8px 24px rgba(0, 0, 0, 0.5);
  --shadow-e3: 0 24px 64px rgba(0, 0, 0, 0.65);
}
```

### Risk tints (used as pill backgrounds — 12% of the solid colour)

| Level | Solid | Tint |
|---|---|---|
| Critical | `#FF3D71` | `rgba(255,61,113,0.12)` |
| High | `#FF8A3D` | `rgba(255,138,61,0.12)` |
| Medium | `#FFC53D` | `rgba(255,197,61,0.12)` |
| Low | `#22D3A5` | `rgba(34,211,165,0.12)` |

### Status chip backgrounds (10–12%)

| Status | Text/dot colour | Background |
|---|---|---|
| Open | `#8B9CB8` | `rgba(139,156,184,0.1)` |
| Mitigated | `#22D3A5` | `rgba(34,211,165,0.1)` |
| Risk Accepted | `#A78BFA` | `rgba(167,139,250,0.1)` |
| False Positive | `#5A6478` | `rgba(90,100,120,0.12)` |

Status chip border is the status colour at 20% alpha (`{color}33` in the export).

### Motion tokens

| Token | Duration | Easing | Used for |
|---|---|---|---|
| fast | `120ms` | `ease-out` | hover, focus, background changes |
| base | `200ms` | `cubic-bezier(0.2, 0, 0, 1)` | card hover elevation |
| slow | `320ms` | `cubic-bezier(0.2, 0, 0, 1)` | hero spine fill on load |

Loading spinner: `600ms linear infinite`.

---

## 3. Base / global CSS — paste verbatim

Directly after the `:root` block.

```css
*,
*::before,
*::after { box-sizing: border-box; }

html, body { margin: 0; padding: 0; min-height: 100vh; }

body {
  background-color: var(--surface-base);
  color: var(--text-primary);
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
}

/* Background grid texture — 2.5% hairline, 32px cell.
   This is the ONLY background decoration. No orbs, no mesh, no blur blobs. */
body::before {
  content: "";
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
  background-size: 32px 32px;
  pointer-events: none;
  z-index: 0;
}

.page-shell { position: relative; z-index: 1; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.18); }

/* Type utilities */
.font-display { font-family: var(--font-display); }
.font-mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }

/* Gradient text — permitted ONCE per screen (logo, or one hero number) */
.gradient-text {
  background: var(--gradient-accent);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Glass card — the only blurred surface level. Never nest one inside another. */
.glass-card {
  background: var(--surface-raised);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--border-hairline);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-e1);
}

.surface-sunken {
  background: var(--surface-sunken);
  border: 1px solid var(--border-hairline);
}

/* Focus ring — every interactive element, no exceptions */
.focus-ring:focus-visible,
a:focus-visible,
button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
[tabindex]:focus-visible {
  outline: 2px solid var(--border-focus);
  outline-offset: 2px;
}

/* Skip link */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--accent-primary);
  color: #fff;
  padding: 8px 16px;
  z-index: 100;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
}
.skip-link:focus { top: 0; }

/* Screen-reader only */
.sr-only {
  position: absolute; width: 1px; height: 1px;
  padding: 0; margin: -1px; overflow: hidden;
  clip: rect(0,0,0,0); white-space: nowrap; border: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 4. Typography scale

Apply these exactly. Every heading uses `--font-display`; every number uses
`--font-mono` with tabular figures; everything else uses `--font-body`.

| Role | Family | Size / line-height | Weight | Letter-spacing | Colour |
|---|---|---|---|---|---|
| Page title (`h1`) | display | 28 / 36px | 600 | `-0.01em` | `--text-primary` |
| Auth headline | display | 28 / 34px | 600 | `-0.01em` | `--text-primary` |
| Auth panel headline | display | 32 / 40px | 600 | `-0.01em` | `--text-primary` |
| Section heading (`h2`) | display | 24 / 32px | 600 | `-0.01em` | `--text-primary` |
| Card title (`h3`) | display | 16 / 24px | 600 | 0 | `--text-primary` |
| Table card heading | display | 16 / 24px | 600 | 0 | `--text-primary` |
| Empty-state headline | display | 18 / 26px | 600 | 0 | `--text-primary` |
| Body | body | 14 / 22px | 400 | 0 | `--text-muted` (sub) / `--text-secondary` (prose) |
| Long-form prose | body | 15 / 26px | 400 | 0 | `--text-secondary`, `max-width: 72ch` |
| Field label | body | 13 / 18px | 500 | 0 | `--text-secondary` |
| Eyebrow / caps label | body | 11 / 14px | 600 | `0.12em`, uppercase | `--text-muted` |
| Table header | body | 11 / 14px | 600 | `0.1em`, uppercase | `--text-muted` |
| Hint / helper text | body | 12 / 18px | 400 | 0 | `--text-muted` |
| Rating extremity hint | body | 11 / 16px | 400 | 0 | `--text-disabled` |
| Stat card value | mono | 44 / 44px | 600 | `-0.01em` | `--text-primary` or risk colour |
| Threat detail score | mono | 56 / 56px | 600 | `-0.02em` | risk colour |
| Live score preview | mono | 36 / 36px | 600 | 0 | risk colour |
| Factor value (rating) | mono | 20 / 20px | 600 | 0 | factor colour |
| Table score cell | mono | 14 / 20px | 600 | 0 | risk colour |
| Timestamp / meta | mono | 11 / 16px | 500 | 0 | `--text-disabled` |
| 404 / 500 numeral | mono | 96 / 96px | 600 | 0 | `rgba(255,255,255,0.04)` / `rgba(255,61,113,0.07)` |

Add to the stylesheet:

```css
h1, h2, h3, h4 { font-family: var(--font-display); margin: 0; }

.eyebrow {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0;
}

.meta-mono {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-disabled);
  font-variant-numeric: tabular-nums;
}

.prose {
  font-size: 15px;
  line-height: 26px;
  color: var(--text-secondary);
  max-width: 72ch;
  margin: 0;
}
```

---

## 5. Layout system

- **Page container:** `max-width: 1280px; margin: 0 auto; padding: 32px 32px 64px;`
- **Content offset for fixed nav:** body content wrapper gets `padding-top: 56px`
  (nav height). Auth pages get `0`.
- **Spacing scale (8pt):** `2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 48, 64`.
  Off-scale values are not permitted.
- **Grid gaps:** stat cards `16px`, project cards `16px`, detail two-column `24px`.

```css
.page-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 32px 64px;
}
```

### Breakpoints

Only one hard breakpoint is defined in the design: **640px**. Everything above it
is the desktop layout; below it is the mobile layout.

```css
@media (max-width: 640px) {
  .threat-table-desktop { display: none; }
  .threat-table-mobile { display: flex; flex-direction: column; }
  .stat-grid { grid-template-columns: repeat(2, 1fr) !important; }
  .page-container { padding-left: 16px !important; padding-right: 16px !important; }
  .auth-split-right { display: none !important; }
  .auth-form-panel {
    max-width: 100% !important;
    border-right: none !important;
    padding: 32px 24px !important;
  }
  .threat-detail-grid { grid-template-columns: 1fr !important; }
  .threat-form-grid { grid-template-columns: 1fr !important; }
  .score-preview-sticky { position: static !important; }
}

@media (min-width: 641px) {
  .threat-table-mobile { display: none; }
}
```

**Mobile tables do not scroll horizontally.** The desktop `<table>` is hidden and a
stacked card list is shown instead. Both render the same queryset — render both in
the template, hide one with CSS.

---

## 6. Python support layer

Create `analysis/templatetags/threatscope.py`. This is the **only** Python addition
permitted, and it adds no model or view logic — it computes presentation values.

```python
from django import template

register = template.Library()

RISK_COLORS = {
    "Critical": "#FF3D71",
    "High": "#FF8A3D",
    "Medium": "#FFC53D",
    "Low": "#22D3A5",
}

RISK_TINTS = {
    "Critical": "rgba(255,61,113,0.12)",
    "High": "rgba(255,138,61,0.12)",
    "Medium": "rgba(255,197,61,0.12)",
    "Low": "rgba(34,211,165,0.12)",
}

RISK_GLYPHS = {
    "Critical": "\u25C6",   # ◆
    "High": "\u25B2",       # ▲
    "Medium": "\u25A0",     # ■
    "Low": "\u25CF",        # ●
}

STATUS_COLORS = {
    "Open": "#8B9CB8",
    "Mitigated": "#22D3A5",
    "Risk Accepted": "#A78BFA",
    "False Positive": "#5A6478",
}

STATUS_BG = {
    "Open": "rgba(139,156,184,0.1)",
    "Mitigated": "rgba(34,211,165,0.1)",
    "Risk Accepted": "rgba(167,139,250,0.1)",
    "False Positive": "rgba(90,100,120,0.12)",
}

STRIDE_ABBR = {
    "Spoofing": "S",
    "Tampering": "T",
    "Repudiation": "R",
    "Information Disclosure": "I",
    "Denial of Service": "D",
    "Elevation of Privilege": "E",
}

FACTOR_NAMES = [
    ("D", "Damage", "damage"),
    ("R", "Reproducibility", "reproducibility"),
    ("E", "Exploitability", "exploitability"),
    ("A", "Affected Users", "affected_users"),
    ("D", "Discoverability", "discoverability"),
]


def _factor_color(value):
    """Per-factor colour. Driven by the individual rating, NOT the overall level."""
    if value >= 8:
        return "#FF3D71"
    if value >= 6:
        return "#FF8A3D"
    if value >= 4:
        return "#FFC53D"
    return "#22D3A5"


@register.filter
def risk_color(level):
    return RISK_COLORS.get(level, "#5A6478")


@register.filter
def risk_tint(level):
    return RISK_TINTS.get(level, "rgba(90,100,120,0.12)")


@register.filter
def risk_glyph(level):
    return RISK_GLYPHS.get(level, "\u25CF")


@register.filter
def status_color(status):
    return STATUS_COLORS.get(status, "#5A6478")


@register.filter
def status_bg(status):
    return STATUS_BG.get(status, "rgba(90,100,120,0.12)")


@register.filter
def stride_abbr(category):
    return STRIDE_ABBR.get(category, "?")


@register.filter
def factor_color(value):
    return _factor_color(value)


@register.filter
def pct_of_ten(value):
    """Rating 1-10 -> percentage string for CSS height."""
    return (float(value) / 10.0) * 100.0


def _values(threat):
    return [
        threat.damage,
        threat.reproducibility,
        threat.exploitability,
        threat.affected_users,
        threat.discoverability,
    ]


@register.inclusion_tag("analysis/_dread_spine_micro.html")
def dread_spine_micro(threat):
    """24x16 inline fingerprint. segW=3, gap=1.5, H=16."""
    W, H, seg_w, gap = 24, 16, 3, 1.5
    vals = _values(threat)
    segs = []
    for i, v in enumerate(vals):
        fill_h = (v / 10.0) * H
        segs.append({
            "x": i * (seg_w + gap),
            "w": seg_w,
            "h": H,
            "fill_h": fill_h,
            "y": H - fill_h,
            "color": _factor_color(v),
        })
    return {
        "W": W, "H": H, "segments": segs,
        "label": "DREAD profile: D%s R%s E%s A%s D%s" % tuple(vals),
    }


@register.inclusion_tag("analysis/_dread_spine_card.html")
def dread_spine_card(threat):
    """120x54 with single-letter labels. segH=36, labelH=14, gap=5, segW=20."""
    W, seg_h, label_h, gap = 120, 36, 14, 5
    seg_w = (W - gap * 4) / 5.0
    total_h = seg_h + label_h + 4
    vals = _values(threat)
    letters = ["D", "R", "E", "A", "D"]
    segs = []
    for i, v in enumerate(vals):
        fill_h = (v / 10.0) * seg_h
        segs.append({
            "x": i * (seg_w + gap),
            "cx": i * (seg_w + gap) + seg_w / 2.0,
            "w": seg_w,
            "h": seg_h,
            "fill_h": fill_h,
            "y": seg_h - fill_h,
            "color": _factor_color(v),
            "letter": letters[i],
        })
    return {
        "W": W, "total_h": total_h, "label_y": seg_h + label_h + 1,
        "segments": segs,
        "label": "DREAD profile: D%s R%s E%s A%s D%s" % tuple(vals),
    }


@register.inclusion_tag("analysis/_dread_spine_hero.html")
def dread_spine_hero(threat):
    """Full-width, 160px tall, factor names + values + average threshold line."""
    vals = _values(threat)
    score = sum(vals) / 5.0
    segs = []
    for (letter, name, _field), v in zip(FACTOR_NAMES, vals):
        fill_pct = (v / 10.0) * 100.0
        segs.append({
            "value": v,
            "name": name,
            "letter": letter,
            "fill_pct": fill_pct,
            "color": _factor_color(v),
            "inside": fill_pct > 20,          # label sits inside the fill
            "label_offset": fill_pct,          # used when label sits above the fill
        })
    return {
        "segments": segs,
        "score": score,
        "threshold_top": 100.0 - (score / 10.0) * 100.0,
        "label": (
            "DREAD scores — Damage: %s, Reproducibility: %s, Exploitability: %s, "
            "Affected Users: %s, Discoverability: %s. Average: %.1f"
            % (vals[0], vals[1], vals[2], vals[3], vals[4], score)
        ),
    }


@register.inclusion_tag("analysis/_risk_bar.html")
def risk_bar(counts):
    """counts: dict with Critical/High/Medium/Low integer keys."""
    order = ["Critical", "High", "Medium", "Low"]
    total = sum(counts.get(k, 0) for k in order) or 0
    segments = []
    for level in order:
        n = counts.get(level, 0)
        pct = (n / total * 100.0) if total else 0
        segments.append({
            "level": level,
            "count": n,
            "pct": pct,
            "color": RISK_COLORS[level],
        })
    return {
        "segments": segments,
        "total": total,
        "aria": "Risk distribution: " + ", ".join(
            "%s %s" % (counts.get(l, 0), l) for l in order
        ),
    }
```

Register the templatetags package in `INSTALLED_APPS` only if `analysis` is not
already listed (it is). Ensure `analysis/templatetags/__init__.py` exists and is
empty. Load with `{% load threatscope %}` at the top of every template that uses
these.

**Views must supply `risk_counts`** as a dict keyed `Critical/High/Medium/Low` on
the dashboard, project list cards, and project detail. If the existing view already
computes this under a different name, pass it through with the existing name — do
not rename view context.

---

## 7. Component specifications

### 7.1 Button

Five variants, three sizes. `.btn` + `.btn--{variant}` + `.btn--{size}`.

| Variant | Background | Text | Border |
|---|---|---|---|
| primary | `var(--accent-primary)` | `#fff` | `1px solid transparent` |
| secondary | `transparent` | `var(--text-secondary)` | `1px solid var(--border-strong)` |
| ghost | `transparent` | `var(--text-secondary)` | `1px solid transparent` |
| danger | `rgba(255,61,113,0.12)` | `var(--risk-critical)` | `1px solid rgba(255,61,113,0.3)` |
| icon | `rgba(255,255,255,0.06)` | `var(--text-secondary)` | `1px solid var(--border-hairline)` |

| Size | Padding | Font-size | Radius |
|---|---|---|---|
| sm | `5px 12px` | 12px | `var(--radius-sm)` |
| md | `8px 16px` | 13px | `var(--radius-sm)` |
| lg | `11px 22px` | 14px | `var(--radius-md)` |

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-family: var(--font-body);
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  text-decoration: none;
  transition: background 120ms ease-out, box-shadow 120ms ease-out, opacity 120ms ease-out;
}
.btn:disabled, .btn[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }

.btn--primary   { background: var(--accent-primary); color: #fff; border: 1px solid transparent; }
.btn--primary:hover:not(:disabled) { background: var(--accent-hover); }
.btn--secondary { background: transparent; color: var(--text-secondary); border: 1px solid var(--border-strong); }
.btn--secondary:hover:not(:disabled) { background: rgba(255,255,255,0.04); color: var(--text-primary); }
.btn--ghost     { background: transparent; color: var(--text-secondary); border: 1px solid transparent; }
.btn--ghost:hover:not(:disabled) { background: rgba(255,255,255,0.04); color: var(--text-primary); }
.btn--danger    { background: rgba(255,61,113,0.12); color: var(--risk-critical); border: 1px solid rgba(255,61,113,0.3); }
.btn--danger:hover:not(:disabled) { background: rgba(255,61,113,0.2); }
.btn--icon      { background: rgba(255,255,255,0.06); color: var(--text-secondary); border: 1px solid var(--border-hairline); }

.btn--sm { padding: 5px 12px;  font-size: 12px; border-radius: var(--radius-sm); }
.btn--md { padding: 8px 16px;  font-size: 13px; border-radius: var(--radius-sm); }
.btn--lg { padding: 11px 22px; font-size: 14px; border-radius: var(--radius-md); }

/* The ONE permitted glow — primary CTA only, one per screen */
.btn--glow { box-shadow: 0 0 20px var(--accent-glow); }

.btn__spinner {
  width: 12px; height: 12px;
  border: 1.5px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 600ms linear infinite;
  flex-shrink: 0;
}
```

**Loading state (submit buttons):** on submit, JS adds `.is-loading`, injects a
`.btn__spinner` span before the label, sets `aria-busy="true"`, and disables the
button. The label text does **not** change, so the button does not resize.

```html
<button type="submit" class="btn btn--primary btn--md focus-ring" data-loading-btn>
  Save changes
</button>
```

```js
document.querySelectorAll('form').forEach(function (form) {
  form.addEventListener('submit', function () {
    var btn = form.querySelector('[data-loading-btn]');
    if (!btn || btn.dataset.busy) return;
    btn.dataset.busy = '1';
    btn.setAttribute('aria-busy', 'true');
    btn.insertAdjacentHTML('afterbegin', '<span class="btn__spinner" aria-hidden="true"></span>');
    // do NOT disable before submit — a disabled button's value is not posted
    setTimeout(function () { btn.disabled = true; }, 0);
  });
});
```

### 7.2 Form field

Label **above** the field (not floating). Error message **below** the field with a
`⚠` glyph. Required marker is a `--risk-critical` asterisk.

```css
.field { display: flex; flex-direction: column; gap: 6px; }

.field__label {
  display: flex; align-items: center; gap: 4px;
  font-family: var(--font-body);
  font-size: 13px; font-weight: 500;
  color: var(--text-secondary);
}
.field__required { color: var(--risk-critical); font-size: 14px; line-height: 1; }

.field__error {
  display: flex; align-items: center; gap: 4px;
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--risk-critical);
}
.field__hint {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--text-muted);
}

.input-base {
  background: var(--surface-sunken);
  border: 1px solid var(--border-hairline);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 22px;
  padding: 10px 12px;
  width: 100%;
  transition: border-color 120ms ease-out, box-shadow 120ms ease-out;
}
.input-base::placeholder { color: var(--text-disabled); }
.input-base:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(76, 141, 255, 0.18);
}
.input-base.is-error { border-color: var(--risk-critical); }
.input-base.is-error:focus { box-shadow: 0 0 0 3px rgba(255, 61, 113, 0.18); }
.input-base:disabled { color: var(--text-disabled); cursor: not-allowed; opacity: 0.6; }

textarea.input-base { resize: vertical; min-height: 100px; }

select.input-base {
  appearance: none;
  padding-right: 32px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' stroke='%2394a3b8' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
}
```

**Django wiring.** Add the base class in `forms.py` widget attrs (this is a widget
attribute change, not logic — permitted):

```python
for name, field in self.fields.items():
    field.widget.attrs.setdefault("class", "input-base focus-ring")
```

Render each field with this partial pattern:

```html
<div class="field">
  <label class="field__label" for="{{ field.id_for_label }}">
    {{ field.label }}
    {% if field.field.required %}<span class="field__required" aria-hidden="true">*</span>{% endif %}
  </label>
  {{ field }}
  {% for error in field.errors %}
    <span class="field__error" role="alert"><span aria-hidden="true">⚠</span> {{ error }}</span>
  {% endfor %}
  {% if field.help_text and not field.errors %}
    <span class="field__hint">{{ field.help_text }}</span>
  {% endif %}
</div>
```

Add `is-error` to the input when `field.errors` is non-empty. Do this in the
template with a wrapper class and a CSS descendant rule, so no Python is needed:

```css
.field.has-error .input-base { border-color: var(--risk-critical); }
.field.has-error .input-base:focus { box-shadow: 0 0 0 3px rgba(255,61,113,0.18); }
```

### 7.3 Form error summary

Rendered at the top of the form when `form.errors` is non-empty. This is essential
for Django's full-page re-render on failed POST.

```css
.form-errors {
  background: rgba(255,61,113,0.08);
  border: 1px solid rgba(255,61,113,0.25);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  display: flex; flex-direction: column; gap: 6px;
}
.form-errors__title {
  margin: 0;
  font-family: var(--font-body);
  font-size: 13px; font-weight: 600;
  color: var(--risk-critical);
}
.form-errors ul { margin: 0; padding-left: 16px; display: flex; flex-direction: column; gap: 4px; }
.form-errors li { font-family: var(--font-body); font-size: 13px; color: var(--text-secondary); }
```

```html
{% if form.errors %}
<div class="form-errors" role="alert">
  <p class="form-errors__title">Fix the following errors to continue:</p>
  <ul>
    {% for field in form %}{% for error in field.errors %}<li>{{ error }}</li>{% endfor %}{% endfor %}
    {% for error in form.non_field_errors %}<li>{{ error }}</li>{% endfor %}
  </ul>
</div>
{% endif %}
```

### 7.4 Risk pill

Tint background, **solid 1px border in the risk colour**, text in the risk colour,
plus a unique leading glyph per level so it survives greyscale.

Glyphs: Critical `◆` · High `▲` · Medium `■` · Low `●`

```css
.risk-pill {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 10px;
  border-radius: 20px;
  font-family: var(--font-body);
  font-size: 12px; font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  letter-spacing: 0.01em;
}
.risk-pill__glyph { font-size: 8px; }
.risk-pill--compact { padding: 2px 7px; gap: 3px; font-size: 11px; }
.risk-pill--compact .risk-pill__glyph { font-size: 7px; }
```

```html
{% load threatscope %}
<span class="risk-pill" aria-label="Risk level: {{ threat.risk_level }}"
      style="background: {{ threat.risk_level|risk_tint }}; border: 1px solid {{ threat.risk_level|risk_color }}; color: {{ threat.risk_level|risk_color }};">
  <span class="risk-pill__glyph" aria-hidden="true">{{ threat.risk_level|risk_glyph }}</span>{{ threat.risk_level }}
</span>
```

### 7.5 Status chip

Quieter than the risk pill — 6px radius (not a pill), 20%-alpha border, 6px dot.

```css
.status-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 9px;
  border-radius: 6px;
  font-family: var(--font-body);
  font-size: 12px; font-weight: 500;
  line-height: 1.4;
  white-space: nowrap;
}
.status-chip__dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
```

```html
<span class="status-chip" aria-label="Status: {{ threat.get_status_display }}"
      style="background: {{ threat.get_status_display|status_bg }}; border: 1px solid {{ threat.get_status_display|status_color }}33; color: {{ threat.get_status_display|status_color }};">
  <span class="status-chip__dot" aria-hidden="true"></span>{{ threat.get_status_display }}
</span>
```

### 7.6 STRIDE tag

Monospace, neutral outline, with the letter abbreviation in accent blue.

```css
.stride-tag {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 9px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border-hairline);
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 11px; font-weight: 500;
  color: var(--text-secondary);
  line-height: 1.4;
  white-space: nowrap;
  letter-spacing: 0.02em;
}
.stride-tag__abbr { font-weight: 700; color: var(--accent-primary); }
```

### 7.7 DREAD Spine — the signature element

Appears at three scales. Segment colour is driven by **each factor's own value**
via `factor_color`, never by the overall risk level. Order is always D, R, E, A, D.

#### Micro — `_dread_spine_micro.html` (24×16, table rows)

```html
<svg width="{{ W }}" height="{{ H }}" viewBox="0 0 {{ W }} {{ H }}"
     role="img" aria-label="{{ label }}" style="display:block;flex-shrink:0">
  {% for s in segments %}
    <rect x="{{ s.x }}" y="0" width="{{ s.w }}" height="{{ s.h }}" fill="rgba(255,255,255,0.07)" rx="1"/>
    <rect x="{{ s.x }}" y="{{ s.y }}" width="{{ s.w }}" height="{{ s.fill_h }}" fill="{{ s.color }}" rx="1"/>
  {% endfor %}
</svg>
```

Geometry: segment width `3`, gap `1.5`, so x positions are `0, 4.5, 9, 13.5, 18`.
Track fill `rgba(255,255,255,0.07)`, corner radius `1`.

#### Card — `_dread_spine_card.html` (120×54, project/threat cards)

Segment width `20`, gap `5` (x = `0, 25, 50, 75, 100`), segment height `36`,
label row `14px` beneath, corner radius `2`, track `rgba(255,255,255,0.06)`.
Letters `D R E A D` in JetBrains Mono 10px/500, `rgba(255,255,255,0.35)`,
centred under each segment.

```html
<svg width="{{ W }}" height="{{ total_h }}" viewBox="0 0 {{ W }} {{ total_h }}"
     role="img" aria-label="{{ label }}" style="display:block;overflow:visible">
  {% for s in segments %}
    <rect x="{{ s.x }}" y="0" width="{{ s.w }}" height="{{ s.h }}" fill="rgba(255,255,255,0.06)" rx="2"/>
    <rect x="{{ s.x }}" y="{{ s.y }}" width="{{ s.w }}" height="{{ s.fill_h }}" fill="{{ s.color }}" rx="2"/>
    <text x="{{ s.cx }}" y="{{ label_y }}" text-anchor="middle" fill="rgba(255,255,255,0.35)"
          font-size="10" font-family="JetBrains Mono, monospace" font-weight="500">{{ s.letter }}</text>
  {% endfor %}
</svg>
```

#### Hero — `_dread_spine_hero.html` (full-width, 160px, threat detail)

Built with divs, not SVG, so it can animate. Five flex columns, `gap: 8px`,
height `160px`, radius `4px`, track `rgba(255,255,255,0.06)`.

- **Average threshold line:** absolutely positioned across the full width at
  `top: {{ threshold_top }}%`, `height: 1px`, `background: rgba(255,255,255,0.28)`, `z-index: 2`.
- **Numeric value:** JetBrains Mono 18px/600. If fill > 20% of the column height,
  the number sits **inside** the fill at `bottom: 10px` in `rgba(255,255,255,0.9)`.
  Otherwise it sits **above** the fill at `bottom: calc({fill}% + 8px)` in the
  factor colour.
- **Factor names** below: 11px/600, `0.09em` tracking, uppercase, `--text-muted`,
  `margin-top: 10px`, centred per column.
- **Fill animation:** columns start at `height: 0`, then a `requestAnimationFrame`
  adds `.is-mounted` to the wrapper and heights transition to their final value
  over `320ms cubic-bezier(0.2, 0, 0, 1)`. Under `prefers-reduced-motion` the
  global transition override makes this instant — no extra code needed.

```html
<div class="spine-hero" role="img" aria-label="{{ label }}">
  <div class="spine-hero__track">
    <div class="spine-hero__threshold" style="top: {{ threshold_top }}%"></div>
    {% for s in segments %}
      <div class="spine-hero__col">
        <div class="spine-hero__bg"></div>
        <div class="spine-hero__fill" style="--fill: {{ s.fill_pct }}%; background: {{ s.color }}"></div>
        <div class="spine-hero__value{% if not s.inside %} spine-hero__value--above{% endif %}"
             style="{% if s.inside %}color: rgba(255,255,255,0.9){% else %}color: {{ s.color }}; --fill: {{ s.fill_pct }}%{% endif %}">{{ s.value }}</div>
      </div>
    {% endfor %}
  </div>
  <div class="spine-hero__names">
    {% for s in segments %}<div class="spine-hero__name">{{ s.name }}</div>{% endfor %}
  </div>
</div>
```

```css
.spine-hero { width: 100%; }
.spine-hero__track { display: flex; gap: 8px; height: 160px; position: relative; }
.spine-hero__threshold {
  position: absolute; left: 0; right: 0; height: 1px;
  background: rgba(255,255,255,0.28); pointer-events: none; z-index: 2;
}
.spine-hero__col { flex: 1; position: relative; }
.spine-hero__bg { position: absolute; inset: 0; background: rgba(255,255,255,0.06); border-radius: 4px; }
.spine-hero__fill {
  position: absolute; bottom: 0; left: 0; right: 0;
  height: 0; border-radius: 4px;
  transition: height 320ms cubic-bezier(0.2, 0, 0, 1);
}
.is-mounted .spine-hero__fill { height: var(--fill); }
.spine-hero__value {
  position: absolute; bottom: 10px; left: 0; right: 0;
  text-align: center;
  font-family: var(--font-mono); font-size: 18px; font-weight: 600;
  font-variant-numeric: tabular-nums; line-height: 1;
  opacity: 0; transition: opacity 320ms cubic-bezier(0.2, 0, 0, 1), bottom 320ms cubic-bezier(0.2, 0, 0, 1);
}
.spine-hero__value--above { bottom: 8px; }
.is-mounted .spine-hero__value { opacity: 1; }
.is-mounted .spine-hero__value--above { bottom: calc(var(--fill) + 8px); }
.spine-hero__names { display: flex; gap: 8px; margin-top: 10px; }
.spine-hero__name {
  flex: 1; text-align: center;
  font-family: var(--font-body); font-size: 11px; font-weight: 600;
  letter-spacing: 0.09em; text-transform: uppercase; color: var(--text-muted);
}
```

```js
requestAnimationFrame(function () {
  document.querySelectorAll('.spine-hero').forEach(function (el) { el.classList.add('is-mounted'); });
});
```

### 7.8 DREAD rating control (threat form)

The most important form component. Ten discrete segments per factor.

Structure per factor:
1. **Label row** — left: a monospace letter badge (`D`/`R`/`E`/`A`/`D`) coloured by
   the current value, then the full factor name. Right: the current value in
   JetBrains Mono 20px/600 in the factor colour, `min-width: 28px`, right-aligned,
   `aria-live="polite"`.
2. **Segment strip** — 10 segments, `flex: 1` each, `gap: 3px`, `height: 28px`,
   `border-radius: 4px`. Active segments (index ≤ value) use `factor_color(index+1)`
   with a `{color}60` border; inactive use `rgba(255,255,255,0.07)` with
   `rgba(255,255,255,0.06)` border.
3. **Hint row** — `1 — {hint1}` left, `10 — {hint10}` right, 11px, `--text-disabled`,
   each capped at `48%` width.

Letter badge: mono 11px/600, `0.08em` tracking, uppercase, colour = factor colour,
background `{color}18`, border `1px solid {color}40`, radius `4`, padding `1px 5px`.

Factors are separated by a `1px` `--border-hairline` divider, `20px` gap between blocks.

**Exact hint copy — use verbatim:**

| Factor | 1 — | 10 — |
|---|---|---|
| Damage | Minimal impact, easily recovered | Full system compromise, data destroyed or exfiltrated |
| Reproducibility | Only under rare conditions | Trivially reproducible every time |
| Exploitability | Requires specialized hardware or expertise | No skill needed, automated tooling available |
| Affected Users | Single user or internal service | All users or the entire customer base |
| Discoverability | Obscure or deeply buried code path | Publicly documented, exposed to the internet |

**Django wiring.** The real form field is a number/select input named `damage`,
`reproducibility`, etc. Render it as a **hidden input** carrying the value, with
the segment strip as the visible control writing into it. Keep the hidden input's
`name` and `id` exactly as Django generates them so POST still works.

```html
<div class="rating" data-rating data-field="{{ field.html_name }}">
  <input type="hidden" name="{{ field.html_name }}" id="{{ field.id_for_label }}" value="{{ field.value|default:5 }}">
  <div class="rating__head">
    <label class="rating__label" for="{{ field.id_for_label }}">
      <span class="rating__badge" data-badge>D</span> Damage
    </label>
    <span class="rating__value" data-value aria-live="polite">{{ field.value|default:5 }}</span>
  </div>
  <div class="rating__strip" role="slider" tabindex="0"
       aria-valuemin="1" aria-valuemax="10" aria-valuenow="{{ field.value|default:5 }}"
       aria-label="Damage rating">
    {% for i in "12345678910"|make_list %}<span class="rating__seg" data-seg></span>{% endfor %}
  </div>
  <div class="rating__hints">
    <span>1 — Minimal impact, easily recovered</span>
    <span>10 — Full system compromise, data destroyed or exfiltrated</span>
  </div>
</div>
```

> The `make_list` trick above produces 11 items — build the 10 segments in JS
> instead, or pass a `range(1, 11)` list from the view context. Prefer generating
> the ten `<span>` elements in JS on page load from the hidden input's value.

Keyboard: `ArrowRight`/`ArrowUp` increments (max 10), `ArrowLeft`/`ArrowDown`
decrements (min 1). Click on a segment sets the value to that segment's index.
Every change updates: the hidden input, the numeric readout, `aria-valuenow`,
the badge colour, the segment colours, and the live score preview (§7.9).

**Progressive enhancement:** if JS is off, the hidden input must fall back to a
visible `<input type="number" min="1" max="10">`. Wrap the enhanced markup in a
`<noscript>`-safe pattern: render the number input, and let JS replace it.

### 7.9 Live score preview (threat form sidebar)

Sunken surface, `--radius-md`, padding `16px 20px`, flex row, `justify-content: space-between`.

- Left: eyebrow `DREAD SCORE`, then the score in mono 36px/600 in the level colour,
  one decimal place.
- Right: eyebrow `RISK LEVEL` right-aligned, then a risk pill at 13px/600,
  padding `4px 12px`, radius 20, background `{color}18`, border `1px solid {color}`.
- Wrapper has `aria-live="polite"`.

Thresholds (must match `Threat.risk_level` exactly): `≥8.0` Critical · `6.0–7.9`
High · `4.0–5.9` Medium · `<4.0` Low.

Below it, a **DREAD Scale** reference card (glass, padding `16px 18px`) listing:

| `≥ 8.0` | Critical |
| `6.0 – 7.9` | High |
| `4.0 – 5.9` | Medium |
| `< 4.0` | Low |

Range in mono 11px `--text-muted` on the left, level name in body 11px/600 in the
level colour on the right, `6px` gap between rows.

### 7.10 Stat card

```css
.stat-card { padding: 24px 24px 20px; display: flex; flex-direction: column; gap: 8px; }
.stat-card__label {
  font-family: var(--font-body); font-size: 11px; font-weight: 600;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-muted);
}
.stat-card__row { display: flex; align-items: flex-end; gap: 10px; justify-content: space-between; }
.stat-card__value {
  font-family: var(--font-mono); font-size: 44px; font-weight: 600;
  line-height: 1; letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums; color: var(--text-primary);
}
.stat-card__delta { font-size: 12px; font-weight: 500; margin-bottom: 6px; }
```

Uses `.glass-card` as the wrapper. Critical/High cards set
`style="color: {{ level|risk_color }}"` on the value when the count is > 0;
otherwise the value stays `--text-primary`.

**Gradient text is not used on stat cards.** Four gradient numbers in a row is
explicitly out of scope for this design.

### 7.11 Risk distribution bar — `_risk_bar.html`

Height `8px`, radius `4px`, `gap: 1px` between segments, `overflow: hidden`.
Order is fixed **Critical → High → Medium → Low**, left to right, always.
Segments with a count of 0 are not rendered. Every rendered segment has
`min-width: 4px` so a tiny slice is still visible.

Legend below at `margin-top: 8px`, `gap: 16px`, wrapping. Each item: an `8×8`
square with `border-radius: 2px` in the risk colour, then `{count} {Level}` in
mono 11px `--text-muted`.

Empty state (total = 0): a single `8px` bar in `rgba(255,255,255,0.06)`, radius 4,
no legend.

```html
{% if total %}
<div class="risk-bar" role="img" aria-label="{{ aria }}">
  {% for s in segments %}{% if s.count %}
    <div class="risk-bar__seg" style="flex: 0 0 {{ s.pct|floatformat:2 }}%; background: {{ s.color }}"
         title="{{ s.level }}: {{ s.count }} ({{ s.pct|floatformat:0 }}%)"></div>
  {% endif %}{% endfor %}
</div>
<div class="risk-bar__legend">
  {% for s in segments %}
  <div class="risk-bar__legend-item">
    <span class="risk-bar__swatch" style="background: {{ s.color }}" aria-hidden="true"></span>
    <span class="risk-bar__legend-text">{{ s.count }} {{ s.level }}</span>
  </div>
  {% endfor %}
</div>
{% else %}
<div class="risk-bar risk-bar--empty"></div>
{% endif %}
```

```css
.risk-bar { display: flex; height: 8px; border-radius: 4px; overflow: hidden; gap: 1px; }
.risk-bar--empty { background: rgba(255,255,255,0.06); }
.risk-bar__seg { min-width: 4px; }
.risk-bar__legend { display: flex; gap: 16px; margin-top: 8px; flex-wrap: wrap; }
.risk-bar__legend-item { display: flex; align-items: center; gap: 5px; }
.risk-bar__swatch { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }
.risk-bar__legend-text {
  font-family: var(--font-mono); font-size: 11px;
  color: var(--text-muted); font-variant-numeric: tabular-nums;
}
```

### 7.12 Data table

**No vertical rules.** Horizontal `1px --border-hairline` between rows only.
Header row sits on `--surface-sunken` with a hairline bottom border. The table
lives inside a `.glass-card` with `overflow: hidden`.

Row hover: `rgba(255,255,255,0.03)` fill **plus** a `2px --accent-primary` left
edge on the first cell. The first cell's left padding drops from `24px` to `22px`
on hover so the 2px border does not shift the layout.

```css
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  padding: 10px 16px;
  text-align: left;
  font-family: var(--font-body);
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted);
  white-space: nowrap;
  background: var(--surface-sunken);
  border-bottom: 1px solid var(--border-hairline);
}
.data-table th.is-right, .data-table td.is-right { text-align: right; }
.data-table th.is-sortable { cursor: pointer; user-select: none; }
.data-table th.is-sorted { color: var(--accent-hover); }
.data-table th .sort-icon { font-size: 9px; opacity: 0.4; margin-left: 4px; }
.data-table th.is-sorted .sort-icon { opacity: 1; }

.data-table tbody tr { border-top: 1px solid var(--border-hairline); cursor: pointer; }
.data-table tbody tr:hover { background: rgba(255,255,255,0.03); }
.data-table tbody tr:hover td:first-child {
  border-left: 2px solid var(--accent-primary);
  padding-left: 22px;
}
.data-table td { padding: 12px 16px; }
.data-table td:first-child { padding-left: 24px; }
.data-table td:last-child { padding-right: 24px; }

.cell-title {
  font-family: var(--font-body); font-size: 13px; font-weight: 500;
  color: var(--text-primary);
  display: block; max-width: 260px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.cell-score {
  font-family: var(--font-mono); font-size: 14px; font-weight: 600;
  font-variant-numeric: tabular-nums;
}
```

Sort indicators: unsorted `⇅` at 40% opacity, ascending `▲`, descending `▼`.
Sortable headers carry `aria-sort="ascending|descending|none"`.

**Sorting is server-side.** Sortable headers are links to the same view with a
`?sort=` / `?dir=` query string, preserving existing filter params. If the current
view does not support sort params, render the headers as non-sortable rather than
adding view logic — flag it in the PR description as a follow-up.

Whole-row click navigates to the threat detail. Implement by wrapping the row in a
`data-href` attribute and a small JS delegate, and **also** make the title cell a
real `<a>` so keyboard and no-JS users can navigate.

### 7.13 Mobile card row

Replaces the table below 640px. Two lines:
- Line 1: threat title, 13px/500/20px, `--text-primary`
- Line 2: micro spine, score in mono 13px/600 in risk colour, risk pill (compact),
  status chip — all in a flex row with `gap: 10px`

Container: full-width `<a>`, `padding: 14px 20px`, `border-top: 1px solid var(--border-hairline)`,
`gap: 8px` column flex, left-aligned, no background.

### 7.14 Filter bar

Flex row, `gap: 10px`, `margin-bottom: 16px`, wrapping, `role="search"`.

- Search input: `flex: 1 1 200px`, `min-width: 160px`, with a `⌕` glyph absolutely
  positioned at `left: 10px`, vertically centred, `--text-disabled`, 12px,
  `pointer-events: none`; input gets `padding-left: 28px`.
- Status select: `flex: 0 0 160px`. Options: `All statuses`, `Open`, `Mitigated`,
  `Risk Accepted`, `False Positive`.
- Risk select: `flex: 0 0 150px`. Options: `All risk levels`, `Critical`, `High`,
  `Medium`, `Low`.
- Active filter chips: `padding: 3px 8px`, `background: rgba(59,130,246,0.1)`,
  `border: 1px solid rgba(59,130,246,0.25)`, `border-radius: 6px`, 12px,
  `--accent-hover`. The search term chip is wrapped in quotes.
- `Clear all` link: plain button, 12px, `--text-muted`, links to the bare view URL.
- Result count on the far right (`margin-left: auto`), mono 12px `--text-muted`,
  `aria-live="polite"`: `{n} result` / `{n} results`.

**This is a GET form.** Wrap the whole bar in `<form method="get">`, keep the
existing query parameter names the view already reads, and add a submit button
that is visually hidden but keyboard-reachable. Selects submit the form on change
via JS; without JS, the hidden submit still works.

### 7.15 Pagination

Top border `1px --border-hairline`, `padding: 14px 0`, flex, space-between.

Left: `{start}–{end} of {total}` in mono 12px `--text-muted`, tabular.
Right: `← Prev`, numbered pages, `Next →` — each a `6px`-radius button,
`padding: 5px 10px`, mono 12px/500.
- Inactive: `rgba(255,255,255,0.04)` bg, `--border-hairline` border, `--text-muted`
- Active: `--accent-primary` bg and border, `#fff` text
- Disabled: `--text-disabled`, `opacity: 0.4`, `cursor: not-allowed`

Use Django's `page_obj` / `paginator`. Preserve existing query params on every
page link. Per-page is **8** on the project detail threat table.

### 7.16 Navigation bar

Fixed, full width, `height: 56px`, `background: rgba(9,10,15,0.88)`,
`backdrop-filter: blur(20px)`, `border-bottom: 1px solid var(--border-hairline)`,
`z-index: 40`, `padding: 0 32px`, flex centred.

- **Logo** (left, `margin-right: 40px`): 24×26 shield SVG + wordmark. The wordmark
  is Space Grotesk 16px/600, `-0.01em`, with `.gradient-text`. Links to dashboard.
- **Links:** Dashboard, Projects. Each `padding: 5px 12px`, `border-radius: 6px`,
  13px/500, `--text-secondary`. Active: `background: rgba(59,130,246,0.12)`,
  colour `--accent-hover`. Projects is active on the project list, detail, and
  both project forms.
- **Avatar menu** (far right): `background: rgba(255,255,255,0.06)`,
  `border: 1px solid var(--border-hairline)`, `border-radius: 8px`,
  `padding: 5px 10px 5px 6px`, 13px/500. Contains a 26px circular avatar
  (`linear-gradient(135deg, #3b82f6, #8b5cf6)`, white initials at 11px/600),
  the username, and a 12px chevron at 50% opacity.
- **Dropdown:** `top: calc(100% + 6px)`, right-aligned, `background: rgba(14,17,28,0.97)`,
  `blur(20px)`, `border: 1px solid var(--border-strong)`, `border-radius: 10px`,
  `padding: 4px`, `min-width: 160px`, `box-shadow: var(--shadow-e2)`.
  Items: `padding: 8px 12px`, `border-radius: 6px`, 13px/500. `Profile`, then a
  `1px` hairline divider with `4px 0` margin, then `Log out` in `--risk-critical`.
  `aria-expanded` / `aria-haspopup="menu"` on the trigger; `role="menu"` on the panel.
  Close on outside click and on `Escape`.

**Log out must be a POST form**, not a link, for CSRF safety. Style the submit as
a `DropdownItem` and keep the label `Log out`.

Shield SVG (use verbatim, unique gradient `id` per instance):

```html
<svg width="24" height="26" viewBox="0 0 24 26" fill="none" aria-hidden="true">
  <path d="M12 1L2 5V13C2 18.5 6.5 23.3 12 25C17.5 23.3 22 18.5 22 13V5L12 1Z"
        fill="url(#shieldGradNav)" stroke="rgba(255,255,255,0.12)" stroke-width="0.5"/>
  <path d="M8 13l2.5 2.5L16 10" stroke="rgba(255,255,255,0.9)" stroke-width="1.5"
        stroke-linecap="round" stroke-linejoin="round"/>
  <defs>
    <linearGradient id="shieldGradNav" x1="2" y1="1" x2="22" y2="25" gradientUnits="userSpaceOnUse">
      <stop stop-color="#3B82F6"/><stop offset="0.5" stop-color="#8B5CF6"/><stop offset="1" stop-color="#EC4899"/>
    </linearGradient>
  </defs>
</svg>
```

### 7.17 Flash messages (Django `messages`)

Fixed at `top: 68px; right: 16px` (or `top: 16px` on auth pages), `z-index: 60`,
column flex, `gap: 8px`.

Each banner: `padding: 11px 14px`, `border-radius: 10px`, `min-width: 280px`,
`max-width: 420px`, `box-shadow: var(--shadow-e2)`, `backdrop-filter: blur(16px)`,
flex row with `gap: 10px`. Icon in mono 14px, message in body 13px/1.5
`--text-primary`, dismiss `✕` button in `--text-muted` at 14px.
`role="alert" aria-live="polite"`.

| Django tag | Background | Border | Colour | Icon |
|---|---|---|---|---|
| `success` | `rgba(34,211,165,0.1)` | `rgba(34,211,165,0.3)` | `#22D3A5` | `✓` |
| `error` | `rgba(255,61,113,0.1)` | `rgba(255,61,113,0.3)` | `#FF3D71` | `✕` |
| `warning` | `rgba(255,197,61,0.1)` | `rgba(255,197,61,0.3)` | `#FFC53D` | `⚠` |
| `info`/`debug` | `rgba(59,130,246,0.1)` | `rgba(59,130,246,0.3)` | `#60A5FA` | `ℹ` |

Auto-dismiss after **5000ms** via JS; the dismiss button removes it immediately.
Map Django's `message.tags` to these four classes.

### 7.18 Empty state

Centred column, `padding: 64px 32px`, `text-align: center`, `gap: 16px`.
**No decorative icon or illustration** — headline and action carry it.

- Headline: display 18px/600 `--text-primary`
- Guidance: body 14px/22px `--text-muted`, `max-width: 340px`, `margin-top: 6px`
- Action: a button

Always wrapped in a `.glass-card`.

### 7.19 Breadcrumb

`margin-bottom: 24px`, `<nav aria-label="Breadcrumb">` + `<ol>`, flex, `gap: 6px`,
no list markers. Separator `/` in `--text-disabled` 12px between items.
Links: 13px `--text-muted`. Current page: 13px/500 `--text-secondary` with
`aria-current="page"`.

### 7.20 Section heading

Flex row, `align-items: flex-start`, space-between, `gap: 16px`, `margin-bottom: 24px`.
Left: `h2` display 24px/32px/600, `-0.01em`; optional subtitle body 14px/22px
`--text-muted` at `margin-top: 4px`. Right: an action button.

---

## 8. Page specifications

Each page is described top to bottom in render order with exact spacing. Every page
except login/signup extends `base.html`.

### 8.0 `base.html` — the shell

```
<html lang="en">
  <head>
    charset, viewport, title block, threatscope.css
  </head>
  <body>
    <a class="skip-link" href="#main-content">Skip to main content</a>
    {% include "analysis/_nav.html" %}          ← only when user.is_authenticated
    {% include "analysis/_flash.html" %}
    <div class="page-shell" style="padding-top: 56px">   ← 0 on auth pages
      {% block content %}{% endblock %}
    </div>
    <script>…</script>
  </body>
</html>
```

Blocks to expose: `title`, `content`, `body_class`, `extra_js`.

### 8.1 Dashboard — `dashboard.html`

1. **Page header** — flex, space-between, `margin-bottom: 40px`, wraps, `gap: 16px`.
   - Left: `h1` display 28px/600 `-0.01em` — `Welcome back, {{ user.first_name|default:user.username }}.`
     Below it at `margin-top: 4px`, body 14px `--text-muted`:
     `{n} project{s} · {n} threat{s} tracked`.
     When empty: `You have no projects yet. Create one to start modelling threats.`
   - Right: `+ New project` — `.btn--primary .btn--md .btn--glow`. **This is the one
     glow on this screen.**
2. **`<main id="main-content">`** wraps everything below.
3. **Stat grid** — `.stat-grid`, `display: grid`, `grid-template-columns: repeat(4, 1fr)`,
   `gap: 16px`, `margin-bottom: 32px`. Cards in order:
   `Total Projects`, `Total Threats`, `Critical Risks`, `High Risks`.
   Critical card: value in `--risk-critical` when > 0, plus a delta
   `↑ {n} open` in `--risk-critical` 12px/500, `margin-bottom: 6px`.
   High card: value in `--risk-high` when > 0.
4. **Risk distribution** — `.glass-card`, `padding: 24px`, `margin-bottom: 32px`.
   Heading `Risk Distribution` as an `h2` in **display 14px/600, 0.08em, uppercase,
   `--text-muted`**, `margin-bottom: 16px`. Then the risk bar.
5. **Top threats card** — `.glass-card` with `overflow: hidden`.
   - Header strip: `padding: 20px 24px 16px`, `border-bottom: 1px solid var(--border-hairline)`,
     flex space-between. Left `h2` display 16px/600 `Top 5 Highest-Risk Threats`.
     Right `View all →` as `.btn--ghost .btn--sm` linking to the project list.
   - Table columns, in order: **Threat · Project · DREAD · Score (right) · Risk · Status**.
     Threat title `max-width: 280px` with ellipsis. Project name body 12px `--text-muted`.
     DREAD = micro spine. Score = mono 14px/600 in the risk colour, one decimal.
     Risk = compact risk pill. Status = status chip.
   - Sorted by score descending, sliced to 5. Compute in the view if not already.

**Empty dashboard** (0 projects and 0 threats): render the four stat cards showing
`0` at `opacity: 0.4` with `aria-hidden="true"`, then a `.glass-card` containing an
empty state:
- Headline: `No projects yet`
- Guidance: `Create your first project to start cataloguing threats and calculating DREAD scores.`
- Action: `+ Create first project` — `.btn--primary .btn--lg .btn--glow`

### 8.2 Projects list — `project_list.html`

1. Section heading: title `Projects`, subtitle
   `Each project represents a system or application being threat-modelled.`,
   action `+ New project` (`.btn--primary .btn--md`).
2. Card grid: `display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px;`
   with `role="list"` and `aria-label="Projects"`.
3. **Project card** — `.glass-card`, `padding: 0`, `overflow: hidden`,
   `role="listitem"`, focusable (`tabindex="0"`), keyboard-activatable on
   Enter/Space, `transition: box-shadow 200ms cubic-bezier(0.2,0,0,1), border-color 200ms`.
   `aria-label`: `Project: {name}. {n} threats. Highest score: {x.x}.`
   - **Top colour bar:** `height: 3px`, background = risk colour of the project's
     highest-scoring threat; `rgba(255,255,255,0.06)` when the project has no threats.
   - Body: `padding: 20px 24px 24px`.
     - `h3` display 16px/600 `--text-primary`, `margin-bottom: 4px`.
     - Description: body 13px/20px `--text-muted`, clamped to **2 lines**
       (`display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden`).
     - `margin-bottom: 14px` after the title block.
     - Mini risk bar (only when the project has threats), `margin-bottom: 16px`.
     - Metrics row: flex space-between, `gap: 12px`.
       Left group `gap: 16px`: `THREATS` (count, body 16px/600 `--text-secondary`)
       and `HIGHEST` (max score to one decimal, mono 16px/600 in the risk colour).
       Metric labels: body 11px/600, `0.1em`, uppercase, `--text-disabled`,
       `margin-bottom: 2px`.
       Right: last-updated date, mono 11px `--text-disabled`, formatted
       `{{ project.updated_at|date:"M j, Y" }}`.

**Empty:** `.glass-card` + empty state — headline `No projects yet`, guidance
`Create a project for each system you want to threat-model. A project owns all its threats and DREAD scores.`,
action `+ Create first project`.

Views must supply per-project `threat_count`, `max_score`, and `risk_counts`.
Prefer annotating the existing queryset over adding N+1 queries in the template.

### 8.3 Project detail — `project_detail.html`

1. **Breadcrumb:** `Projects / {project name}`.
2. **Project header** — flex, `align-items: flex-start`, space-between, `gap: 24px`,
   `margin-bottom: 32px`, wraps.
   - Left: `h1` display 28px/600 `-0.01em`, `margin-bottom: 6px`. Description body
     14px/22px `--text-muted`, `max-width: 600px`. Then `margin-top: 8px`, mono 11px
     `--text-disabled`: `Created {date} · Updated {date}`.
   - Right: button row `gap: 8px`, wrapping — `Edit` (`.btn--ghost .btn--sm`),
     `Export CSV` (`.btn--secondary .btn--sm`, `aria-label="Export project as CSV"`),
     `Delete` (`.btn--danger .btn--sm`).
3. **Risk summary** (only when threats exist) — `.glass-card`, `padding: 20px 24px`,
   `margin-bottom: 24px`. Eyebrow `Risk Summary` (11px/600, `0.1em`, uppercase,
   `--text-muted`), `margin-bottom: 12px`, then the risk bar.
4. **Section heading:** `Threats ({{ total }})` with action `+ Add threat`
   (`.btn--primary .btn--md`).
5. **Filter bar** (§7.14).
6. **Threats table** — inside `.glass-card` with `overflow: hidden`.
   Columns in order: **Threat · DREAD · Score (right) · Risk · STRIDE · Status ·
   Updated · Actions**.
   - Threat title `max-width: 260px`, ellipsis.
   - Sortable: Threat (title), Score, Status. Default sort: Score descending.
   - STRIDE cell shows `—` in `--text-disabled` 12px when unset.
   - Updated: mono 11px `--text-disabled`.
   - Actions cell: `Edit` as `.btn--ghost .btn--sm` with
     `aria-label="Edit {{ threat.title }}"`. Header for this column is
     `<span class="sr-only">Actions</span>`. Clicking the action must not trigger
     the row navigation.
   - Mobile card list rendered alongside, hidden above 640px.
   - Pagination at `padding: 0 24px`, **8 per page**.
7. **Two distinct empty states:**
   - No threats at all: headline `No threats yet`, guidance
     `Add your first threat to start scoring risk with DREAD. Real examples: session fixation, injection endpoints, broken access control.`,
     action `+ Add first threat` (`.btn--primary .btn--md`).
   - Filters match nothing: headline `No results for these filters`, guidance
     `Try adjusting the search term, status, or risk level filter.`,
     action `Clear filters` (`.btn--secondary .btn--sm`).

**Export CSV** keeps its existing URL and response. Show a loading spinner on the
button for the duration of the request, and emit a Django success message
`CSV export ready. Download started.` if the view already redirects; if it streams
the file directly, skip the message rather than adding view logic.

### 8.4 Threat detail — `threat_detail.html`

1. **Breadcrumb:** `Projects / {project} / Threat detail`.
2. **Meta header** — flex, `align-items: flex-start`, space-between, `gap: 24px`,
   `margin-bottom: 32px`, wraps.
   - Left: chips row (`gap: 8px`, wraps, `margin-bottom: 12px`) — full-size risk
     pill, status chip, STRIDE tag (if set). Then `h1` display 28px/36px/600
     `-0.01em`. Then `margin-top: 6px`, mono 11px `--text-disabled`:
     `Created {date} · Updated {date}`.
   - Right: `Edit threat` (`.btn--secondary .btn--sm`), `Delete` (`.btn--danger .btn--sm`).
3. **Hero card** — `.glass-card`, `padding: 32px 32px 24px`, `margin-bottom: 32px`.
   - Score row: flex, `align-items: flex-end`, `gap: 24px`, `margin-bottom: 32px`.
     - Eyebrow `DREAD SCORE` (11px/600, `0.12em`, uppercase, `--text-muted`,
       `margin-bottom: 4px`), then the score in **mono 56px/600, `-0.02em`**, in the
       risk colour, one decimal. `aria-label="DREAD score: {x.x} out of 10"`.
     - `/10` in mono 16px `--text-muted`, `margin-bottom: 10px`.
     - Factor breakdown at `margin-left: 8px`, `margin-bottom: 8px`, `gap: 16px`:
       five centred columns, each the value in mono 20px/600 `--text-secondary`
       above the letter in mono 10px `--text-disabled` with `0.06em` tracking and
       `margin-top: 4px`. `title="{Factor}: {v}/10"` on each value.
   - **Hero DREAD Spine** (§7.7) directly below.
4. **Content grid** — `.threat-detail-grid`, `display: grid`,
   `grid-template-columns: 1fr 280px`, `gap: 24px`, `align-items: start`.
   - **Left column**, column flex `gap: 24px`:
     - `<section>` `.glass-card` `padding: 24px 32px`, `aria-labelledby="desc-heading"`.
       Eyebrow `h2#desc-heading` = `Description`, `margin-bottom: 14px`.
       Body `.prose` (15px/26px, `--text-secondary`, `max-width: 72ch`).
     - Same structure for `Mitigation Plan` (`#mitigation-heading`). When empty,
       render `<em style="color: var(--text-disabled)">No mitigation recorded. Add one when editing this threat.</em>`.
     - Use `{{ value|linebreaks }}` so multi-paragraph text renders correctly.
   - **Right rail** — `<aside aria-label="Threat metadata">`, column flex `gap: 12px`.
     `.glass-card` `padding: 20px`. Heading `Details` (11px/600, `0.1em`, uppercase,
     `--text-muted`, `margin-bottom: 16px`). Rows at `gap: 14px`, each with a label
     (body 11px/600, `0.08em`, uppercase, `--text-disabled`, `margin-bottom: 4px`)
     above its value:
     `Project` (link, 13px/500 `--accent-hover`) · `Status` (chip) · `Risk` (compact
     pill) · `STRIDE` (tag, only if set) · `Created` (mono 12px `--text-secondary`) ·
     `Updated` (mono 12px `--text-secondary`).

### 8.5 Threat form — `threat_form.html`

1. Breadcrumb: `Projects / {project} / Add threat` (or `Edit threat`).
2. Section heading: `Add threat` / `Edit threat`, subtitle
   `Catalogue a threat against {project}.` / `Update a threat against {project}.`
3. `<form method="post" class="threat-form-grid">` with
   `display: grid; grid-template-columns: 1fr 360px; gap: 24px; align-items: start;`
   and `{% csrf_token %}` first.
4. **Left column**, column flex `gap: 20px`:
   - Form error summary (§7.3).
   - **Threat details card** — `.glass-card` `padding: 24px`. Eyebrow
     `Threat details`, `margin-bottom: 18px`. Fields at `gap: 16px`:
     - `Threat title` — required, `maxlength=200`, placeholder
       `e.g. Session token exposed in URL parameters`
     - `Description` — required, 4 rows, hint
       `Describe the vulnerability, its root cause, and how it could be exploited.`,
       placeholder `e.g. The /admin/export endpoint does not verify session state. An unauthenticated user can retrieve all project data by guessing the URL.`
     - `Mitigation plan` — optional, 4 rows, hint
       `How should this threat be addressed? Include specific steps.`, placeholder
       `e.g. Add @login_required decorator to the export view. Add an integration test asserting 302 redirect for anonymous requests.`
     - Two-column sub-grid (`1fr 1fr`, `gap: 16px`): `STRIDE category` (first option
       `— None —`) and `Status` (required).
   - **DREAD Ratings card** — `.glass-card` `padding: 24px`. Eyebrow `DREAD Ratings`,
     `margin-bottom: 20px`. Five rating controls (§7.8) at `gap: 20px`, separated by
     `1px` hairline dividers, in order Damage → Reproducibility → Exploitability →
     Affected Users → Discoverability. Default value **5** for new threats.
   - **Actions** — flex, `gap: 8px`, right-aligned: `Cancel` (`.btn--secondary .btn--md`,
     link back), then submit `Add threat` / `Save changes` (`.btn--primary .btn--md`).
5. **Right column** — `.score-preview-sticky`, `position: sticky; top: 80px;`.
   Live score preview (§7.9) with `margin-bottom: 12px`, then the DREAD Scale
   reference card.

**Validation copy** (match the design, but only where the Django form already
enforces the same rule — do not add new validators):
- `Threat title is required.`
- `Title must be 200 characters or fewer.`
- `Description is required.`

### 8.6 Project form — `project_form.html`

Breadcrumb `Projects / New project` (or `Edit project`). Section heading
`New project` / `Edit "{name}"`, subtitle
`A project represents a system or application you are threat-modelling.`

`<form>` with `max-width: 600px`, containing one `.glass-card` at `padding: 28px`,
fields at `gap: 18px`: error summary, `Project name` (required, `maxlength=120`,
placeholder `e.g. Payment Gateway API`), `Description` (required, 4 rows, hint
`Briefly describe the system, its purpose, and any context useful for threat modelling.`,
placeholder `e.g. REST API handling payment processing, refunds, and transaction history. Integrates with Stripe and handles PCI-DSS sensitive data flows.`).

Actions right-aligned at `padding-top: 4px`, `gap: 8px`: `Cancel`, then
`Create project` / `Save changes`.

### 8.7 Delete confirmation — `confirm_delete.html`

Centred, `max-width: 520px`, `margin: 0 auto`, `padding-top: 32px`.
`.glass-card` at `padding: 32px` with `border: 1px solid rgba(255,61,113,0.2)`.

1. Warning tile: `48×48`, `border-radius: 12px`, `background: rgba(255,61,113,0.1)`,
   `border: 1px solid rgba(255,61,113,0.25)`, centred `⚠` at 22px, `margin-bottom: 20px`.
2. `h1` display 22px/600 in `--risk-critical`: `Delete Project?` / `Delete Threat?`
3. Body 14px/22px `--text-secondary`, `margin-bottom: 16px`:
   `You are about to permanently delete <strong>{name}</strong>.`
   For projects with threats, append: `This also deletes {n} associated threat{s}.`
   Always end with: `This action cannot be undone.`
   The `<strong>` is `--text-primary`.
4. Confirm instruction box: `background: rgba(255,61,113,0.06)`,
   `border: 1px solid rgba(255,61,113,0.15)`, `border-radius: 8px`,
   `padding: 12px 14px`, `margin-bottom: 20px`, 13px `--text-muted`:
   `Type {name} to confirm.` with the name in mono 12px `--text-primary`.
5. Text input, `margin-bottom: 20px`, placeholder `Type "{name}" to confirm`,
   `aria-label="Type {name} to confirm deletion"`.
6. Actions right-aligned, `gap: 8px`: `Cancel` (`.btn--secondary .btn--md`),
   `Delete project` / `Delete threat` (`.btn--danger .btn--md`), **disabled until
   the typed text exactly matches the object name**.

The delete button lives in a POST form with `{% csrf_token %}` pointing at the
existing delete URL. The type-to-confirm gate is client-side only — do not add
server-side confirmation validation.

### 8.8 Login / Signup — `login.html`, `signup.html`

Full-height split, no nav bar.
`min-height: 100vh; display: flex; background: linear-gradient(135deg, var(--surface-base) 0%, var(--surface-base2) 100%);`

**Left panel** — `.auth-form-panel`, `width: 100%`, `max-width: 460px`, column flex,
vertically centred, `padding: 48px`, `border-right: 1px solid var(--border-hairline)`.

1. Logo lockup: 28×30 shield + `ThreatScope` in `.gradient-text` display 20px/600,
   `gap: 10px`, `margin-bottom: 48px`.
2. `h1` display 28px/600: `Sign in to your account` / `Create your account`,
   `margin-bottom: 6px`. Subtitle body 14px/22px `--text-muted`:
   `Your threat models are waiting.` / `Start cataloguing threats in seconds.`
   Block has `margin-bottom: 32px`.
3. Form, fields at `gap: 18px`: error summary, then (signup only) `Full name`,
   then `Email address` (placeholder `you@example.com`), then `Password`
   (signup hint `At least 8 characters.`). Set correct `autocomplete` attributes:
   `name`, `email`, `current-password` / `new-password`.
4. Submit: full-width `.btn--primary .btn--lg`, `margin-top: 4px`,
   `Sign in` / `Create account`.
5. Footer line at `margin-top: 24px`, centred, 13px `--text-muted`:
   `No account yet? Sign up` / `Already have an account? Sign in`, with the link in
   `--accent-hover` 13px/500.

> **Field names must match the existing Django auth form.** If the project uses
> `username` rather than `email`, keep `username` and relabel only if the model
> genuinely stores an email. Do not change authentication behaviour.

**Right panel** — `.auth-split-right`, `flex: 1`,
`background: linear-gradient(150deg, var(--surface-base2) 0%, #111828 100%)`,
centred, `overflow: hidden`, hidden below 640px. Content at `padding: 48px 40px`,
column flex, `gap: 36px`:

1. Headline, display 32px/40px/600 `-0.01em`, `margin-bottom: 8px`, two lines:
   `Every threat has` / `a fingerprint.`
   Paragraph 14px/22px `--text-muted`:
   `DREAD scoring reveals the shape of risk, not just its level. Two threats with the same score can demand entirely different responses.`
2. Three demo spines at `gap: 20px`, each a flex row with `gap: 16px`:
   columns `height: 100px`, `gap: 4px`, `border-radius: 3px`, track
   `rgba(255,255,255,0.04)`, fill at the level colour with `90` alpha suffix.
   Right of each, a `72px` fixed block: score in mono 20px/600 in the level colour,
   then the level name in body 11px/600, `0.1em`, uppercase, same colour at
   `opacity: 0.7`, `margin-top: 2px`.

   | Profile | D R E A D | Score | Level |
   |---|---|---|---|
   | 1 | 9, 10, 9, 10, 7 | 9.0 | Critical `#FF3D71` |
   | 2 | 7, 5, 8, 6, 9 | 7.0 | High `#FF8A3D` |
   | 3 | 4, 6, 3, 5, 2 | 4.0 | Medium `#FFC53D` |

3. Letter row `D R E A D` at `gap: 8px`, `margin-top: 4px`, mono 10px/600,
   `0.1em`, `--text-disabled`, each `flex: 1` centred, followed by a `72px` spacer
   so the letters align with the columns above.

This panel is static decoration — hard-code it in the template.

### 8.9 Error pages — `404.html`, `500.html`

Centred column, `min-height: 60vh`, `gap: 20px`, `text-align: center`.

1. Giant numeral, mono 96px/600, `user-select: none`, `aria-hidden="true"`:
   404 → `rgba(255,255,255,0.04)` · 500 → `rgba(255,61,113,0.07)`
2. Text block at `margin-top: -32px`: `h1` display 28px/600 —
   `Page not found` / `Server error`, `margin-bottom: 8px`. Body 14px `--text-muted`:
   - 404: `That URL does not exist. Check the address or navigate back.`
   - 500: `Something went wrong on our end. The error has been logged. Try again in a moment.`
3. Actions: 404 → `Back to dashboard` (`.btn--primary .btn--md`).
   500 → `Retry` (`.btn--secondary .btn--md`) + `Back to dashboard` (`.btn--primary .btn--md`).

Place these at `templates/404.html` and `templates/500.html`. They render only when
`DEBUG = False`; test with `DEBUG=False` and `ALLOWED_HOSTS=['*']` locally.
`500.html` must not use context processors or template tags that touch the
database — keep it static, and do **not** `{% load threatscope %}` in it.

---

## 9. Restraint rules — enforce these during review

These are what keep the build from reading as generic AI output. Violating one is
a review blocker.

1. **Glass appears on at most two surface levels.** `.glass-card` never nests inside
   another `.glass-card`. Table rows, inputs, badges, and chips are never glass.
2. **One glow per screen.** `.btn--glow` appears at most once per rendered page. On
   the dashboard it is the `+ New project` CTA. Nowhere else.
3. **Gradient text once per screen.** The nav wordmark uses it. Nothing else on that
   screen may. On auth pages the logo lockup uses it instead.
4. **No floating orbs, mesh gradients, or blurred colour blobs.** The 32px hairline
   grid is the only background texture.
5. **Border radius stays on the scale** — 8 / 12 / 16, plus the specific exceptions
   already listed (pills 20, chips and small buttons 6, spine segments 1–4).
6. **No drop shadows on text. No pure `#FFFFFF` or `#000000`. No centred long
   paragraphs.** Prose is left-aligned and capped at 72ch.
7. **No invented features.** No AI assistant, no notification centre, no team
   collaboration UI, no real-time feed, no dark/light toggle.
8. **No stock illustrations or security clip-art** — no padlocks, hooded figures,
   or binary rain. Empty states have no icon.
9. **Risk is never colour-only.** Every risk indicator carries its text label and a
   glyph. Verify by screenshotting in greyscale.

---

## 10. Accessibility requirements

- **WCAG 2.2 AA.** Body text ≥ 4.5:1, large text and UI borders ≥ 3:1, measured
  against the composited glass surface, not flat `#090A0F`.
- `--text-muted` (`#94A3B8`) is the dimmest colour permitted to carry meaning.
  `--text-disabled` is decorative or non-essential only.
- Visible focus ring on every interactive element: `2px solid var(--border-focus)`
  at `2px` offset. Never remove an outline without replacing it.
- Skip-to-content link on every page, first focusable element.
- Semantic landmarks: `<header role="banner">`, `<nav role="navigation">`,
  `<main id="main-content">`, `<aside>` for the metadata rail.
- One `<h1>` per page. Heading levels never skip.
- Tables use `<th scope="col">`, `aria-sort` on sortable headers, and a table
  `aria-label`.
- Icon-only buttons carry `aria-label`. Decorative SVG and glyphs carry
  `aria-hidden="true"`.
- The rating control exposes `role="slider"` with `aria-valuemin="1"`,
  `aria-valuemax="10"`, `aria-valuenow`, and a descriptive `aria-label`.
- Live regions: `aria-live="polite"` on the score preview, the filter result count,
  and the flash message container.
- Touch targets ≥ 44×44px on mobile — increase button padding under the 640px
  breakpoint where needed.
- All motion respects `prefers-reduced-motion` via the global override.
- Every interactive element must work without JavaScript, or degrade to a working
  server-rendered equivalent. Row-click navigation has a real `<a>` fallback;
  the rating strip has a number-input fallback; the filter bar has a submit button.

---

## 11. Verification checklist

Run through this before opening the PR. Every item must pass.

**Functionality (nothing broken)**
- [ ] Sign up, log in, log out all work
- [ ] Create, edit, delete a project
- [ ] Create, edit, delete a threat; DREAD score and risk level recalculate correctly
- [ ] Search, status filter, and risk filter all still return the correct rows
- [ ] Filters combine correctly and survive pagination
- [ ] CSV export downloads with the same columns as before
- [ ] Django admin still renders
- [ ] A second user cannot see the first user's projects
- [ ] `python manage.py check` passes with no new warnings
- [ ] No migrations were generated (`makemigrations --check --dry-run` is clean)

**Form behaviour under Django's full re-render**
- [ ] Submitting an invalid threat form re-renders with the error summary at the top
- [ ] Field-level errors appear below the correct fields with the red border
- [ ] Previously entered values are preserved after a failed POST
- [ ] DREAD ratings are preserved after a failed POST (hidden inputs repopulate)
- [ ] All four Django message levels render as the correct banner colour

**Design fidelity**
- [ ] Every colour in the rendered page traces to a `:root` token
- [ ] No off-8pt-grid spacing values
- [ ] Exactly one `.btn--glow` per page
- [ ] Exactly one gradient-text element per page
- [ ] No nested `.glass-card`
- [ ] Scores always display one decimal place
- [ ] All numerals use JetBrains Mono with tabular figures and align in columns
- [ ] The DREAD Spine appears at all three scales, with per-factor colours
- [ ] The risk bar order is always Critical → High → Medium → Low

**Responsive**
- [ ] At 375px: stat cards go 2-up, tables become card rows, the auth visual panel
      is hidden, the threat detail collapses to one column
- [ ] No horizontal scroll at any width between 320px and 1920px
- [ ] The sticky score preview becomes static on mobile

**Accessibility**
- [ ] Tab through every page — focus is always visible and the order is logical
- [ ] Keyboard-only: create a threat end to end, including setting all five ratings
- [ ] Screenshot in greyscale — risk level is still distinguishable everywhere
- [ ] Run axe DevTools or Lighthouse; resolve all critical and serious issues
- [ ] Lighthouse accessibility score ≥ 95

**Cross-browser**
- [ ] Chrome, Firefox, Safari — `backdrop-filter` degrades gracefully in Firefox
      (the `--surface-raised` fill alone must still read as a card)

---

## 12. Delivery workflow

```bash
git checkout -b feat/ui-overhaul

# commit in reviewable chunks:
#   1. chore: add design tokens and base stylesheet
#   2. feat: add threatscope templatetags
#   3. feat: rebuild base shell, nav, and flash messages
#   4. feat: rebuild dashboard and project list
#   5. feat: rebuild project detail and threat table
#   6. feat: rebuild threat detail with DREAD spine
#   7. feat: rebuild forms and rating control
#   8. feat: rebuild auth, delete confirm, and error pages
#   9. fix: responsive and accessibility passes

python manage.py runserver   # verify every checklist item above
git push -u origin feat/ui-overhaul
```

**PR description must include:**
- Before/after screenshots of the dashboard, project detail, threat detail, and
  threat form, at both 1280px and 375px
- A statement that no models, views, URLs, or form fields were changed
- The verification checklist with every box ticked
- Any item you could not implement without a view change, listed as a follow-up

Squash merge, delete the branch after merge.
