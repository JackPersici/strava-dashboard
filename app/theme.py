from __future__ import annotations

import html
import streamlit as st

# =========================================================
# DESIGN TOKENS - Strava premium dark dashboard
# =========================================================

COLORS = {
    "bg": "#040912",
    "bg_alt": "#06101B",
    "surface": "#0A1422",
    "panel": "#0E1827",
    "panel_2": "#121D2E",
    "panel_3": "#18263A",
    "border": "rgba(216,230,255,0.070)",
    "border_soft": "rgba(216,230,255,0.040)",
    "text": "#F7FAFF",
    "text_soft": "#DCE7F5",
    "muted": "#93A7BD",
    "muted_2": "#6B7D91",
    "accent": "#F05A22",
    "accent_2": "#FF9A5C",
    "blue": "#7DB7FF",
    "green": "#22C55E",
    "red": "#EF4444",
    "yellow": "#F59E0B",
    "purple": "#8B5CF6",
}

SPACING = {"xs": "4px", "sm": "8px", "md": "12px", "lg": "18px", "xl": "24px"}
RADIUS = {"sm": "10px", "md": "13px", "lg": "16px", "xl": "22px"}

ACCENT = COLORS["accent"]
GREEN = COLORS["green"]
PANEL = COLORS["panel"]
TEXT = COLORS["text"]
MUTED = COLORS["muted"]


def _esc(value: object) -> str:
    return html.escape(str(value))


