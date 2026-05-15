from __future__ import annotations

import streamlit as st


# =========================================================
# DESIGN TOKENS
# =========================================================

COLORS = {
    "bg": "#0E1117",
    "card": "#161B22",
    "card_alt": "#1C2330",
    "text": "#E6EDF3",
    "muted": "#9DA7B3",
    "primary": "#4F8CFF",
    "green": "#2ECC71",
    "red": "#E74C3C",
    "yellow": "#F1C40F",
}

SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
}

RADIUS = {
    "sm": "10px",
    "md": "14px",
    "lg": "18px",
}


# =========================================================
# GLOBAL CSS (MOBILE FIRST)
# =========================================================

def inject_global_css():
    st.markdown(
        f"""
        <style>

        html, body {{
            background-color: {COLORS["bg"]};
            color: {COLORS["text"]};
        }}

        /* Main container */
        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }}

        /* Cards */
        .card {{
            background: {COLORS["card"]};
            padding: 16px;
            border-radius: {RADIUS["md"]};
            border: 1px solid rgba(255,255,255,0.05);
        }}

        .card:hover {{
            border-color: rgba(79,140,255,0.4);
            transition: 0.2s ease;
        }}

        /* KPI cards */
        .kpi-card {{
            background: linear-gradient(135deg, {COLORS["card"]}, {COLORS["card_alt"]});
            padding: 16px;
            border-radius: {RADIUS["lg"]};
            text-align: center;
        }}

        .kpi-value {{
            font-size: 26px;
            font-weight: 700;
            margin-top: 6px;
        }}

        .kpi-label {{
            font-size: 12px;
            color: {COLORS["muted"]};
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .kpi-delta {{
            font-size: 12px;
            margin-top: 6px;
        }}

        /* Section */
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 12px;
            color: {COLORS["text"]};
        }}

        /* Pills */
        .pill {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            background: rgba(79,140,255,0.15);
            color: {COLORS["primary"]};
        }}

        /* Insight row */
        .insight-row {{
            background: {COLORS["card"]};
            padding: 10px 12px;
            border-radius: 12px;
            margin-bottom: 8px;
        }}

        .insight-main {{
            font-weight: 600;
        }}

        .insight-sub {{
            font-size: 12px;
            color: {COLORS["muted"]};
        }}

        /* Empty state */
        .big-empty {{
            padding: 40px;
            text-align: center;
            color: {COLORS["muted"]};
            border: 1px dashed rgba(255,255,255,0.1);
            border-radius: 12px;
        }}

        /* MOBILE RESPONSIVE */
        @media (max-width: 768px) {{
            .block-container {{
                padding-left: 12px;
                padding-right: 12px;
            }}

            .kpi-value {{
                font-size: 22px;
            }}

            .kpi-card {{
                padding: 12px;
            }}

            .card {{
                padding: 12px;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# COMPONENTS
# =========================================================

def card_html(title: str, value: str, subtitle: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta">{subtitle}</div>
    </div>
    """


def mini_stat_html(title: str, value: str, subtitle: str = "") -> str:
    return f"""
    <div class="card">
        <div class="kpi-label">{title}</div>
        <div style="font-size:18px;font-weight:600;margin-top:4px;">{value}</div>
        <div class="insight-sub">{subtitle}</div>
    </div>
    """


def section_open(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="margin-top:18px;margin-bottom:10px;">
            <div class="section-title">{title}</div>
            <div class="insight-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_close():
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


def render_header():
    st.markdown(
        """
        <div style="padding:10px 0 20px 0;">
            <h2 style="margin:0;">🚴 Strava Dashboard</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# Retrocompatibilità con moduli esistenti
# ---------------------------------------------------------

ACCENT = COLORS["primary"]
GREEN = COLORS["green"]
PANEL = COLORS["card"]
TEXT = COLORS["text"]

def sport_color_map(sports=None):
    base = {
        "Ride": "#4F8CFF",
        "VirtualRide": "#8B5CF6",
        "Run": "#2ECC71",
        "Walk": "#F1C40F",
        "Hike": "#E67E22",
        "Workout": "#E74C3C",
    }

    if sports is None:
        return base

    return {sport: base.get(sport, "#9DA7B3") for sport in sports}
