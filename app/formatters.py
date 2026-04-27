from __future__ import annotations


def fmt_km(v: float) -> str:
    return f"{v:,.1f} km"


def fmt_h(v: float) -> str:
    return f"{v:,.1f} h"


def fmt_m(v: float) -> str:
    return f"{v:,.0f} m"


def fmt_int(v: float | int) -> str:
    return f"{int(round(v))}"


def fmt_pct(v: float) -> str:
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.0f}%"
