"""
SQLite data layer for TLC BidFlow AI.

All data is fictional demo data. This module provides simple, reliable
helpers for reading and writing the demo database.
"""
from __future__ import annotations

import os
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "tlc_bidflow.db")


@contextmanager
def get_conn():
    """Yield a SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they do not exist."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL,
                owner TEXT,
                location TEXT,
                project_type TEXT,
                estimated_value REAL,
                bid_due TEXT,
                prebid TEXT,
                estimator TEXT,
                project_manager TEXT,
                status TEXT DEFAULT 'New Opportunity',
                risk TEXT DEFAULT 'Medium',
                readiness INTEGER DEFAULT 50,
                scope_json TEXT,
                divisions_json TEXT,
                missing_json TEXT,
                next_actions_json TEXT,
                notes TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS scope_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                scope TEXT,
                quantity REAL,
                unit TEXT,
                self_perform TEXT,
                subcontract TEXT,
                quote_required TEXT,
                status TEXT
            );

            CREATE TABLE IF NOT EXISTS estimates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                labor REAL,
                materials REAL,
                equipment REAL,
                subcontractors REAL,
                mobilization REAL,
                temp_facilities REAL,
                supervision REAL,
                insurance REAL,
                permits REAL,
                contingency_pct REAL,
                overhead_pct REAL,
                profit_pct REAL,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS subcontractors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                trade TEXT,
                contact TEXT,
                email TEXT,
                phone TEXT,
                location TEXT,
                insurance_status TEXT,
                w9_status TEXT,
                quote_status TEXT,
                last_contact TEXT,
                projects_worked INTEGER DEFAULT 0,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                scope TEXT,
                contact TEXT,
                email TEXT,
                phone TEXT,
                location TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                vendor TEXT,
                scope TEXT,
                amount REAL,
                lead_time_weeks INTEGER,
                validity_days INTEGER,
                compliance TEXT,
                status TEXT,
                exceptions TEXT,
                received_at TEXT
            );

            CREATE TABLE IF NOT EXISTS addenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                number INTEGER,
                received_date TEXT,
                status TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                timestamp TEXT,
                message TEXT,
                category TEXT
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                level TEXT,
                message TEXT,
                created_at TEXT,
                read INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                project TEXT,
                owner TEXT,
                location TEXT,
                contract_value REAL,
                project_manager TEXT,
                estimate_linked INTEGER,
                subs_linked INTEGER,
                vendors_linked INTEGER,
                docs_linked INTEGER,
                status TEXT,
                start_date TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                project TEXT,
                status TEXT,
                next_followup TEXT,
                action TEXT,
                message TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                role TEXT,
                email TEXT
            );
            """
        )


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _rows(sql: str, params: Iterable[Any] = ()) -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]


def _row(sql: str, params: Iterable[Any] = ()) -> dict | None:
    rows = _rows(sql, params)
    return rows[0] if rows else None


def _execute(sql: str, params: Iterable[Any] = ()) -> int:
    with get_conn() as conn:
        cur = conn.execute(sql, tuple(params))
        return cur.lastrowid


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_opportunities(status: str | None = None) -> list[dict]:
    if status and status != "All":
        return _rows(
            "SELECT * FROM opportunities WHERE status = ? ORDER BY bid_due",
            (status,),
        )
    return _rows("SELECT * FROM opportunities ORDER BY bid_due")


def get_opportunity(opp_id: int) -> dict | None:
    return _row("SELECT * FROM opportunities WHERE id = ?", (opp_id,))


