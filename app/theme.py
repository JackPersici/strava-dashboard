from __future__ import annotations

import html
import streamlit as st

# =========================================================
# DESIGN TOKENS - Strava premium dark dashboard
# =========================================================

COLORS = {
    "bg": "#050B14",
    "bg_alt": "#07111F",
    "surface": "#0B1626",
    "panel": "#0E1A2B",
    "panel_2": "#121F33",
    "panel_3": "#17263C",
    "border": "rgba(255,255,255,0.08)",
    "border_soft": "rgba(255,255,255,0.055)",
    "text": "#F6F8FC",
    "text_soft": "#D9E2EF",
    "muted": "#8FA1B8",
    "muted_2": "#65758B",
    "accent": "#FC4C02",
    "accent_2": "#FF8A3D",
    "blue": "#7DB7FF",
    "green": "#22C55E",
    "red": "#EF4444",
    "yellow": "#F59E0B",
    "purple": "#8B5CF6",
}

SPACING = {"xs": "4px", "sm": "8px", "md": "14px", "lg": "20px", "xl": "28px"}
RADIUS = {"sm": "10px", "md": "14px", "lg": "18px", "xl": "24px"}

ACCENT = COLORS["accent"]
GREEN = COLORS["green"]
PANEL = COLORS["panel"]
TEXT = COLORS["text"]
MUTED = COLORS["muted"]


