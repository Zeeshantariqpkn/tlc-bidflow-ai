"""Estimating calculations for TLC BidFlow AI (demo-level)."""
from __future__ import annotations


def compute_estimate(est: dict) -> dict:
    """
    Given an estimate dict with direct, indirect, contingency, markup fields,
    return a computed summary.

    Expected keys:
      labor, materials, equipment, subcontractors,
      mobilization, temp_facilities, supervision, insurance, permits,
      contingency_pct, overhead_pct, profit_pct
    """
    direct = (
        float(est.get("labor", 0) or 0)
        + float(est.get("materials", 0) or 0)
        + float(est.get("equipment", 0) or 0)
        + float(est.get("subcontractors", 0) or 0)
    )
    indirect = (
        float(est.get("mobilization", 0) or 0)
        + float(est.get("temp_facilities", 0) or 0)
        + float(est.get("supervision", 0) or 0)
        + float(est.get("insurance", 0) or 0)
        + float(est.get("permits", 0) or 0)
    )
    contingency_pct = float(est.get("contingency_pct", 0) or 0)
    contingency = (direct + indirect) * (contingency_pct / 100.0)
    total_cost = direct + indirect + contingency

    overhead_pct = float(est.get("overhead_pct", 0) or 0)
    profit_pct = float(est.get("profit_pct", 0) or 0)
    markup = total_cost * ((overhead_pct + profit_pct) / 100.0)
    final_bid = total_cost + markup

    gross_margin = 0.0
    if final_bid > 0:
        gross_margin = (final_bid - total_cost) / final_bid * 100.0

    return {
        "direct_cost": direct,
        "indirect_cost": indirect,
        "contingency": contingency,
        "total_cost": total_cost,
        "markup": markup,
        "final_bid": final_bid,
        "gross_margin": gross_margin,
        "contingency_pct": contingency_pct,
        "overhead_pct": overhead_pct,
        "profit_pct": profit_pct,
    }


def readiness_score(scope_cov: float, quote_cov: float,
                    material_cov: float, risk_cov: float) -> float:
    """Weighted readiness 0-100."""
    return round(
        scope_cov * 0.35 + quote_cov * 0.25 + material_cov * 0.2
        + risk_cov * 0.2,
        0,
    )


def estimate_health(scope_items: list[dict], quotes: list[dict]) -> dict:
    """Return a dict of coverage percentages + warnings."""
    total_scope = max(len(scope_items), 1)
    ready = sum(1 for s in scope_items if s.get("status") == "Ready")
    scope_cov = ready / total_scope * 100

    quote_scope = [s for s in scope_items if s.get("quote_required") == "Yes"]
    total_quote_scope = max(len(quote_scope), 1)
    received = sum(
        1 for s in quote_scope
        if any(q.get("scope") == s.get("scope")
               and q.get("status") == "Received" for q in quotes)
    )
    quote_cov = received / total_quote_scope * 100

    material_cov = 81.0
    risk_cov = 72.0
    completeness = (scope_cov + quote_cov + material_cov + risk_cov) / 4

    warnings = []
    if quote_cov < 100:
        warnings.append("Electrical subcontractor pricing is still pending.")
    if material_cov < 90:
        warnings.append("Equipment pricing has not been confirmed.")
    if any(s.get("status") in ("Needs Review", "Not Reviewed")
           for s in scope_items):
        warnings.append("Latest addendum has not been reviewed.")
    if not warnings:
        warnings.append("No open estimate warnings in the demo dataset.")

    return {
        "scope_coverage": round(scope_cov, 0),
        "quote_coverage": round(quote_cov, 0),
        "material_coverage": round(material_cov, 0),
        "risk_coverage": round(risk_cov, 0),
        "completeness": round(completeness, 0),
        "warnings": warnings,
    }


def compare_quotes(quotes: list[dict]) -> list[dict]:
    """
    Return quotes with comparison fields. Does NOT simply recommend the
    cheapest vendor — surfaces price, coverage, lead time, compliance,
    completeness, exceptions.
    """
    if not quotes:
        return []
    valid = [q for q in quotes if q.get("amount", 0) > 0]
    if not valid:
        return []
    lowest = min(q["amount"] for q in valid)
    out = []
    for q in quotes:
        amount = q.get("amount", 0) or 0
        delta = amount - lowest if amount else 0
        out.append({
            **q,
            "delta_vs_low": delta,
            "price_rank": "Lowest" if delta == 0 and amount > 0 else "Higher",
            "lead_time_weeks": q.get("lead_time_weeks", 0),
            "compliance": q.get("compliance", ""),
            "completeness": (
                "Complete" if q.get("compliance") == "Complete"
                else "Incomplete"
            ),
            "exceptions": q.get("exceptions", "None"),
        })
    return out