def create_opportunity(data: dict) -> int:
    return _execute(
        """
        INSERT INTO opportunities
        (project, owner, location, project_type, estimated_value, bid_due,
         prebid, estimator, project_manager, status, risk, readiness,
         scope_json, divisions_json, missing_json, next_actions_json,
         notes, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            data.get("project", "Untitled"),
            data.get("owner", ""),
            data.get("location", ""),
            data.get("project_type", ""),
            float(data.get("estimated_value", 0) or 0),
            data.get("bid_due", ""),
            data.get("prebid", ""),
            data.get("estimator", ""),
            data.get("project_manager", ""),
            data.get("status", "New Opportunity"),
            data.get("risk", "Medium"),
            int(data.get("readiness", 50) or 50),
            json.dumps(data.get("scope", [])),
            json.dumps(data.get("divisions", [])),
            json.dumps(data.get("missing", [])),
            json.dumps(data.get("next_actions", [])),
            data.get("notes", ""),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def update_opportunity(opp_id: int, fields: dict) -> None:
    if not fields:
        return
    keys = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [opp_id]
    _execute(f"UPDATE opportunities SET {keys} WHERE id = ?", vals)


def get_scope_items(opp_id: int) -> list[dict]:
    return _rows(
        "SELECT * FROM scope_items WHERE opportunity_id = ? ORDER BY id",
        (opp_id,),
    )


def add_scope_item(opp_id: int, item: dict) -> int:
    return _execute(
        """
        INSERT INTO scope_items
        (opportunity_id, scope, quantity, unit, self_perform, subcontract,
         quote_required, status)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            opp_id,
            item.get("scope", ""),
            float(item.get("quantity", 0) or 0),
            item.get("unit", "LS"),
            item.get("self_perform", "No"),
            item.get("subcontract", "No"),
            item.get("quote_required", "No"),
            item.get("status", "Pending"),
        ),
    )


def update_scope_item(item_id: int, fields: dict) -> None:
    if not fields:
        return
    keys = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [item_id]
    _execute(f"UPDATE scope_items SET {keys} WHERE id = ?", vals)


def get_estimate(opp_id: int) -> dict | None:
    return _row("SELECT * FROM estimates WHERE opportunity_id = ?", (opp_id,))


def upsert_estimate(opp_id: int, fields: dict) -> None:
    existing = get_estimate(opp_id)
    if existing:
        keys = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [opp_id]
        _execute(
            f"UPDATE estimates SET {keys}, updated_at = ? WHERE opportunity_id = ?",
            vals + [datetime.now().isoformat(timespec="seconds")],
        )
    else:
        cols = [
            "labor", "materials", "equipment", "subcontractors",
            "mobilization", "temp_facilities", "supervision",
            "insurance", "permits", "contingency_pct",
            "overhead_pct", "profit_pct",
        ]
        vals = [float(fields.get(c, 0) or 0) for c in cols]
        _execute(
            f"""
            INSERT INTO estimates
            (opportunity_id, {', '.join(cols)}, updated_at)
            VALUES (?, {', '.join(['?'] * len(cols))}, ?)
            """,
            [opp_id] + vals + [datetime.now().isoformat(timespec="seconds")],
        )


def get_subcontractors() -> list[dict]:
    return _rows("SELECT * FROM subcontractors ORDER BY company")


def add_subcontractor(data: dict) -> int:
    return _execute(
        """
        INSERT INTO subcontractors
        (company, trade, contact, email, phone, location, insurance_status,
         w9_status, quote_status, last_contact, projects_worked, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            data.get("company", ""),
            data.get("trade", ""),
            data.get("contact", ""),
            data.get("email", ""),
            data.get("phone", ""),
            data.get("location", ""),
            data.get("insurance_status", "Pending"),
            data.get("w9_status", "Pending"),
            data.get("quote_status", "Invited"),
            data.get("last_contact", ""),
            int(data.get("projects_worked", 0) or 0),
            data.get("notes", ""),
        ),
    )


def update_subcontractor(sub_id: int, fields: dict) -> None:
    if not fields:
        return
    keys = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [sub_id]
    _execute(f"UPDATE subcontractors SET {keys} WHERE id = ?", vals)


def get_vendors() -> list[dict]:
    return _rows("SELECT * FROM vendors ORDER BY company")


def add_vendor(data: dict) -> int:
    return _execute(
        """
        INSERT INTO vendors
        (company, scope, contact, email, phone, location, notes)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            data.get("company", ""),
            data.get("scope", ""),
            data.get("contact", ""),
            data.get("email", ""),
            data.get("phone", ""),
            data.get("location", ""),
            data.get("notes", ""),
        ),
    )


def get_quotes(opp_id: int | None = None) -> list[dict]:
    if opp_id:
        return _rows(
            "SELECT * FROM quotes WHERE opportunity_id = ? ORDER BY amount",
            (opp_id,),
        )
    return _rows("SELECT * FROM quotes ORDER BY received_at DESC")


