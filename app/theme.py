from __future__ import annotations

import streamlit as st


BG = "#07111f"
PANEL = "#0b1830"
BORDER = "rgba(148, 163, 184, 0.18)"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
ACCENT = "#ff7a1a"
GREEN = "#22c55e"
RED = "#ef4444"

SPORT_COLORS = {
    "Ciclismo": "#ff7a1a",
    "VirtualRide": "#3b82f6",
    "Corsa": "#ff4d4f",
    "TrailRun": "#a855f7",
    "Escursionismo": "#4ade80",
    "Camminata": "#22c55e",
    "GravelRide": "#8b5cf6",
    "Sci alpino": "#60a5fa",
    "Sci alpinismo": "#38bdf8",
    "Nuoto": "#fbbf24",
    "SUP": "#14b8a6",
    "Surf": "#f59e0b",
    "Workout": "#10b981",
    "E-Bike": "#84cc16",
    "Altri": "#64748b",
    "Other": "#64748b",
}

SPORT_ICONS = {
    "Ciclismo": "🚴",
    "VirtualRide": "💻",
    "Corsa": "👟",
    "TrailRun": "🏃",
    "Escursionismo": "🥾",
    "Camminata": "🚶",
    "GravelRide": "🪨",
    "Sci alpino": "🎿",
    "Sci alpinismo": "⛷️",
    "Nuoto": "🏊",
    "SUP": "🏄",
    "Surf": "🌊",
    "Workout": "🏋️",
    "E-Bike": "⚡",
    "Altri": "✨",
}


def sport_color_map(labels) -> dict[str, str]:
    fallback = SPORT_COLORS.get("Altri", "#64748b")
    return {str(lab): SPORT_COLORS.get(str(lab), fallback) for lab in labels}


def sport_icon(label: str) -> str:
    return SPORT_ICONS.get(label, "✨")