def _esc(value: object) -> str:
    return html.escape(str(value))


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
                radial-gradient(circle at 12% 0%, rgba(252,76,2,0.16), transparent 24rem),
                radial-gradient(circle at 90% 4%, rgba(125,183,255,0.09), transparent 25rem),
                linear-gradient(180deg, {COLORS['bg']} 0%, {COLORS['bg_alt']} 100%) !important;
            color: {COLORS['text']} !important;
        }}

        .block-container {{
            max-width: 1220px;
            padding-top: 0.65rem;
            padding-bottom: 2.4rem;
        }}

        header[data-testid="stHeader"] {{ background: transparent !important; }}
        footer {{ visibility: hidden; }}
        #MainMenu {{ visibility: hidden; }}

        h1, h2, h3, h4, p, span, div {{
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}

        div[data-testid="stVerticalBlock"] {{ gap: 0.65rem; }}
        div[data-testid="stHorizontalBlock"] {{ gap: 0.85rem; }}

        /* Widgets */
        div[data-baseweb="select"] > div {{
            background: rgba(11,22,38,0.94) !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 14px !important;
            color: {COLORS['text']} !important;
            min-height: 38px !important;
            box-shadow: none !important;
        }}
        div[data-baseweb="select"] span {{ color: {COLORS['text_soft']} !important; }}
        .stMultiSelect label, .stSelectbox label, .stDateInput label {{
            color: {COLORS['muted']} !important;
            font-size: 0.72rem !important;
            letter-spacing: .08em;
            text-transform: uppercase;
            font-weight: 750;
        }}

        /* Premium compact tabs */
        div[data-testid="stTabs"] {{
            background: rgba(11,22,38,0.52);
            border: 1px solid {COLORS['border_soft']};
            border-radius: 18px;
            padding: 5px 8px 0;
            margin-bottom: 0.7rem;
        }}
        div[data-baseweb="tab-list"] {{ gap: 4px; }}
        button[data-baseweb="tab"] {{
            color: {COLORS['muted']} !important;
            padding: 8px 14px !important;
            border-radius: 999px !important;
            font-weight: 750 !important;
            font-size: 0.88rem !important;
        }}
        button[data-baseweb="tab"]:hover {{
            color: {COLORS['text_soft']} !important;
            background: rgba(255,255,255,0.04) !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: #FFD3BD !important;
            background: rgba(252,76,2,0.13) !important;
        }}
        div[data-baseweb="tab-highlight"] {{ background-color: transparent !important; }}
        div[data-baseweb="tab-border"] {{ background-color: transparent !important; }}

        /* Native metrics still used in secondary pages */
        div[data-testid="stMetric"] {{
            background: linear-gradient(145deg, rgba(18,31,51,0.94), rgba(8,17,31,0.98));
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['lg']};
            padding: 12px 14px;
            box-shadow: 0 16px 38px rgba(0,0,0,0.20);
        }}
        div[data-testid="stMetricLabel"] {{ color: {COLORS['muted']} !important; }}
        div[data-testid="stMetricValue"] {{ color: {COLORS['text']} !important; }}

        /* Header kept for app-level use: compact, not hero-sized */
        .sd-app-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            padding: 12px 2px 8px;
            margin-bottom: 6px;
        }}
        .sd-app-title {{
            color: {COLORS['text']};
            font-size: clamp(1.25rem, 2.1vw, 1.8rem);
            font-weight: 900;
            letter-spacing: -0.045em;
            margin: 0;
        }}
        .sd-app-subtitle {{
            color: {COLORS['muted']};
            font-size: .84rem;
            margin-top: 3px;
        }}
        .sd-header-actions {{ display: flex; flex-wrap: wrap; gap: 7px; justify-content: flex-end; }}

        .sd-overview-hero {{
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 18px;
            padding: 16px 18px;
            margin: 2px 0 12px;
            border-radius: {RADIUS['xl']};
            border: 1px solid {COLORS['border']};
            background:
                radial-gradient(circle at 10% 0%, rgba(252,76,2,0.24), transparent 16rem),
                linear-gradient(135deg, rgba(18,31,51,0.92), rgba(9,18,32,0.98));
            box-shadow: 0 24px 70px rgba(0,0,0,0.30);
        }}
        .sd-overview-hero::after {{
            content: "";
            position: absolute;
            inset: auto 18px 0 18px;
            height: 2px;
            border-radius: 999px 999px 0 0;
            background: linear-gradient(90deg, {COLORS['accent']}, rgba(252,76,2,0));
            opacity: .85;
        }}
        .sd-eyebrow {{
            color: {COLORS['accent_2']};
            font-size: .68rem;
            font-weight: 900;
            letter-spacing: .18em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }}
        .sd-hero-title {{
            color: {COLORS['text']};
            font-size: clamp(1.38rem, 2.7vw, 2rem);
            line-height: 1.05;
            font-weight: 920;
            letter-spacing: -0.06em;
            margin: 0;
        }}
        .sd-hero-subtitle {{ color: {COLORS['muted']}; font-size: .86rem; margin-top: 6px; }}
        .sd-hero-metrics {{ display: flex; flex-wrap: wrap; gap: 9px; justify-content: flex-end; }}
        .sd-hero-metric {{
            min-width: 96px;
            padding: 9px 11px;
            border: 1px solid {COLORS['border_soft']};
            border-radius: 15px;
            background: rgba(255,255,255,0.045);
        }}
        .sd-hero-metric-label {{ color: {COLORS['muted']}; font-size: .65rem; text-transform: uppercase; letter-spacing: .12em; font-weight: 850; }}
        .sd-hero-metric-value {{ color: {COLORS['text']}; font-size: .95rem; font-weight: 850; margin-top: 3px; }}

        .sd-pill, .pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 9px;
            border-radius: 999px;
            font-size: .72rem;
            font-weight: 800;
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
            min-height: 92px;
            padding: 13px 14px 12px;
            border-radius: {RADIUS['lg']};
            border: 1px solid {COLORS['border']};
            background:
                radial-gradient(circle at 90% 15%, rgba(252,76,2,0.13), transparent 7rem),
                linear-gradient(145deg, rgba(18,31,51,0.97), rgba(8,17,31,0.99));
            box-shadow: 0 18px 48px rgba(0,0,0,0.25);
        }}
        .kpi-card::after {{
            content: "";
            position: absolute;
            left: 14px; right: 14px; bottom: 0;
            height: 2px;
            border-radius: 999px 999px 0 0;
            background: linear-gradient(90deg, {COLORS['accent']}, rgba(252,76,2,0));
            opacity: .78;
        }}
        .kpi-label {{
            color: {COLORS['muted']};
            font-size: .66rem;
            text-transform: uppercase;
            letter-spacing: .14em;
            font-weight: 850;
        }}
        .kpi-value {{
            color: {COLORS['text']};
            font-size: clamp(1.28rem, 1.85vw, 1.75rem);
            font-weight: 900;
            letter-spacing: -0.05em;
            margin-top: 8px;
            line-height: 1.05;
        }}
        .kpi-delta {{
            margin-top: 6px;
            color: {COLORS['muted']};
            font-size: .72rem;
            font-weight: 700;
        }}
        .kpi-delta.positive {{ color: #86EFAC; }}
        .kpi-delta.negative {{ color: #FDA4AF; }}

        .sd-section-title {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 12px;
            margin: 0 0 10px;
        }}
        .sd-section-title h3 {{
            color: {COLORS['text']};
            font-size: .98rem;
            font-weight: 850;
            letter-spacing: -0.02em;
            margin: 0;
        }}
        .sd-section-title p {{ color: {COLORS['muted']}; font-size: .77rem; margin: 3px 0 0; }}

        .card, .sd-card {{
            background: linear-gradient(145deg, rgba(18,31,51,0.95), rgba(8,17,31,0.99));
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['lg']};
            padding: 13px;
            box-shadow: 0 18px 48px rgba(0,0,0,0.22);
        }}
        .sd-card.compact {{ padding: 12px; }}
        .sd-chart-card {{ padding: 12px 12px 8px; }}

        .mini-stat, .insight-row {{
            background: linear-gradient(145deg, rgba(18,31,51,0.94), rgba(10,20,36,0.98));
            border: 1px solid {COLORS['border_soft']};
            border-radius: 15px;
            padding: 10px 12px;
            margin-bottom: 8px;
        }}
        .mini-label {{
            color: {COLORS['muted']};
            font-size: .63rem;
            letter-spacing: .13em;
            text-transform: uppercase;
            font-weight: 850;
        }}
        .mini-value, .insight-main {{
            color: {COLORS['text']};
            font-size: 1rem;
            font-weight: 850;
            line-height: 1.15;
            margin-top: 4px;
        }}
        .mini-sub, .insight-sub, .tiny {{ color: {COLORS['muted']}; font-size: .75rem; margin-top: 4px; }}
        .insight-row {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: center;
            column-gap: 10px;
        }}
        .insight-kicker {{ color: {COLORS['muted']}; font-size: .62rem; text-transform: uppercase; letter-spacing: .12em; font-weight: 850; }}
        .insight-value {{ color: {COLORS['text']}; font-size: .98rem; font-weight: 850; text-align: right; }}

        .big-empty {{
            padding: 30px 16px;
            text-align: center;
            color: {COLORS['muted']};
            border: 1px dashed rgba(255,255,255,0.12);
            border-radius: 16px;
            background: rgba(255,255,255,0.025);
        }}

        .table-wrap {{
            overflow: auto;
            border: 1px solid {COLORS['border_soft']};
            border-radius: 16px;
        }}
        .data-table {{ width: 100%; border-collapse: collapse; color: {COLORS['text_soft']}; font-size: .82rem; }}
        .data-table th {{ color: {COLORS['muted']}; text-transform: uppercase; letter-spacing: .08em; font-size: .68rem; background: rgba(255,255,255,0.035); }}
        .data-table th, .data-table td {{ padding: 10px 12px; border-bottom: 1px solid {COLORS['border_soft']}; }}
        .data-table tr:last-child td {{ border-bottom: 0; }}

        @media (max-width: 768px) {{
            .block-container {{ padding-left: 0.75rem; padding-right: 0.75rem; padding-top: .45rem; }}
            .sd-app-header, .sd-overview-hero {{ align-items: flex-start; flex-direction: column; }}
            .sd-header-actions, .sd-hero-metrics {{ justify-content: flex-start; width: 100%; }}
            .sd-hero-metric {{ flex: 1 1 42%; }}
            .kpi-card {{ min-height: 84px; padding: 12px; }}
            .kpi-value {{ font-size: 1.36rem; }}
            .card, .sd-card {{ padding: 12px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# COMPONENTS
# =========================================================

def render_header(title: str = "Strava Dashboard", subtitle: str = "", badges: list[str] | None = None) -> None:
    badges_html = "".join(f"<span class='sd-pill secondary'>{_esc(badge)}</span>" for badge in (badges or []))
    st.markdown(
        f"""
        <div class="sd-app-header">
            <div>
                <h1 class="sd-app-title">{_esc(title)}</h1>
                {f'<div class="sd-app-subtitle">{_esc(subtitle)}</div>' if subtitle else ''}
            </div>
            <div class="sd-header-actions">{badges_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def overview_hero(title: str, subtitle: str, metrics: list[tuple[str, str]]) -> str:
    metrics_html = "".join(
        f"""
        <div class="sd-hero-metric">
            <div class="sd-hero-metric-label">{_esc(label)}</div>
            <div class="sd-hero-metric-value">{_esc(value)}</div>
        </div>
        """
        for label, value in metrics
    )
    return f"""
    <div class="sd-overview-hero">
        <div>
            <div class="sd-eyebrow">Personal training cockpit</div>
            <h2 class="sd-hero-title">{_esc(title)}</h2>
            <div class="sd-hero-subtitle">{_esc(subtitle)}</div>
        </div>
        <div class="sd-hero-metrics">{metrics_html}</div>
    </div>
    """


def card_html(title: str, value: str, subtitle: str = "") -> str:
    delta_class = "positive" if subtitle.strip().startswith("+") else "negative" if subtitle.strip().startswith("-") else ""
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


def insight_row_html(label: str, value: str, subtitle: str = "") -> str:
    return f"""
    <div class="insight-row">
        <div>
            <div class="insight-kicker">{_esc(label)}</div>
            <div class="insight-sub">{_esc(subtitle)}</div>
        </div>
        <div class="insight-value">{_esc(value)}</div>
    </div>
    """


def section_open(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="sd-card sd-chart-card">
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
    st.markdown("</div>", unsafe_allow_html=True)


def sport_color_map(sports=None):
    base = {
        "Ciclismo": "#FC4C02",
        "Ride": "#FC4C02",
        "VirtualRide": "#8B5CF6",
        "GravelRide": "#F59E0B",
        "E-Bike": "#06B6D4",
        "Corsa": "#22C55E",
        "Run": "#22C55E",
        "TrailRun": "#84CC16",
        "Camminata": "#7DB7FF",
        "Walk": "#7DB7FF",
        "Escursionismo": "#F97316",
        "Hike": "#F97316",
        "Workout": "#EF4444",
        "Pesi": "#EF4444",
        "Nuoto": "#38BDF8",
        "Altri": "#94A3B8",
    }
    if sports is None:
        return base
    return {str(sport): base.get(str(sport), "#94A3B8") for sport in sports}