def _delta_class(subtitle: str) -> str:
    s = subtitle.strip()
    if s.startswith("+") or s.startswith("↑"):
        return "positive"
    if s.startswith("-") or s.startswith("↓"):
        return "negative"
    return ""


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
                radial-gradient(circle at 12% 0%, rgba(252,76,2,0.095), transparent 20rem),
                radial-gradient(circle at 88% 4%, rgba(125,183,255,0.055), transparent 24rem),
                linear-gradient(180deg, {COLORS['bg']} 0%, {COLORS['bg_alt']} 100%) !important;
            color: {COLORS['text']} !important;
        }}

        .block-container {{
            max-width: 1280px;
            padding-top: 0.35rem;
            padding-bottom: 1.65rem;
        }}

        header[data-testid="stHeader"] {{ background: transparent !important; }}
        footer {{ visibility: hidden; }}
        #MainMenu {{ visibility: hidden; }}

        h1, h2, h3, h4, p, span, div {{
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}

        div[data-testid="stVerticalBlock"] {{ gap: 0.42rem; }}
        div[data-testid="stHorizontalBlock"] {{ gap: 0.66rem; }}

        /* Remove the default white/gray Streamlit feel */
        section[data-testid="stSidebar"] {{ background: {COLORS['bg']} !important; }}
        .stMarkdown, .stPlotlyChart {{ color: {COLORS['text']} !important; }}

        /* Widgets */
        div[data-baseweb="select"] > div {{
            background: rgba(11,22,38,0.92) !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 13px !important;
            color: {COLORS['text']} !important;
            min-height: 36px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.025) !important;
        }}
        div[data-baseweb="select"] span {{ color: {COLORS['text_soft']} !important; font-size: .88rem !important; }}

        div[data-baseweb="select"] input,
        div[data-baseweb="select"] [data-testid="stMarkdownContainer"],
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] span {{
            color: {COLORS['text_soft']} !important;
            opacity: 1 !important;
        }}
        div[data-baseweb="select"] div[aria-disabled="true"],
        div[data-baseweb="select"] span[aria-disabled="true"] {{
            color: {COLORS['text_soft']} !important;
            opacity: .95 !important;
        }}
        .stMultiSelect label, .stSelectbox label, .stDateInput label {{
            color: {COLORS['muted']} !important;
            font-size: 0.68rem !important;
            letter-spacing: .08em;
            text-transform: uppercase;
            font-weight: 800;
        }}

        /* Premium compact tabs */
        div[data-testid="stTabs"] {{
            background: transparent;
            border-bottom: 1px solid rgba(255,255,255,0.095);
            padding: 0;
            margin: 0.1rem 0 0.65rem;
        }}
        div[data-baseweb="tab-list"] {{ gap: 4px; }}
        button[data-baseweb="tab"] {{
            color: {COLORS['muted']} !important;
            padding: 7px 10px 9px !important;
            border-radius: 0 !important;
            font-weight: 680 !important;
            font-size: 0.78rem !important;
            border-bottom: 2px solid transparent !important;
        }}
        button[data-baseweb="tab"]:hover {{
            color: {COLORS['text_soft']} !important;
            background: transparent !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: #FF8A3D !important;
            border-bottom-color: {COLORS['accent']} !important;
            background: transparent !important;
        }}
        div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {{ background-color: transparent !important; }}

        /* Secondary Streamlit metric fallback */
        div[data-testid="stMetric"] {{
            background: rgba(13,25,42,0.88);
            border: 1px solid {COLORS['border']};
            border-radius: 15px;
            padding: 10px 12px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.16);
        }}
        div[data-testid="stMetricLabel"] {{ color: {COLORS['muted']} !important; }}
        div[data-testid="stMetricValue"] {{ color: {COLORS['text']} !important; }}

        /* Backward-compatible app hero from previous steps: compact it strongly */
        .sd-hero, .sd-app-header {{
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            padding: 12px 16px;
            margin: 0 0 6px;
            border-radius: 18px;
            border: 1px solid {COLORS['border']};
            background:
                radial-gradient(circle at 6% 0%, rgba(240,90,34,0.115), transparent 12rem),
                linear-gradient(135deg, rgba(15,26,42,0.92), rgba(7,16,28,0.98));
            box-shadow: 0 10px 28px rgba(0,0,0,0.18);
            overflow: hidden;
        }}
        .sd-hero::after, .sd-app-header::after {{
            content: "";
            position: absolute;
            left: 18px;
            right: 45%;
            bottom: 0;
            height: 2px;
            background: linear-gradient(90deg, {COLORS['accent']}, rgba(252,76,2,0));
            opacity: .72;
        }}
        .sd-hero-eyebrow, .sd-eyebrow {{
            color: {COLORS['accent_2']};
            font-size: .63rem;
            font-weight: 820;
            letter-spacing: .18em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }}
        .sd-hero-title, .sd-app-title, .sd-page-title {{
            color: {COLORS['text']};
            font-size: clamp(1.16rem, 1.9vw, 1.60rem);
            line-height: 1.02;
            font-weight: 840;
            letter-spacing: -0.045em;
            margin: 0;
        }}
        .sd-hero-subtitle, .sd-app-subtitle {{ color: {COLORS['muted']}; font-size: .82rem; margin-top: 6px; }}
        .sd-hero-badges, .sd-header-actions {{ display: flex; flex-wrap: wrap; gap: 7px; justify-content: flex-end; align-items: center; }}

        .sd-overview-topline {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 16px;
            margin: 0 0 10px;
        }}
        .sd-page-kicker {{
            color: {COLORS['accent_2']};
            font-size: .63rem;
            font-weight: 820;
            letter-spacing: .18em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        .sd-page-subtitle {{ color: {COLORS['muted']}; font-size: .76rem; margin-top: 4px; }}
        .sd-topline-actions {{ display: flex; gap: 7px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }}

        .sd-pill, .pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 8px;
            border-radius: 999px;
            font-size: .68rem;
            font-weight: 740;
            border: 1px solid rgba(252,76,2,0.30);
            background: rgba(252,76,2,0.10);
            color: #FFB084;
            white-space: nowrap;
        }}
        .sd-pill.secondary {{
            border-color: {COLORS['border']};
            background: rgba(255,255,255,0.045);
            color: {COLORS['text_soft']};
        }}
        .sd-pill.green {{ border-color: rgba(34,197,94,.28); background: rgba(34,197,94,.10); color: #86EFAC; }}
        .sd-pill.red {{ border-color: rgba(239,68,68,.28); background: rgba(239,68,68,.10); color: #FDA4AF; }}

        .sd-code-chip, .sd-dev-chip, .sd-debug-chip {{ display: none !important; }}

        .kpi-card {{
            position: relative;
            overflow: hidden;
            min-height: 74px;
            padding: 10px 12px 10px;
            border-radius: 15px;
            border: 1px solid {COLORS['border']};
            background:
                linear-gradient(145deg, rgba(16,28,45,0.82), rgba(8,17,31,0.96));
            box-shadow: 0 8px 22px rgba(0,0,0,0.12);
        }}
        .kpi-inner {{
            display: grid;
            grid-template-columns: 36px minmax(0, 1fr);
            align-items: center;
            gap: 11px;
        }}
        .kpi-icon {{
            width: 34px;
            height: 34px;
            border-radius: 11px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.04rem;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
        }}
        .kpi-icon.fire {{ background: rgba(252,76,2,0.15); color: #FF8A3D; }}
        .kpi-icon.distance {{ background: rgba(34,197,94,0.14); color: #4ADE80; }}
        .kpi-icon.time {{ background: rgba(14,165,233,0.15); color: #38BDF8; }}
        .kpi-icon.elevation {{ background: rgba(139,92,246,0.16); color: #A78BFA; }}
        .kpi-card::after {{
            content: "";
            position: absolute;
            left: 12px; right: 12px; bottom: 0;
            height: 2px;
            border-radius: 999px 999px 0 0;
            background: linear-gradient(90deg, {COLORS['accent']}, rgba(252,76,2,0));
            opacity: .54;
        }}
        .kpi-label {{
            color: {COLORS['muted']};
            font-size: .58rem;
            text-transform: uppercase;
            letter-spacing: .14em;
            font-weight: 740;
        }}
        .kpi-value {{
            color: {COLORS['text']};
            font-size: clamp(1.05rem, 1.45vw, 1.36rem);
            font-weight: 820;
            letter-spacing: -0.055em;
            margin-top: 5px;
            line-height: 1.02;
        }}
        .kpi-delta {{ margin-top: 5px; color: {COLORS['muted']}; font-size: .63rem; font-weight: 720; }}
        .kpi-delta.positive {{ color: #86EFAC; }}
        .kpi-delta.negative {{ color: #FDA4AF; }}

        .sd-section-title {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 10px;
            margin: 8px 0 8px;
        }}
        .sd-section-title h3 {{
            color: {COLORS['text']};
            font-size: .86rem;
            font-weight: 740;
            letter-spacing: -0.025em;
            margin: 0;
        }}
        .sd-section-title p {{ color: {COLORS['muted']}; font-size: .73rem; margin: 3px 0 0; }}

        .sd-card, .card {{
            background: rgba(12,23,38,0.68);
            border: 1px solid {COLORS['border']};
            border-radius: 15px;
            padding: 10px;
            box-shadow: 0 8px 22px rgba(0,0,0,0.10);
        }}
        .sd-chart-card {{ padding: 10px 11px 7px; }}
        .sd-card.flat {{ background: rgba(9,21,37,0.70); box-shadow: none; }}



        .sd-chart-legend {{
            display: flex;
            align-items: center;
            gap: 18px;
            flex-wrap: wrap;
            margin: -2px 0 4px 6px;
            color: #BFD0E4;
            font-size: .62rem;
            line-height: 1;
        }}
        .sd-chart-legend-item {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            white-space: nowrap;
        }}
        .sd-chart-dot {{
            width: 8px;
            height: 8px;
            border-radius: 999px;
            display: inline-block;
            box-shadow: 0 0 0 1px rgba(255,255,255,.08);
        }}

        /* Streamlit plot containers get a card feel even if HTML wrappers are not respected */
        div[data-testid="stPlotlyChart"] {{
            background: rgba(12,23,38,0.58);
            border: 1px solid {COLORS['border_soft']};
            border-radius: 15px;
            padding: 7px 7px 0;
            box-shadow: 0 7px 18px rgba(0,0,0,0.10);
            overflow: hidden !important;
        }}
        .sd-card div[data-testid="stPlotlyChart"] {{ background: transparent; border: 0; box-shadow: none; padding: 0; }}

        .mini-stat, .insight-row {{
            background: rgba(9,19,32,0.54);
            border: 1px solid {COLORS['border_soft']};
            border-radius: 13px;
            padding: 8px 9px;
            margin-bottom: 6px;
        }}
        .mini-label, .insight-kicker {{
            color: {COLORS['muted']};
            font-size: .56rem;
            letter-spacing: .13em;
            text-transform: uppercase;
            font-weight: 740;
        }}
        .mini-value, .insight-main {{
            color: {COLORS['text']};
            font-size: .86rem;
            font-weight: 740;
            line-height: 1.12;
            margin-top: 4px;
        }}
        .mini-sub, .insight-sub, .tiny {{ color: {COLORS['muted']}; font-size: .66rem; margin-top: 3px; }}
        .insight-row {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: center;
            column-gap: 10px;
        }}
        .insight-value {{ color: {COLORS['text']}; font-size: .92rem; font-weight: 740; text-align: right; }}

        .big-empty {{
            padding: 22px 12px;
            text-align: center;
            color: {COLORS['muted']};
            border: 1px dashed rgba(255,255,255,0.11);
            border-radius: 14px;
            background: rgba(255,255,255,0.022);
            font-size: .82rem;
        }}

        .table-wrap {{ overflow: auto; border: 1px solid {COLORS['border_soft']}; border-radius: 14px; }}
        .data-table {{ width: 100%; border-collapse: collapse; color: {COLORS['text_soft']}; font-size: .78rem; }}
        .data-table th {{ color: {COLORS['muted']}; text-transform: uppercase; letter-spacing: .08em; font-size: .63rem; background: rgba(255,255,255,0.035); }}
        .data-table th, .data-table td {{ padding: 8px 9px; border-bottom: 1px solid {COLORS['border_soft']}; }}
        .data-table tr:last-child td {{ border-bottom: 0; }}



        /* Step 4 premium polish overrides */
        .sd-page-title {{ font-size: clamp(1.18rem, 1.65vw, 1.46rem); font-weight: 760; letter-spacing: -0.035em; }}
        .sd-page-kicker, .sd-hero-eyebrow, .sd-eyebrow {{ font-weight: 760; letter-spacing: .17em; }}
        .sd-section-title h3 {{ font-size: .84rem; font-weight: 720; letter-spacing: -0.018em; }}
        .sd-section-title p {{ font-size: .70rem; opacity: .92; }}
        .kpi-card {{ min-height: 76px; padding: 11px 12px 10px; }}
        .kpi-value {{ text-shadow: none; margin-top: 7px; }}
        .sd-pill {{ padding: 3px 8px; font-weight: 720; }}
        .mini-value, .insight-main, .insight-value {{ font-weight: 760; }}
        .mini-stat, .insight-row {{ box-shadow: none; }}
        div[data-testid="stPlotlyChart"] svg {{ overflow: visible; }}

        @media (max-width: 768px) {{
            .block-container {{ padding-left: 0.70rem; padding-right: 0.70rem; padding-top: .4rem; }}
            .sd-hero, .sd-app-header, .sd-overview-topline {{ align-items: flex-start; flex-direction: column; padding: 13px 14px; }}
            .sd-hero-badges, .sd-header-actions, .sd-topline-actions {{ justify-content: flex-start; width: 100%; }}
            .kpi-card {{ min-height: 74px; padding: 10px; }}
            .kpi-value {{ font-size: 1.22rem; }}
            div[data-testid="stPlotlyChart"] {{ padding: 6px 6px 0; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# COMPONENTS
# =========================================================

def render_header(
    title: str = "Strava Dashboard",
    subtitle: str = "La tua attività, i tuoi trend e i progressi verso gli obiettivi.",
    eyebrow: str = "Personal analytics",
    badges: list[str] | None = None,
) -> None:
    # Header intentionally renders only the Live Strava status.
    # Extra badges from older app versions are ignored because one of them was
    # leaking as a literal "</div>" chip in the UI.
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
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def overview_topline(title: str, subtitle: str, badges: list[str] | None = None) -> str:
    badges_html = "".join(f"<span class='sd-pill secondary'>{_esc(b)}</span>" for b in (badges or []))
    return f"""
    <div class="sd-overview-topline">
        <div>
            <div class="sd-page-kicker">Overview</div>
            <h2 class="sd-page-title">{_esc(title)}</h2>
            <div class="sd-page-subtitle">{_esc(subtitle)}</div>
        </div>
        <div class="sd-topline-actions">{badges_html}</div>
    </div>
    """


def overview_hero(title: str, subtitle: str, metrics: list[tuple[str, str]]) -> str:
    metrics_html = "".join(f"<span class='sd-pill secondary'>{_esc(label)} · {_esc(value)}</span>" for label, value in metrics)
    return overview_topline(title, subtitle, [f"{label} · {value}" for label, value in metrics])


def _kpi_icon(title: str) -> tuple[str, str]:
    normalized = title.strip().lower()
    if "att" in normalized:
        return "🔥", "fire"
    if "distan" in normalized:
        return "🗺️", "distance"
    if "tempo" in normalized:
        return "🕘", "time"
    if "disliv" in normalized:
        return "⛰️", "elevation"
    return "•", "distance"


def card_html(title: str, value: str, subtitle: str = "") -> str:
    delta_class = _delta_class(subtitle)
    icon, icon_class = _kpi_icon(title)
    return f"""
    <div class="kpi-card">
        <div class="kpi-inner">
            <div class="kpi-icon {icon_class}">{icon}</div>
            <div class="kpi-copy">
                <div class="kpi-label">{_esc(title)}</div>
                <div class="kpi-value">{_esc(value)}</div>
                <div class="kpi-delta {delta_class}">{_esc(subtitle)}</div>
            </div>
        </div>
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


def section_header_html(title: str, subtitle: str = "") -> str:
    return f"""
    <div class="sd-section-title">
        <div>
            <h3>{_esc(title)}</h3>
            {f'<p>{_esc(subtitle)}</p>' if subtitle else ''}
        </div>
    </div>
    """


def section_open(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="sd-card sd-chart-card">
            {section_header_html(title, subtitle)}
        """,
        unsafe_allow_html=True,
    )


def section_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def sport_color_map(sports=None):
    base = {
        "Ciclismo": "#E56A35",
        "Ride": "#E56A35",
        "VirtualRide": "#8067E8",
        "GravelRide": "#D8A06B",
        "E-Bike": "#06B6D4",
        "Corsa": "#22C55E",
        "Run": "#22C55E",
        "TrailRun": "#84CC16",
        "Camminata": "#7DB7FF",
        "Walk": "#7DB7FF",
        "Escursionismo": "#166534",
        "Hike": "#166534",
        "Workout": "#EF4444",
        "Pesi": "#EF4444",
        "Nuoto": "#38BDF8",
        "Altri": "#748397",
    }
    if sports is None:
        return base
    return {str(sport): base.get(str(sport), "#94A3B8") for sport in sports}
