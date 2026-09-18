"""Notification + activity helpers for TLC BidFlow AI."""
from __future__ import annotations

from datetime import datetime

from data import database as db

LEVEL_EMOJI = {
    "red": "🔴",
    "orange": "🟠",
    "green": "🟢",
    "blue": "🔵",
}


def notify(level: str, message: str, opp_id: int | None = None) -> int:
    """Create a notification and matching activity."""
    nid = db.create_notification(level, message, opp_id)
    db.create_activity(opp_id, message, "notification")
    return nid


def activity(message: str, opp_id: int | None = None,
             category: str = "general") -> int:
    return db.create_activity(opp_id, message, category)


def emoji_for(level: str) -> str:
    return LEVEL_EMOJI.get((level or "").lower(), "•")


def time_ago(ts: str) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return ts
    delta = datetime.now() - dt
    secs = int(delta.total_seconds())
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    if secs < 172800:
        return "yesterday"
    return f"{secs // 86400}d ago"