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
    if not isinstance(counts, dict):
        counts = {}
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
