"""Formatting helpers."""
from __future__ import annotations

from datetime import datetime


def money(value: float | int | None, compact: bool = False) -> str:
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        return "$0"
    if compact:
        if abs(v) >= 1_000_000:
            return f"${v / 1_000_000:.1f}M"
        if abs(v) >= 1_000:
            return f"${v / 1_000:.0f}K"
    return f"${v:,.0f}"


def pct(value: float | int | None) -> str:
    try:
        return f"{float(value or 0):.0f}%"
    except (TypeError, ValueError):
        return "0%"


def short_date(value: str | None) -> str:
    if not value:
        return "—"
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%b %d, %Y")
        except ValueError:
            continue
    return value


def short_datetime(value: str | None) -> str:
    if not value:
        return "—"
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%b %d, %Y — %I:%M %p").replace(" 0", " ")
        except ValueError:
            continue
    return value


def relative_day(value: str | None) -> str:
    if not value:
        return "—"
    try:
        dt = datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return "—"
    delta = (dt.date() - datetime.now().date()).days
    if delta == 0:
        return "Due Today"
    if delta == 1:
        return "Due Tomorrow"
    if 0 < delta <= 7:
        return "Due This Week"
    if delta < 0:
        return "Past"
    return "Upcoming"


def badge(level: str) -> str:
    """Return an HTML span for a status/risk badge."""
    level = (level or "").strip()
    key = level.lower()
    cls = "badge badge-gray"
    if key in ("high", "red", "lost", "not reviewed", "pending",
               "clarification needed"):
        cls = "badge badge-red"
    elif key in ("medium", "orange", "under review", "needs review",
                 "quotes pending", "pricing pending", "review",
                 "missing docs"):
        cls = "badge badge-orange"
    elif key in ("low", "green", "ready", "received", "complete",
                 "reviewed", "selected", "awarded", "qualified"):
        cls = "badge badge-green"
    elif key in ("blue", "new opportunity", "invited", "plans sent",
                 "estimating"):
        cls = "badge badge-blue"
    return f'<span class="{cls}">{level}</span>'


def status_color(status: str) -> str:
    s = (status or "").lower()
    if s in ("awarded",):
        return "#16a34a"
    if s in ("lost",):
        return "#dc2626"
    if s in ("submitted", "bid review"):
        return "#2563eb"
    if s in ("estimating", "quotes pending"):
        return "#d97706"
    return "#6b7280"