def inject_global_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top right, rgba(25, 55, 95, 0.45), transparent 28%),
                linear-gradient(180deg, #07111f 0%, #09162a 100%);
            color: {TEXT};
        }}
        .block-container {{
            max-width: 1450px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }}
        h1, h2, h3, h4, h5, h6, p, div, span, label {{ color: {TEXT}; }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stToolbar"] {{ right: 0.5rem; }}
        .app-title {{ font-size: 3rem; font-weight: 800; line-height: 1; margin-bottom: 0.4rem; letter-spacing: -0.03em; }}
        .app-subtitle {{ color: {MUTED}; font-size: 1rem; margin-bottom: 1.25rem; }}
        .hero-wrap {{
            background: linear-gradient(180deg, rgba(11,24,48,0.88) 0%, rgba(8,18,35,0.88) 100%);
            border: 1px solid {BORDER}; border-radius: 22px; padding: 20px 20px 16px 20px; margin-bottom: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.22);
        }}
        .filter-wrap {{
            background: linear-gradient(180deg, rgba(11,24,48,0.85) 0%, rgba(8,18,35,0.85) 100%);
            border: 1px solid {BORDER}; border-radius: 18px; padding: 14px 14px 4px 14px; margin-bottom: 18px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        }}
        .kpi-card {{
            background: linear-gradient(180deg, rgba(13,27,52,1) 0%, rgba(9,22,42,1) 100%);
            border: 1px solid {BORDER}; border-radius: 18px; padding: 16px 18px 14px 18px; min-height: 125px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.16);
        }}
        .kpi-label {{ font-size: 0.88rem; color: #cbd5e1; margin-bottom: 10px; }}
        .kpi-value {{ font-size: 2rem; font-weight: 800; line-height: 1.05; margin-bottom: 8px; color: white; }}
        .kpi-delta {{ font-size: 0.9rem; color: {GREEN}; font-weight: 600; }}
        .panel {{
            background: linear-gradient(180deg, rgba(11,24,48,0.98) 0%, rgba(8,18,35,0.98) 100%);
            border: 1px solid {BORDER}; border-radius: 18px; padding: 14px 14px 10px 14px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.16); margin-bottom: 14px;
        }}
        .panel-title {{ font-size: 1.15rem; font-weight: 800; margin-bottom: 10px; color: white; }}
        .panel-note {{ color: {MUTED}; font-size: 0.9rem; margin-top: -2px; margin-bottom: 8px; }}
        .mini-stat {{ background: rgba(255,255,255,0.02); border: 1px solid {BORDER}; border-radius: 16px; padding: 14px 14px 10px 14px; margin-bottom: 10px; }}
        .mini-label {{ color: {MUTED}; font-size: 0.85rem; margin-bottom: 4px; }}
        .mini-value {{ color: white; font-size: 1.55rem; font-weight: 800; line-height: 1.1; }}
        .mini-sub {{ color: #cbd5e1; font-size: 0.9rem; margin-top: 4px; }}
        .pill {{ display: inline-block; background: rgba(255,122,26,0.10); color: #ffb37b; border: 1px solid rgba(255,122,26,0.22); padding: 5px 10px; border-radius: 999px; font-size: 0.82rem; font-weight: 600; }}
        .insight-row {{ padding: 10px 0; border-bottom: 1px solid rgba(148,163,184,0.12); }}
        .insight-row:last-child {{ border-bottom: none; }}
        .insight-main {{ font-size: 1.05rem; font-weight: 700; color: white; }}
        .insight-sub {{ color: {MUTED}; font-size: 0.88rem; margin-top: 2px; }}
        .table-wrap {{ background: transparent; overflow-x: auto; }}
        .data-table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.95rem; overflow: hidden; border-radius: 14px; border: 1px solid {BORDER}; }}
        .data-table th {{ background: rgba(255,255,255,0.04); color: #cbd5e1; text-align: left; padding: 12px 14px; font-weight: 700; border-bottom: 1px solid rgba(148,163,184,0.12); }}
        .data-table td {{ padding: 12px 14px; border-bottom: 1px solid rgba(148,163,184,0.08); color: white; }}
        .data-table tr:last-child td {{ border-bottom: none; }}
        .data-table tr:nth-child(even) td {{ background: rgba(255,255,255,0.015); }}
        .tiny {{ color: {MUTED}; font-size: 0.86rem; }}
        .big-empty {{ background: linear-gradient(180deg, rgba(11,24,48,0.9) 0%, rgba(8,18,35,0.9) 100%); border: 1px dashed rgba(148,163,184,0.22); border-radius: 18px; padding: 28px; text-align: center; color: {MUTED}; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 10px; margin-bottom: 8px; }}
        .stTabs [data-baseweb="tab"] {{ background: transparent; border-radius: 12px 12px 0 0; color: #cbd5e1; padding: 8px 8px; font-weight: 600; }}
        .stTabs [aria-selected="true"] {{ color: {ACCENT} !important; }}
        [data-testid="stExpander"] {{ background: transparent; border: none !important; }}
        .stMultiSelect div[data-baseweb="select"] > div,
        .stSelectbox div[data-baseweb="select"] > div,
        .stDateInput > div > div {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(148,163,184,0.16); border-radius: 12px; color: white; }}
        .stButton button {{ background: linear-gradient(180deg, #ff7a1a 0%, #f97316 100%); color: white; border: none; border-radius: 12px; font-weight: 700; padding: 0.5rem 1rem; }}
        .stButton button:hover {{ background: linear-gradient(180deg, #ff8b36 0%, #fb7c20 100%); color: white; }}
        div[data-testid="stMetric"] {{ background: linear-gradient(180deg, rgba(13,27,52,1) 0%, rgba(9,22,42,1) 100%); border: 1px solid {BORDER}; border-radius: 16px; padding: 12px 16px; }}
        div[data-testid="stMetricLabel"] * {{ color: #cbd5e1 !important; }}
        div[data-testid="stMetricValue"] * {{ color: white !important; }}
        div[data-testid="stMetricDelta"] * {{ color: {GREEN} !important; }}
        [data-testid="stExpander"] details summary,
        [data-testid="stExpander"] details summary p,
        [data-testid="stExpander"] details summary span,
        [data-testid="stExpander"] details summary div {{ color: white !important; }}
        .stMultiSelect label,
        .stSelectbox label,
        .stDateInput label,
        .stTextInput label,
        .stNumberInput label {{ color: #e5e7eb !important; font-weight: 600; }}
        .stMultiSelect div[data-baseweb="select"] *,
        .stSelectbox div[data-baseweb="select"] *,
        .stDateInput * {{ color: white !important; }}
        div[role="listbox"] {{ background: #0f1d38 !important; color: white !important; border: 1px solid rgba(148, 163, 184, 0.18) !important; }}
        div[role="option"] {{ background: #0f1d38 !important; color: white !important; }}
        div[role="option"]:hover {{ background: rgba(255, 122, 26, 0.14) !important; color: white !important; }}
        .stMultiSelect [data-baseweb="tag"] {{ background: rgba(255, 122, 26, 0.14) !important; border: 1px solid rgba(255, 122, 26, 0.26) !important; color: white !important; }}
        .stMultiSelect [data-baseweb="tag"] * {{ color: white !important; }}
        [data-baseweb="calendar"], [data-baseweb="calendar"] * {{ background: #0f1d38 !important; color: white !important; }}
        .stDateInput input {{ color: white !important; -webkit-text-fill-color: white !important; }}
        input::placeholder, textarea::placeholder {{ color: #94a3b8 !important; opacity: 1 !important; }}
        @media (max-width: 768px) {{ .app-title {{ font-size: 2.3rem; }} .kpi-value {{ font-size: 1.7rem; }} .panel-title {{ font-size: 1rem; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="app-title">Strava Dashboard</div>
            <div class="app-subtitle">Overview completa, analisi avanzate e design mobile-first</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_html(label: str, value: str, delta: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta">{delta if delta else '&nbsp;'}</div>
    </div>
    """


def mini_stat_html(label: str, value: str, sub: str = "") -> str:
    return f"""
    <div class="mini-stat">
        <div class="mini-label">{label}</div>
        <div class="mini-value">{value}</div>
        <div class="mini-sub">{sub}</div>
    </div>
    """


def section_open(title: str, note: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{title}</div>
            {f'<div class="panel-note">{note}</div>' if note else ''}
        """,
        unsafe_allow_html=True,
    )


def section_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)
