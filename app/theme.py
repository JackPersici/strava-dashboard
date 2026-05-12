from __future__ import annotations

import html
import streamlit as st


# =========================================================
# DESIGN TOKENS - Strava personal dashboard
# =========================================================

COLORS = {
    "bg": "#07111F",
    "bg_alt": "#0A1424",
    "panel": "#0E1A2B",
    "panel_2": "#121F33",
    "panel_3": "#17263C",
    "border": "rgba(255,255,255,0.08)",
    "border_soft": "rgba(255,255,255,0.05)",
    "text": "#F4F7FB",
    "text_soft": "#D7E1EE",
    "muted": "#8EA0B8",
    "muted_2": "#64748B",
    "accent": "#FC4C02",
    "accent_2": "#FF8A3D",
    "blue": "#7DB7FF",
    "green": "#22C55E",
    "red": "#EF4444",
    "yellow": "#F59E0B",
    "purple": "#8B5CF6",
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
    "md": "16px",
    "lg": "22px",
    "xl": "28px",
}


# =========================================================
# GLOBAL CSS
# =========================================================

def inject_global_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --sd-bg: {COLORS['bg']};
            --sd-panel: {COLORS['panel']};
            --sd-panel-2: {COLORS['panel_2']};
            --sd-text: {COLORS['text']};
            --sd-muted: {COLORS['muted']};
            --sd-accent: {COLORS['accent']};
            --sd-border: {COLORS['border']};
        }}

        html, body, .stApp {{
            background:
                radial-gradient(circle at top left, rgba(252,76,2,0.16), transparent 30rem),
                radial-gradient(circle at top right, rgba(125,183,255,0.10), transparent 28rem),
                linear-gradient(180deg, {COLORS['bg']} 0%, {COLORS['bg_alt']} 100%) !important;
            color: {COLORS['text']} !important;
        }}

        .block-container {{
            max-width: 1240px;
            padding-top: 1.1rem;
            padding-bottom: 3rem;
        }}

        header[data-testid="stHeader"] {{ background: transparent !important; }}
        footer {{ visibility: hidden; }}

        /* Streamlit widgets */
        div[data-baseweb="select"] > div {{
            background: rgba(14,26,43,0.92) !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 14px !important;
            color: {COLORS['text']} !important;
            min-height: 44px;
        }}
        div[data-baseweb="select"] span {{ color: {COLORS['text_soft']} !important; }}
        .stMultiSelect label, .stSelectbox label {{
            color: {COLORS['muted']} !important;
            font-size: 0.78rem !important;
            letter-spacing: .02em;
        }}

        /* Tabs */
        button[data-baseweb="tab"] {{
            color: {COLORS['muted']} !important;
            padding-left: 0 !important;
            padding-right: 22px !important;
            font-weight: 600 !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {COLORS['accent']} !important;
        }}
        div[data-baseweb="tab-highlight"] {{
            background-color: {COLORS['accent']} !important;
            height: 3px !important;
            border-radius: 999px !important;
        }}
        div[data-baseweb="tab-border"] {{ background-color: {COLORS['border']} !important; }}

        /* Native metrics still used in secondary pages */
        div[data-testid="stMetric"] {{
            background: linear-gradient(145deg, rgba(18,31,51,0.96), rgba(10,20,36,0.98));
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['lg']};
            padding: 16px 18px;
            box-shadow: 0 18px 45px rgba(0,0,0,0.22);
        }}
        div[data-testid="stMetricLabel"] {{ color: {COLORS['muted']} !important; }}
        div[data-testid="stMetricValue"] {{ color: {COLORS['text']} !important; }}

        /* Reusable components */
        .sd-hero {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 20px 22px;
            margin: 4px 0 20px 0;
            border-radius: {RADIUS['xl']};
            border: 1px solid {COLORS['border']};
            background:
                linear-gradient(135deg, rgba(252,76,2,0.20), rgba(18,31,51,0.94) 38%, rgba(14,26,43,0.96));
            box-shadow: 0 22px 70px rgba(0,0,0,0.28);
        }}
        .sd-hero-eyebrow {{
            color: {COLORS['accent_2']};
            font-size: .75rem;
            font-weight: 800;
            letter-spacing: .16em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .sd-hero-title {{
            color: {COLORS['text']};
            font-size: clamp(1.6rem, 3vw, 2.35rem);
            line-height: 1.05;
            font-weight: 850;
            margin: 0;
        }}
        .sd-hero-subtitle {{
            color: {COLORS['muted']};
            font-size: .92rem;
            margin-top: 8px;
        }}
        .sd-hero-badges {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }}
        .sd-pill, .pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 11px;
            border-radius: 999px;
            font-size: .78rem;
            font-weight: 700;
            border: 1px solid rgba(252,76,2,0.30);
            background: rgba(252,76,2,0.12);
            color: #FFB084;
        }}
        .sd-pill.secondary {{
            border-color: {COLORS['border']};
            background: rgba(255,255,255,0.05);
            color: {COLORS['text_soft']};
        }}

        .kpi-card {{
            position: relative;
            overflow: hidden;
            min-height: 116px;
            padding: 18px 18px 16px;
            border-radius: {RADIUS['lg']};
            border: 1px solid {COLORS['border']};
            background:
                radial-gradient(circle at 85% 15%, rgba(252,76,2,0.16), transparent 9rem),
                linear-gradient(145deg, rgba(18,31,51,0.98), rgba(9,18,32,0.98));
            box-shadow: 0 20px 55px rgba(0,0,0,0.27);
        }}
        .kpi-card::after {{
            content: "";
            position: absolute;
            left: 18px; right: 18px; bottom: 0;
            height: 3px;
            border-radius: 999px 999px 0 0;
            background: linear-gradient(90deg, {COLORS['accent']}, rgba(252,76,2,0));
            opacity: .75;
        }}
        .kpi-label {{
            color: {COLORS['muted']};
            font-size: .72rem;
            text-transform: uppercase;
            letter-spacing: .14em;
            font-weight: 800;
        }}
        .kpi-value {{
            color: {COLORS['text']};
            font-size: clamp(1.55rem, 2.2vw, 2.15rem);
            font-weight: 850;
            letter-spacing: -0.04em;
            margin-top: 12px;
        }}
        .kpi-delta {{
            margin-top: 8px;
            color: {COLORS['muted']};
            font-size: .78rem;
            font-weight: 650;
        }}
        .kpi-delta.positive {{ color: #86EFAC; }}
        .kpi-delta.negative {{ color: #FDA4AF; }}

        .sd-section-title {{
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 12px;
            margin: 24px 0 10px;
        }}
        .sd-section-title h3 {{
            color: {COLORS['text']};
            font-size: 1.02rem;
            font-weight: 800;
            margin: 0;
        }}
        .sd-section-title p {{
            color: {COLORS['muted']};
            font-size: .82rem;
            margin: 4px 0 0;
        }}

        .card, .sd-card {{
            background: linear-gradient(145deg, rgba(18,31,51,0.96), rgba(10,20,36,0.98));
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['lg']};
            padding: 16px;
            box-shadow: 0 20px 55px rgba(0,0,0,0.22);
        }}
        .mini-stat, .insight-row {{
            background: linear-gradient(145deg, rgba(18,31,51,0.98), rgba(11,21,36,0.98));
            border: 1px solid {COLORS['border_soft']};
            border-radius: 18px;
            padding: 15px 16px;
            margin-bottom: 10px;
        }}
        .mini-label {{
            color: {COLORS['muted']};
            font-size: .70rem;
            letter-spacing: .13em;
            text-transform: uppercase;
            font-weight: 800;
        }}
        .mini-value, .insight-main {{
            color: {COLORS['text']};
            font-size: 1.08rem;
            font-weight: 800;
            margin-top: 7px;
        }}
        .mini-sub, .insight-sub {{
            color: {COLORS['muted']};
            font-size: .78rem;
            margin-top: 5px;
        }}

        .big-empty {{
            min-height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: {COLORS['muted']};
            border: 1px dashed rgba(255,255,255,0.14);
            border-radius: {RADIUS['lg']};
            background: rgba(255,255,255,0.03);
        }}

        .table-wrap {{
            overflow: auto;
            border-radius: 16px;
            border: 1px solid {COLORS['border']};
        }}
        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            color: {COLORS['text_soft']};
            background: rgba(14,26,43,0.92);
        }}
        table.data-table th {{
            background: rgba(255,255,255,0.04);
            color: {COLORS['text']};
            font-size: .78rem;
            text-transform: uppercase;
            letter-spacing: .08em;
            padding: 12px;
        }}
        table.data-table td {{
            border-top: 1px solid {COLORS['border_soft']};
            padding: 12px;
        }}

        @media (max-width: 768px) {{
            .block-container {{ padding-left: 12px; padding-right: 12px; }}
            .sd-hero {{ align-items: flex-start; flex-direction: column; padding: 18px; }}
            .sd-hero-badges {{ justify-content: flex-start; }}
            .kpi-card {{ min-height: 104px; padding: 15px; }}
            .sd-section-title {{ align-items: flex-start; flex-direction: column; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# COMPONENTS
# =========================================================

def _esc(value: object) -> str:
    return html.escape(str(value))


def _delta_class(subtitle: str) -> str:
    s = subtitle.strip()
    if s.startswith("+") or s.startswith("↑"):
        return "positive"
    if s.startswith("-") or s.startswith("↓"):
        return "negative"
    return ""


def card_html(title: str, value: str, subtitle: str = "") -> str:
    delta_class = _delta_class(subtitle)
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{_esc(title)}</div>
        <div class="kpi-value">{_esc(value)}</div>
        <div class="kpi-delta {delta_class}">{_esc(subtitle)}</div>
    </div>
    """


def mini_stat_html(title: str, value: str, subtitle: str = "") -> str:
    return f"""
    <div class="mini-stat">
        <div class="mini-label">{_esc(title)}</div>
        <div class="mini-value">{_esc(value)}</div>
        <div class="mini-sub">{_esc(subtitle)}</div>
    </div>
    """


def insight_row_html(title: str, value: str, subtitle: str = "") -> str:
    return f"""
    <div class="insight-row">
        <div class="mini-label">{_esc(title)}</div>
        <div class="insight-main">{_esc(value)}</div>
        <div class="insight-sub">{_esc(subtitle)}</div>
    </div>
    """


def section_open(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="sd-section-title">
            <div>
                <h3>{_esc(title)}</h3>
                {f'<p>{_esc(subtitle)}</p>' if subtitle else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_close() -> None:
    st.markdown("<div style='height: 6px'></div>", unsafe_allow_html=True)


def render_header(
    title: str = "Strava Dashboard",
    subtitle: str = "La tua attività, i tuoi trend e i progressi verso gli obiettivi.",
    eyebrow: str = "Personal analytics",
    badges: list[str] | None = None,
) -> None:
    badges = badges or []
    badges_html = "".join(f"<span class='sd-pill secondary'>{_esc(b)}</span>" for b in badges)
    st.markdown(
        f"""
        <div class="sd-hero">
            <div>
                <div class="sd-hero-eyebrow">{_esc(eyebrow)}</div>
                <h1 class="sd-hero-title">{_esc(title)}</h1>
                <div class="sd-hero-subtitle">{_esc(subtitle)}</div>
            </div>
            <div class="sd-hero-badges">
                <span class="sd-pill">● Live Strava</span>
                {badges_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Compatibility constants for charts and existing views
# ---------------------------------------------------------

ACCENT = COLORS["accent"]
GREEN = COLORS["green"]
PANEL = COLORS["panel"]
TEXT = COLORS["text"]
MUTED = COLORS["muted"]


def sport_color_map(sports=None):
    base = {
        "Ciclismo": "#A8B3C2",
        "Ride": "#A8B3C2",
        "VirtualRide": "#8B5CF6",
        "GravelRide": "#D4A373",
        "E-Bike": "#38BDF8",
        "Corsa": "#22C55E",
        "Run": "#22C55E",
        "TrailRun": "#16A34A",
        "Camminata": "#F59E0B",
        "Walk": "#F59E0B",
        "Escursionismo": "#FB923C",
        "Hike": "#FB923C",
        "Workout": "#EF4444",
        "Altri": "#64748B",
    }

    if sports is None:
        return base

    return {str(sport): base.get(str(sport), "#94A3B8") for sport in sports}