def create_quote(opp_id: int, data: dict) -> int:
    return _execute(
        """
        INSERT INTO quotes
        (opportunity_id, vendor, scope, amount, lead_time_weeks, validity_days,
         compliance, status, exceptions, received_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            opp_id,
            data.get("vendor", ""),
            data.get("scope", ""),
            float(data.get("amount", 0) or 0),
            int(data.get("lead_time_weeks", 0) or 0),
            int(data.get("validity_days", 30) or 30),
            data.get("compliance", "Complete"),
            data.get("status", "Received"),
            data.get("exceptions", ""),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def update_quote(quote_id: int, fields: dict) -> None:
    if not fields:
        return
    keys = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [quote_id]
    _execute(f"UPDATE quotes SET {keys} WHERE id = ?", vals)


def get_addenda(opp_id: int | None = None) -> list[dict]:
    if opp_id:
        return _rows(
            "SELECT * FROM addenda WHERE opportunity_id = ? ORDER BY number",
            (opp_id,),
        )
    return _rows("SELECT * FROM addenda ORDER BY received_date DESC")


def add_addendum(opp_id: int, number: int, received_date: str,
                 status: str = "Not Reviewed", notes: str = "") -> int:
    return _execute(
        """
        INSERT INTO addenda (opportunity_id, number, received_date, status, notes)
        VALUES (?,?,?,?,?)
        """,
        (opp_id, number, received_date, status, notes),
    )


def update_addendum(add_id: int, fields: dict) -> None:
    if not fields:
        return
    keys = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [add_id]
    _execute(f"UPDATE addenda SET {keys} WHERE id = ?", vals)


def create_activity(opp_id: int | None, message: str,
                    category: str = "general") -> int:
    return _execute(
        """
        INSERT INTO activities (opportunity_id, timestamp, message, category)
        VALUES (?,?,?,?)
        """,
        (
            opp_id,
            datetime.now().isoformat(timespec="seconds"),
            message,
            category,
        ),
    )


def get_activities(opp_id: int | None = None, limit: int = 30) -> list[dict]:
    if opp_id:
        return _rows(
            "SELECT * FROM activities WHERE opportunity_id = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (opp_id, limit),
        )
    return _rows(
        "SELECT * FROM activities ORDER BY timestamp DESC LIMIT ?", (limit,)
    )


def create_notification(level: str, message: str,
                        opp_id: int | None = None) -> int:
    return _execute(
        """
        INSERT INTO notifications (opportunity_id, level, message, created_at)
        VALUES (?,?,?,?)
        """,
        (
            opp_id,
            level,
            message,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def get_notifications(unread_only: bool = False) -> list[dict]:
    if unread_only:
        return _rows(
            "SELECT * FROM notifications WHERE read = 0 "
            "ORDER BY created_at DESC"
        )
    return _rows("SELECT * FROM notifications ORDER BY created_at DESC")


def mark_notification_read(nid: int) -> None:
    _execute("UPDATE notifications SET read = 1 WHERE id = ?", (nid,))


def get_projects() -> list[dict]:
    return _rows("SELECT * FROM projects ORDER BY created_at DESC")


def create_project(data: dict) -> int:
    return _execute(
        """
        INSERT INTO projects
        (opportunity_id, project, owner, location, contract_value,
         project_manager, estimate_linked, subs_linked, vendors_linked,
         docs_linked, status, start_date, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            data.get("opportunity_id"),
            data.get("project", ""),
            data.get("owner", ""),
            data.get("location", ""),
            float(data.get("contract_value", 0) or 0),
            data.get("project_manager", ""),
            int(bool(data.get("estimate_linked", 1))),
            int(bool(data.get("subs_linked", 1))),
            int(bool(data.get("vendors_linked", 1))),
            int(bool(data.get("docs_linked", 1))),
            data.get("status", "Active"),
            data.get("start_date", ""),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def get_followups(opp_id: int | None = None) -> list[dict]:
    if opp_id:
        return _rows(
            "SELECT * FROM followups WHERE opportunity_id = ? "
            "ORDER BY next_followup",
            (opp_id,),
        )
    return _rows("SELECT * FROM followups ORDER BY next_followup")


def create_followup(data: dict) -> int:
    return _execute(
        """
        INSERT INTO followups
        (opportunity_id, project, status, next_followup, action, message,
         created_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            data.get("opportunity_id"),
            data.get("project", ""),
            data.get("status", "Submitted"),
            data.get("next_followup", ""),
            data.get("action", ""),
            data.get("message", ""),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def get_users() -> list[dict]:
    return _rows("SELECT * FROM users ORDER BY name")


def count_rows(table: str) -> int:
    row = _row(f"SELECT COUNT(*) AS c FROM {table}")
    return int(row["c"]) if row else 0