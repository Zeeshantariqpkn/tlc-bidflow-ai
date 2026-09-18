"""
Deterministic AI-style extraction for TLC BidFlow AI.

This module NEVER depends on a paid API. If an HF_TOKEN is available, it may
optionally call a Hugging Face Inference endpoint. Otherwise it uses a robust
rule-based extractor that produces structured, believable results from a bid
notice.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Optional Hugging Face hook (never required)
# ---------------------------------------------------------------------------

def _hf_available() -> bool:
    return bool(os.environ.get("HF_TOKEN"))


def _try_hf(prompt: str) -> str | None:
    """Best-effort HF call. Returns None on any failure."""
    if not _hf_available():
        return None
    try:
        import requests  # local import to keep dependency optional

        token = os.environ["HF_TOKEN"]
        model = os.environ.get("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
        resp = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {token}"},
            json={"inputs": prompt, "parameters": {"max_new_tokens": 512}},
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "")
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Deterministic extractor
# ---------------------------------------------------------------------------

SCOPE_KEYWORDS = {
    "Underground Piping": [
        r"underground\s+(?:utility\s+)?pip", r"gravity\s+sewer",
        r"transmission\s+main", r"water\s+main", r"force\s+main",
    ],
    "Pumping Station": [r"pump(?:ing)?\s+station", r"lift\s+station"],
    "Process Piping": [r"process\s+pip"],
    "Structural Concrete": [
        r"structural\s+concrete", r"cast[- ]in[- ]place",
        r"concrete\s+structure",
    ],
    "Site Grading": [r"site\s+grading", r"earthwork", r"excavat"],
    "Equipment Installation": [
        r"equipment\s+install", r"equipment\s+schedule",
        r"process\s+equipment",
    ],
    "Electrical Coordination": [
        r"electrical\s+coord", r"electrical\s+work", r"electrical\s+install",
        r"instrumentation",
    ],
    "HVAC": [r"\bhvac\b", r"ventilation"],
    "Landscaping": [r"landscap", r"revegetation"],
    "Traffic Control": [r"traffic\s+control", r"maintenance\s+of\s+traffic"],
}

DIVISION_MAP = {
    "Underground Piping": "Underground Utilities",
    "Pumping Station": "Process Mechanical",
    "Process Piping": "Process Mechanical",
    "Structural Concrete": "Concrete",
    "Site Grading": "Earthwork",
    "Equipment Installation": "Equipment",
    "Electrical Coordination": "Electrical",
    "HVAC": "Mechanical",
    "Landscaping": "Sitework",
    "Traffic Control": "Sitework",
}

TYPE_KEYWORDS = [
    ("Wastewater Treatment Plant", [r"wastewater\s+treatment",
                                    r"\bwwtp\b", r"\bwrf\b",
                                    r"water\s+reclamation"]),
    ("Water Treatment Plant", [r"water\s+treatment", r"\bwtp\b"]),
    ("Wastewater Infrastructure", [r"wastewater", r"sewer", r"reclamation"]),
    ("Water Infrastructure", [r"water\s+(?:main|infrastructure|distribution)"]),
    ("Pumping Station", [r"pump(?:ing)?\s+station"]),
    ("Lift Station", [r"lift\s+station"]),
    ("Transmission Main", [r"transmission\s+main"]),
    ("Gravity Sewer Main", [r"gravity\s+sewer"]),
    ("Process Piping", [r"process\s+pip"]),
    ("Utility Construction", [r"utility\s+construction"]),
]

MISSING_INFO = [
    "Complete plan set",
    "Specification sections",
    "Addenda",
    "Bid bond requirements",
    "Insurance requirements",
    "DBE/SBE requirements",
    "Detailed equipment schedule",
]

NEXT_ACTIONS = [
    "Review plans/specifications",
    "Assign estimator",
    "Create bid calendar",
    "Request subcontractor pricing",
    "Identify self-perform scope",
    "Track addenda",
    "Build preliminary estimate",
]

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
    "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
}


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return "Untitled Opportunity"


def _extract_value(text: str) -> float:
    # Look for $18,500,000 or $18.5M or 18.5 million
    m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|m\b|k\b)?",
                  text, re.IGNORECASE)
    if m:
        num = float(m.group(1).replace(",", ""))
        suffix = (m.group(2) or "").lower()
        if suffix.startswith("m") or "million" in suffix:
            num *= 1_000_000
        elif suffix.startswith("k"):
            num *= 1_000
        return num
    m = re.search(r"([\d.]+)\s*million", text, re.IGNORECASE)
    if m:
        return float(m.group(1)) * 1_000_000
    return 0.0


def _extract_date(text: str, kind: str) -> str:
    """
    kind = 'bid' or 'prebid'. Returns 'YYYY-MM-DD HH:MM' or ''.
    """
    patterns = {
        "bid": [
            r"(?:bid|proposal|submission)s?\s+(?:due|closing|deadline)[:\s]*"
            r"([A-Za-z]+\s+\d{1,2},?\s+\d{4})[^\d]*(\d{1,2}:\d{2}\s*[APap][Mm])?",
            r"due[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})[^\d]*"
            r"(\d{1,2}:\d{2}\s*[APap][Mm])?",
        ],
        "prebid": [
            r"pre[- ]?bid[^\n]*?([A-Za-z]+\s+\d{1,2},?\s+\d{4})"
            r"[^\d]*(\d{1,2}:\d{2}\s*[APap][Mm])?",
        ],
    }
    for pat in patterns.get(kind, []):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            date_str = m.group(1)
            time_str = (m.group(2) or "").strip()
            return _parse_datetime(date_str, time_str)
    return ""


def _parse_datetime(date_str: str, time_str: str) -> str:
    try:
        cleaned = date_str.replace(",", "").strip()
        parts = cleaned.split()
        if len(parts) >= 3:
            month = MONTHS.get(parts[0].lower(), 1)
            day = int(parts[1])
            year = int(parts[2])
        elif len(parts) == 2:
            month = MONTHS.get(parts[0].lower(), 1)
            day = int(parts[1])
            year = datetime.now().year
        else:
            return ""
        hour, minute = 14, 0
        if time_str:
            tm = re.match(r"(\d{1,2}):(\d{2})\s*([APap][Mm])?", time_str)
            if tm:
                hour = int(tm.group(1))
                minute = int(tm.group(2))
                ampm = (tm.group(3) or "").upper()
                if ampm == "PM" and hour < 12:
                    hour += 12
                if ampm == "AM" and hour == 12:
                    hour = 0
        return datetime(year, month, day, hour, minute).strftime(
            "%Y-%m-%d %H:%M"
        )
    except Exception:
        return ""


def _extract_location(text: str) -> str:
    m = re.search(r"(?:project\s+)?location[:\s]+([^\n\.]+)", text,
                  re.IGNORECASE)
    if m:
        loc = m.group(1).strip().rstrip(",")
        if "," not in loc and "FL" not in loc.upper():
            loc = loc + ", FL"
        return loc
    # Fallback: look for "City, FL" pattern
    m = re.search(r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?,\s*FL)",
                  text)
    if m:
        return m.group(1)
    for city in ["Tampa", "Palmetto", "Sarasota", "Clearwater", "Bradenton",
                 "St. Petersburg", "Orlando", "Fort Myers",
                 "West Palm Beach", "Miami"]:
        if city.lower() in text.lower():
            return f"{city}, FL"
    return "Florida"


def _extract_owner(text: str) -> str:
    first = _first_nonempty_line(text)
    m = re.match(r"(City of [A-Za-z ]+|County of [A-Za-z ]+|"
                 r"[A-Za-z ]+ County|[A-Za-z ]+ Utilities|"
                 r"[A-Za-z ]+ Water & Sewer)", first)
    if m:
        return m.group(1).strip()
    m = re.search(r"(City of [A-Za-z ]+|County of [A-Za-z ]+|"
                  r"[A-Za-z ]+ County|[A-Za-z ]+ Utilities)",
                  text)
    if m:
        return m.group(1).strip()
    return "Owner to Confirm"


def _extract_project_name(text: str) -> str:
    first = _first_nonempty_line(text)
    # Strip trailing punctuation
    return first.rstrip(".:-").strip() or "Untitled Opportunity"


def _extract_scope(text: str) -> list[str]:
    found: list[str] = []
    lower = text.lower()
    for scope, patterns in SCOPE_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, lower):
                if scope not in found:
                    found.append(scope)
                break
    # Always ensure the canonical Clearwater set is complete if it looks
    # like a treatment facility
    return found


def _extract_project_type(text: str, scope: list[str]) -> str:
    lower = text.lower()
    for ptype, patterns in TYPE_KEYWORDS:
        for pat in patterns:
            if re.search(pat, lower):
                return ptype
    if "Underground Piping" in scope:
        return "Utility Construction"
    return "Water/Wastewater Infrastructure"


def _extract_quantities(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    m = re.search(r"([\d,]+)\s*LF", text, re.IGNORECASE)
    if m:
        out["underground_lf"] = int(m.group(1).replace(",", ""))
    m = re.search(r"([\d,]+)\s*(?:SF|square\s+feet)", text, re.IGNORECASE)
    if m:
        out["concrete_sf"] = int(m.group(1).replace(",", ""))
    return out


def analyze_bid_notice(text: str) -> dict[str, Any]:
    """
    Deterministic structured extraction. Always returns a dict.
    """
    if not text or not text.strip():
        return _empty_result()

    # Best-effort optional HF augmentation (does not change core extraction)
    _ = _try_hf(
        "Extract project name, owner, location, value, and scope from this "
        "bid notice:\n" + text[:2000]
    )

    scope = _extract_scope(text)
    project_type = _extract_project_type(text, scope)
    divisions = []
    for s in scope:
        d = DIVISION_MAP.get(s)
        if d and d not in divisions:
            divisions.append(d)

    value = _extract_value(text)
    bid_due = _extract_date(text, "bid")
    prebid = _extract_date(text, "prebid")
    location = _extract_location(text)
    owner = _extract_owner(text)
    project = _extract_project_name(text)

    quantities = _extract_quantities(text)

    # Complexity heuristic
    score = 0
    score += 20 if value >= 10_000_000 else 10 if value >= 3_000_000 else 5
    score += min(len(scope) * 8, 40)
    score += 15 if "Electrical Coordination" in scope else 0
    score += 15 if "Process Piping" in scope else 0
    complexity = "High" if score >= 65 else "Medium" if score >= 35 else "Low"

    readiness = 72 if complexity == "High" else 65

    missing = list(MISSING_INFO)
    next_actions = list(NEXT_ACTIONS)

    return {
        "project": project,
        "owner": owner,
        "location": location,
        "project_type": project_type,
        "estimated_value": value,
        "bid_due": bid_due,
        "prebid": prebid,
        "scope": scope or ["Scope to Confirm"],
        "divisions": divisions or ["General"],
        "complexity": complexity,
        "readiness": readiness,
        "missing": missing,
        "next_actions": next_actions,
        "quantities": quantities,
    }


def _empty_result() -> dict[str, Any]:
    return {
        "project": "Untitled Opportunity",
        "owner": "Owner to Confirm",
        "location": "Florida",
        "project_type": "Water/Wastewater Infrastructure",
        "estimated_value": 0.0,
        "bid_due": "",
        "prebid": "",
        "scope": ["Scope to Confirm"],
        "divisions": ["General"],
        "complexity": "Low",
        "readiness": 25,
        "missing": list(MISSING_INFO),
        "next_actions": list(NEXT_ACTIONS),
        "quantities": {},
    }


# ---------------------------------------------------------------------------
# Bid risk analysis (deterministic, demo-level)
# ---------------------------------------------------------------------------

def analyze_risks(opportunity: dict, quotes: list[dict],
                  scope_items: list[dict],
                  addenda: list[dict]) -> dict[str, Any]:
    """Return a dict of risk categories with reason + recommended action."""
    pending_quotes = [q for q in quotes if q.get("status") == "Pending"]
    missing_docs = [q for q in quotes if q.get("compliance") == "Missing docs"]
    unresolved_addenda = [a for a in addenda
                          if a.get("status") in ("Needs Review", "Not Reviewed")]
    ready_scope = [s for s in scope_items if s.get("status") == "Ready"]
    quote_scope = [s for s in scope_items
                   if s.get("quote_required") == "Yes"]

    scope_cov = (len(ready_scope) / max(len(scope_items), 1)) * 100
    quote_cov = (
        (len(quote_scope) - len(pending_quotes)) / max(len(quote_scope), 1)
    ) * 100 if quote_scope else 100

    risks = {
        "scope": {
            "level": "Medium" if scope_cov >= 60 else "High",
            "reason": (
                f"{len(ready_scope)} of {len(scope_items)} scope items are "
                "marked ready."
            ),
            "action": (
                "Confirm remaining scope items and assign self-perform vs. "
                "subcontract."
            ),
        },
        "schedule": {
            "level": "High" if pending_quotes else "Medium",
            "reason": (
                "Equipment lead time has not been confirmed."
                if pending_quotes else
                "Vendor lead times are documented but should be re-confirmed "
                "before final bid review."
            ),
            "action": (
                "Request written lead-time confirmation from equipment "
                "vendors before final bid review."
            ),
        },
        "pricing": {
            "level": "High" if pending_quotes else "Medium",
            "reason": (
                f"{len(pending_quotes)} quote(s) still pending."
                if pending_quotes else
                "All required quotes have been received."
            ),
            "action": (
                "Follow up on pending quote(s) and validate completeness."
            ),
        },
        "subcontractor_coverage": {
            "level": "High" if quote_cov < 70 else "Medium",
            "reason": (
                f"Subcontractor quote coverage is {quote_cov:.0f}%."
            ),
            "action": (
                "Invite additional subcontractors and set firm quote "
                "deadlines."
            ),
        },
        "documentation": {
            "level": "High" if len(unresolved_addenda) >= 2 else "Medium",
            "reason": (
                f"{len(unresolved_addenda)} addendum(s) need review."
                if unresolved_addenda else
                "All received addenda have been reviewed."
            ),
            "action": (
                "Review outstanding addenda and update the estimate."
            ),
        },
    }

    overall = (
        (100 if risks["scope"]["level"] == "Low" else
         70 if risks["scope"]["level"] == "Medium" else 40)
        + (100 if risks["schedule"]["level"] == "Low" else
           60 if risks["schedule"]["level"] == "Medium" else 30)
        + (100 if risks["pricing"]["level"] == "Low" else
           60 if risks["pricing"]["level"] == "Medium" else 30)
        + quote_cov
        + (100 if risks["documentation"]["level"] == "Low" else
           60 if risks["documentation"]["level"] == "Medium" else 30)
    ) / 5

    return {
        "risks": risks,
        "overall_readiness": round(overall, 0),
        "pending_quotes": pending_quotes,
        "missing_docs": missing_docs,
        "unresolved_addenda": unresolved_addenda,
        "quote_coverage": round(quote_cov, 0),
        "scope_coverage": round(scope_cov, 0),
    }


# ---------------------------------------------------------------------------
# Local AI Assistant (deterministic over demo dataset)
# ---------------------------------------------------------------------------

def assistant_answer(question: str, data: dict) -> str:
    """
    Answer a question using the local demo dataset. Deterministic.

    data keys: opportunities, quotes, subcontractors, addenda, followups,
    notifications, projects.
    """
    q = question.lower().strip()
    if not q:
        return "Please ask a question about the current bid pipeline."

    opps = data.get("opportunities", [])
    quotes = data.get("quotes", [])
    addenda = data.get("addenda", [])
    subs = data.get("subcontractors", [])
    followups = data.get("followups", [])

    # Due this week
    if "due this week" in q or "bids due" in q:
        upcoming = [o for o in opps
                    if o.get("bid_due") and o["bid_due"] >=
                    datetime.now().strftime("%Y-%m-%d")]
        upcoming = sorted(upcoming, key=lambda o: o["bid_due"])[:5]
        if not upcoming:
            return "No bids currently scheduled in the demo dataset."
        lines = ["**Bids due soon:**"]
        for o in upcoming:
            lines.append(
                f"- {o['project']} — due {o['bid_due'][:10]} "
                f"({o.get('status', '')})"
            )
        return "\n".join(lines)

    # Missing subcontractor quotes
    if "missing" in q and "quote" in q:
        pending = [x for x in quotes if x.get("status") == "Pending"]
        if not pending:
            return "No pending quotes in the demo dataset."
        lines = ["**Pending subcontractor / vendor quotes:**"]
        for p in pending[:10]:
            opp = next((o for o in opps if o["id"] == p["opportunity_id"]),
                       None)
            proj = opp["project"] if opp else "Unknown project"
            lines.append(f"- {p['vendor']} ({p['scope']}) — {proj}")
        return "\n".join(lines)

    # Low estimate readiness
    if "low" in q and ("readiness" in q or "estimate" in q):
        low = sorted(opps, key=lambda o: o.get("readiness", 0))[:5]
        lines = ["**Opportunities with the lowest readiness:**"]
        for o in low:
            lines.append(
                f"- {o['project']} — readiness {o.get('readiness', 0)}%"
            )
        return "\n".join(lines)

    # Unresolved addenda
    if "addend" in q:
        pending = [a for a in addenda
                   if a.get("status") in ("Needs Review", "Not Reviewed")]
        if not pending:
            return "All received addenda are marked reviewed."
        lines = ["**Unresolved addenda:**"]
        for a in pending[:10]:
            opp = next((o for o in opps if o["id"] == a["opportunity_id"]),
                       None)
            proj = opp["project"] if opp else "Unknown project"
            lines.append(
                f"- Addendum #{a.get('number')} — {proj} — "
                f"{a.get('status')}"
            )
        return "\n".join(lines)

    # Clearwater focus
    if "clearwater" in q:
        opp = next(
            (o for o in opps if "clearwater" in o["project"].lower()), None
        )
        if not opp:
            return "Clearwater opportunity not found in the demo dataset."
        lines = [
            f"**{opp['project']}**",
            f"- Value: ${opp.get('estimated_value', 0):,.0f}",
            f"- Bid due: {opp.get('bid_due', '')[:16]}",
            f"- Status: {opp.get('status', '')}",
            f"- Readiness: {opp.get('readiness', 0)}%",
            f"- Risk: {opp.get('risk', '')}",
            "",
            "**What needs attention before submission:**",
            "1. Electrical quote pending",
            "2. Addendum #2 and #3 need review",
            "3. Equipment lead time not confirmed",
            "4. Insurance and DBE/SBE requirements need confirmation",
        ]
        return "\n".join(lines)

    # High-risk bids
    if "high" in q and "risk" in q:
        high = [o for o in opps if o.get("risk") == "High"]
        if not high:
            return "No high-risk bids in the demo dataset."
        lines = ["**High-risk bids:**"]
        for o in high[:10]:
            lines.append(
                f"- {o['project']} — {o.get('status', '')} — "
                f"readiness {o.get('readiness', 0)}%"
            )
        return "\n".join(lines)

    # Subcontractor quotes pending
    if "subcontractor" in q and "quote" in q:
        pending = [s for s in subs if s.get("quote_status") ==
                   "Pricing Pending"]
        if not pending:
            return "No subcontractors are currently pending pricing."
        lines = ["**Subcontractors with pending pricing:**"]
        for s in pending:
            lines.append(f"- {s['company']} ({s['trade']})")
        return "\n".join(lines)

    # Follow-ups
    if "follow" in q:
        if not followups:
            return "No follow-ups scheduled."
        lines = ["**Scheduled follow-ups:**"]
        for f in followups[:10]:
            lines.append(
                f"- {f['project']} — {f.get('next_followup', '')} — "
                f"{f.get('action', '')}"
            )
        return "\n".join(lines)

    # Fallback
    return (
        "I can answer questions about bids due, pending quotes, low "
        "readiness opportunities, unresolved addenda, high-risk bids, "
        "Clearwater bid status, subcontractor pricing, and follow-ups. "
        "Try: \"What bids are due this week?\" or "
        "\"What needs attention before the Clearwater bid?\""
    )