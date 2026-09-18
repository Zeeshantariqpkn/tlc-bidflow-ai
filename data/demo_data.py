"""
Fictional demo dataset for TLC BidFlow AI.

Everything in this file is synthetic. No real TLC Diversified, Inc. projects,
vendors, subcontractors, or figures are represented.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from data import database as db

# ---------------------------------------------------------------------------
# Florida locations used across the demo
# ---------------------------------------------------------------------------
LOCATIONS = [
    "Tampa, FL", "Palmetto, FL", "Sarasota, FL", "Clearwater, FL",
    "Bradenton, FL", "St. Petersburg, FL", "Orlando, FL", "Fort Myers, FL",
    "West Palm Beach, FL", "Miami, FL",
]

PROJECT_TYPES = [
    "Wastewater Infrastructure",
    "Water Infrastructure",
    "Water Treatment Plant",
    "Wastewater Treatment Plant",
    "Pumping Station",
    "Lift Station",
    "Transmission Main",
    "Gravity Sewer Main",
    "Process Piping",
    "Utility Construction",
]

OWNERS = [
    "City of Clearwater",
    "City of Tampa",
    "Manatee County",
    "Sarasota County",
    "City of Bradenton",
    "Pinellas County",
    "City of Orlando",
    "Lee County Utilities",
    "Palm Beach County",
    "Miami-Dade Water & Sewer",
    "City of Palmetto",
    "City of St. Petersburg",
]

ESTIMATORS = [
    "Michael Carter",
    "Priya Raman",
    "Daniel Okafor",
    "Sofia Alvarez",
    "Jason Whitfield",
    "Anna Kowalski",
]

PMS = [
    "Robert Nguyen",
    "Karen Delgado",
    "Thomas Brennan",
    "Lisa Park",
]

STATUSES = [
    "New Opportunity", "Under Review", "Qualified", "Estimating",
    "Quotes Pending", "Bid Review", "Submitted", "Awarded", "Lost",
]

RISKS = ["Low", "Medium", "High"]


def _d(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def _dt(days: int, hour: int = 14, minute: int = 0) -> str:
    return (datetime.now() + timedelta(days=days)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    ).strftime("%Y-%m-%d %H:%M")


def seed_demo_data() -> None:
    """Populate the database with fictional demo data (idempotent)."""
    if db.count_rows("opportunities") > 0:
        return

    _seed_users()
    _seed_opportunities()
    _seed_scope_items()
    _seed_subcontractors()
    _seed_vendors()
    _seed_quotes()
    _seed_addenda()
    _seed_activities()
    _seed_notifications()
    _seed_followups()
    _seed_projects()


def _seed_users() -> None:
    for name, role in [
        ("Michael Carter", "Chief Estimator"),
        ("Priya Raman", "Senior Estimator"),
        ("Daniel Okafor", "Estimator"),
        ("Sofia Alvarez", "Estimator"),
        ("Jason Whitfield", "Preconstruction Manager"),
        ("Anna Kowalski", "Bid Coordinator"),
    ]:
        db._execute(
            "INSERT INTO users (name, role, email) VALUES (?,?,?)",
            (name, role, name.lower().replace(" ", ".") + "@demo-tlc.example"),
        )


# The flagship demo opportunity text for the AI Bid Intake page
CLEARWATER_TEXT = """City of Clearwater Water Reclamation Facility Improvements

The City is requesting bids for improvements to an existing wastewater treatment facility. The project includes approximately 8,500 LF of underground utility piping, a new wastewater pumping station, process piping modifications, structural concrete, site grading, electrical coordination, and equipment installation.

Estimated construction value: $18,500,000.

Bid due: October 28, 2026 at 2:00 PM.

Pre-bid meeting: October 7, 2026 at 10:00 AM.

Project location: Clearwater, Florida.

The project requires coordination with multiple subcontractors and suppliers. Interested firms should review the complete plans and specifications before submitting pricing."""


def _seed_opportunities() -> None:
    # The Clearwater flagship opportunity — always id = 1
    clearwater_scope = [
        "Underground Piping",
        "Pumping Station",
        "Process Piping",
        "Structural Concrete",
        "Site Grading",
        "Equipment Installation",
        "Electrical Coordination",
    ]
    clearwater_divisions = [
        "Underground Utilities", "Concrete", "Process Mechanical",
        "Earthwork", "Electrical", "Equipment",
    ]
    clearwater_missing = [
        "Complete plan set", "Specification sections", "Addenda",
        "Bid bond requirements", "Insurance requirements",
        "DBE/SBE requirements", "Detailed equipment schedule",
    ]
    clearwater_actions = [
        "Review plans/specifications",
        "Assign estimator",
        "Create bid calendar",
        "Request subcontractor pricing",
        "Identify self-perform scope",
        "Track addenda",
        "Build preliminary estimate",
    ]
    db.create_opportunity({
        "project": "City of Clearwater Water Reclamation Facility Improvements",
        "owner": "City of Clearwater",
        "location": "Clearwater, FL",
        "project_type": "Wastewater Infrastructure",
        "estimated_value": 18_500_000,
        "bid_due": "2026-10-28 14:00",
        "prebid": "2026-10-07 10:00",
        "estimator": "Michael Carter",
        "project_manager": "Robert Nguyen",
        "status": "Estimating",
        "risk": "High",
        "readiness": 72,
        "scope": clearwater_scope,
        "divisions": clearwater_divisions,
        "missing": clearwater_missing,
        "next_actions": clearwater_actions,
        "notes": "Flagship demo opportunity.",
    })

    # Generate 24 additional fictional opportunities
    projects = [
        ("Palmetto Water Treatment Plant Expansion", "City of Palmetto",
         "Palmetto, FL", "Water Treatment Plant", 12_400_000),
        ("Sarasota Lift Station No. 14 Rehabilitation", "Sarasota County",
         "Sarasota, FL", "Lift Station", 3_200_000),
        ("Tampa Bay Transmission Main Segment 3", "City of Tampa",
         "Tampa, FL", "Transmission Main", 22_800_000),
        ("Bradenton Gravity Sewer Replacement", "City of Bradenton",
         "Bradenton, FL", "Gravity Sewer Main", 6_750_000),
        ("Pinellas County Pumping Station Upgrade", "Pinellas County",
         "St. Petersburg, FL", "Pumping Station", 9_100_000),
        ("Orlando WRF Process Piping Modifications", "City of Orlando",
         "Orlando, FL", "Process Piping", 7_400_000),
        ("Lee County Utility Extension Phase 2", "Lee County Utilities",
         "Fort Myers, FL", "Utility Construction", 14_200_000),
        ("West Palm Beach Water Main Replacement", "Palm Beach County",
         "West Palm Beach, FL", "Water Infrastructure", 5_600_000),
        ("Miami-Dade Wastewater Rehab Program", "Miami-Dade Water & Sewer",
         "Miami, FL", "Wastewater Infrastructure", 28_500_000),
        ("Clearwater Beach Lift Station Improvements", "City of Clearwater",
         "Clearwater, FL", "Lift Station", 4_300_000),
        ("Manatee County WRF Aeration Upgrade", "Manatee County",
         "Bradenton, FL", "Wastewater Treatment Plant", 11_900_000),
        ("Sarasota Transmission Main Crossing", "Sarasota County",
         "Sarasota, FL", "Transmission Main", 8_700_000),
        ("Tampa Heights Utility Relocation", "City of Tampa",
         "Tampa, FL", "Utility Construction", 2_950_000),
        ("St. Petersburg Water Treatment Filter Rehab", "City of St. Petersburg",
         "St. Petersburg, FL", "Water Treatment Plant", 6_100_000),
        ("Palmetto Force Main Replacement", "City of Palmetto",
         "Palmetto, FL", "Gravity Sewer Main", 3_850_000),
        ("Orlando Southeast Pumping Station", "City of Orlando",
         "Orlando, FL", "Pumping Station", 5_200_000),
        ("Fort Myers Beach Utility Restoration", "Lee County Utilities",
         "Fort Myers, FL", "Utility Construction", 7_800_000),
        ("West Palm WRF Digester Improvements", "Palm Beach County",
         "West Palm Beach, FL", "Wastewater Treatment Plant", 16_300_000),
        ("Miami Central Lift Station No. 7", "Miami-Dade Water & Sewer",
         "Miami, FL", "Lift Station", 4_950_000),
        ("Clearwater East Water Main Extension", "City of Clearwater",
         "Clearwater, FL", "Water Infrastructure", 3_400_000),
        ("Manatee County Process Piping Upgrade", "Manatee County",
         "Bradenton, FL", "Process Piping", 9_600_000),
        ("Sarasota County Reclaimed Water Main", "Sarasota County",
         "Sarasota, FL", "Water Infrastructure", 6_700_000),
        ("Tampa Wastewater Treatment Phase 4", "City of Tampa",
         "Tampa, FL", "Wastewater Treatment Plant", 19_400_000),
        ("Pinellas Park Utility Improvements", "Pinellas County",
         "St. Petersburg, FL", "Utility Construction", 4_100_000),
    ]

    for i, (proj, owner, loc, ptype, value) in enumerate(projects):
        status = STATUSES[i % len(STATUSES)]
        risk = RISKS[i % len(RISKS)]
        readiness = 45 + (i * 3) % 50
        db.create_opportunity({
            "project": proj,
            "owner": owner,
            "location": loc,
            "project_type": ptype,
            "estimated_value": value,
            "bid_due": _dt(3 + i * 2, 14, 0),
            "prebid": _dt(-2 + i * 2, 10, 0),
            "estimator": ESTIMATORS[i % len(ESTIMATORS)],
            "project_manager": PMS[i % len(PMS)],
            "status": status,
            "risk": risk,
            "readiness": readiness,
            "scope": ["Underground Piping", "Concrete", "Mechanical"],
            "divisions": ["Underground Utilities", "Concrete",
                          "Process Mechanical"],
            "missing": ["Addenda", "Insurance requirements"],
            "next_actions": ["Review plans", "Assign estimator"],
        })


def _seed_scope_items() -> None:
    # Scope items for the Clearwater flagship (opp 1)
    rows = [
        ("Underground Piping", 8500, "LF", "Yes", "No", "No", "Ready"),
        ("Structural Concrete", 1, "LS", "Yes", "No", "No", "Ready"),
        ("Process Piping", 1, "LS", "Partial", "Yes", "Yes", "Quotes Pending"),
        ("Electrical", 1, "LS", "No", "Yes", "Yes", "Pending"),
        ("Earthwork", 1, "LS", "Yes", "No", "No", "Ready"),
        ("Equipment", 1, "LS", "No", "Yes", "Yes", "Pending"),
    ]
    for r in rows:
        db.add_scope_item(1, {
            "scope": r[0], "quantity": r[1], "unit": r[2],
            "self_perform": r[3], "subcontract": r[4],
            "quote_required": r[5], "status": r[6],
        })

    # A few for other opportunities
    for opp_id in range(2, 6):
        for r in rows[:3]:
            db.add_scope_item(opp_id, {
                "scope": r[0], "quantity": r[1], "unit": r[2],
                "self_perform": r[3], "subcontract": r[4],
                "quote_required": r[5], "status": r[6],
            })


def _seed_subcontractors() -> None:
    subs = [
        ("Gulf Coast Electrical Contractors", "Electrical", "Tom Reyes",
         "tom@gcec-demo.example", "813-555-0101", "Tampa, FL",
         "Complete", "Complete", "Quote Received"),
        ("Sunshine Mechanical Services", "Mechanical", "Maria Lopez",
         "maria@sms-demo.example", "941-555-0134", "Sarasota, FL",
         "Complete", "Complete", "Quote Received"),
        ("Bay Area Process Piping", "Process Piping", "Kevin Doyle",
         "kevin@bapp-demo.example", "727-555-0177", "Clearwater, FL",
         "Complete", "Pending", "Pricing Pending"),
        ("Manatee Concrete Structures", "Concrete", "Deborah Voss",
         "deb@mcs-demo.example", "941-555-0192", "Bradenton, FL",
         "Complete", "Complete", "Selected"),
        ("Precision Survey Group", "Survey", "Alan Whitcomb",
         "alan@psg-demo.example", "813-555-0155", "Tampa, FL",
         "Complete", "Complete", "Quote Received"),
        ("Central FL HVAC & Controls", "HVAC", "Nina Patel",
         "nina@cfhc-demo.example", "407-555-0121", "Orlando, FL",
         "Pending", "Complete", "Invited"),
        ("Specialty Process Equipment Co.", "Specialty Equipment",
         "Greg Hammond", "greg@spec-demo.example", "305-555-0166",
         "Miami, FL", "Complete", "Complete", "Clarification Needed"),
        ("SafeWay Traffic Control", "Traffic Control", "Carla Jimenez",
         "carla@safeway-demo.example", "954-555-0143", "West Palm Beach, FL",
         "Complete", "Complete", "Not Selected"),
        ("Evergreen Landscape & Restoration", "Landscaping", "Peter Cho",
         "peter@evergreen-demo.example", "239-555-0188", "Fort Myers, FL",
         "Complete", "Pending", "Plans Sent"),
        ("Tampa Bay Dewatering", "Other", "Sam Ortega",
         "sam@tbd-demo.example", "813-555-0102", "Tampa, FL",
         "Complete", "Complete", "Quote Received"),
        ("Suncoast Instrumentation", "Electrical", "Rita Alvarez",
         "rita@suncoast-demo.example", "727-555-0170", "St. Petersburg, FL",
         "Complete", "Complete", "Invited"),
        ("Palmetto Steel Erectors", "Concrete", "Hector Morales",
         "hector@pse-demo.example", "941-555-0125", "Palmetto, FL",
         "Complete", "Complete", "Quote Received"),
        ("Sarasota Process Controls", "Mechanical", "Liz Fenwick",
         "liz@spc-demo.example", "941-555-0133", "Sarasota, FL",
         "Pending", "Complete", "Invited"),
        ("East Coast Millwrights", "Specialty Equipment", "Dwayne Carter",
         "dwayne@ecm-demo.example", "561-555-0147", "West Palm Beach, FL",
         "Complete", "Complete", "Pricing Pending"),
        ("Orlando Concrete Pumping", "Concrete", "Faye Bennett",
         "faye@ocp-demo.example", "407-555-0189", "Orlando, FL",
         "Complete", "Complete", "Quote Received"),
    ]
    for (company, trade, contact, email, phone, loc, ins, w9, qs) in subs:
        db.add_subcontractor({
            "company": company, "trade": trade, "contact": contact,
            "email": email, "phone": phone, "location": loc,
            "insurance_status": ins, "w9_status": w9, "quote_status": qs,
            "last_contact": _d(-1), "projects_worked": 2,
            "notes": "Fictional demo subcontractor.",
        })


def _seed_vendors() -> None:
    vendors = [
        ("HydroFlow Process Equipment", "Process Equipment", "Karen Blaine",
         "karen@hydroflow-demo.example", "813-555-0200", "Tampa, FL"),
        ("AquaTech Pump Solutions", "Pumps", "Manny Rivera",
         "manny@aquatech-demo.example", "407-555-0210", "Orlando, FL"),
        ("Southern Pipe & Supply", "Pipe & Fittings", "Beth Owens",
         "beth@southernpipe-demo.example", "941-555-0220", "Sarasota, FL"),
        ("Gulf Coast Valve Co.", "Valves", "Dale Kim",
         "dale@gcvalve-demo.example", "727-555-0230", "Clearwater, FL"),
        ("Precision Concrete Products", "Precast Concrete", "Nora Hayes",
         "nora@pcp-demo.example", "941-555-0240", "Bradenton, FL"),
        ("Everglades Electrical Supply", "Electrical", "Victor Rios",
         "victor@ees-demo.example", "305-555-0250", "Miami, FL"),
        ("Bay Area Rebar & Mesh", "Reinforcing Steel", "Jenny Lin",
         "jenny@barb-demo.example", "813-555-0260", "Tampa, FL"),
        ("Sunstate Aggregates", "Aggregates", "Curtis Bell",
         "curtis@sunstate-demo.example", "239-555-0270", "Fort Myers, FL"),
        ("East Coast Instrumentation", "Instrumentation", "Pam Ortiz",
         "pam@eci-demo.example", "561-555-0280", "West Palm Beach, FL"),
        ("Gulfstream Fabrication", "Structural Steel", "Rob Davis",
         "rob@gulfstream-demo.example", "727-555-0290", "St. Petersburg, FL"),
        ("Central FL Coatings", "Coatings & Linings", "Yolanda Cruz",
         "yolanda@cfc-demo.example", "407-555-0300", "Orlando, FL"),
        ("Peninsular Equipment Rental", "Equipment Rental", "Mark Sloan",
         "mark@per-demo.example", "813-555-0310", "Tampa, FL"),
        ("Atlantic Flow Controls", "Process Controls", "Grace Palmer",
         "grace@afc-demo.example", "561-555-0320", "West Palm Beach, FL"),
        ("Manatee Ready Mix", "Ready Mix Concrete", "Todd Franklin",
         "todd@mrm-demo.example", "941-555-0330", "Bradenton, FL"),
        ("South Florida Dewatering", "Dewatering", "Luis Mendez",
         "luis@sfd-demo.example", "954-555-0340", "West Palm Beach, FL"),
    ]
    for (company, scope, contact, email, phone, loc) in vendors:
        db.add_vendor({
            "company": company, "scope": scope, "contact": contact,
            "email": email, "phone": phone, "location": loc,
            "notes": "Fictional demo vendor.",
        })


def _seed_quotes() -> None:
    # Clearwater flagship quotes — three process equipment vendors
    db.create_quote(1, {
        "vendor": "HydroFlow Process Equipment", "scope": "Process Equipment",
        "amount": 1_240_000, "lead_time_weeks": 16, "validity_days": 30,
        "compliance": "Complete", "status": "Received",
        "exceptions": "None",
    })
    db.create_quote(1, {
        "vendor": "AquaTech Pump Solutions", "scope": "Process Equipment",
        "amount": 1_310_000, "lead_time_weeks": 12, "validity_days": 45,
        "compliance": "Complete", "status": "Received",
        "exceptions": "Freight excluded",
    })
    db.create_quote(1, {
        "vendor": "Atlantic Flow Controls", "scope": "Process Equipment",
        "amount": 1_180_000, "lead_time_weeks": 20, "validity_days": 30,
        "compliance": "Missing docs", "status": "Review",
        "exceptions": "Lead time is currently an estimate",
    })
    # Electrical quote pending — represented by a "Pending" quote row
    db.create_quote(1, {
        "vendor": "Gulf Coast Electrical Contractors", "scope": "Electrical",
        "amount": 0, "lead_time_weeks": 0, "validity_days": 0,
        "compliance": "Pending", "status": "Pending",
        "exceptions": "Awaiting final pricing",
    })
    # Mechanical received
    db.create_quote(1, {
        "vendor": "Sunshine Mechanical Services", "scope": "Process Piping",
        "amount": 2_050_000, "lead_time_weeks": 10, "validity_days": 30,
        "compliance": "Complete", "status": "Received",
        "exceptions": "None",
    })

    # Distribute 25 more quotes across other opportunities
    scopes = ["Electrical", "Mechanical", "Process Equipment", "Concrete",
              "Survey", "HVAC", "Traffic Control", "Landscaping"]
    vendors = [v["company"] for v in db.get_vendors()]
    for i in range(25):
        opp_id = (i % 24) + 2
        db.create_quote(opp_id, {
            "vendor": vendors[i % len(vendors)],
            "scope": scopes[i % len(scopes)],
            "amount": 150_000 + i * 47_500,
            "lead_time_weeks": 6 + (i % 18),
            "validity_days": 30 + (i % 3) * 15,
            "compliance": "Complete" if i % 4 else "Missing docs",
            "status": "Received" if i % 5 else "Review",
            "exceptions": "None" if i % 3 else "Freight excluded",
        })


def _seed_addenda() -> None:
    db.add_addendum(1, 1, _d(-18), "Reviewed",
                    "Clarified pipe material specification.")
    db.add_addendum(1, 2, _d(-11), "Needs Review",
                    "Revised equipment schedule and electrical scope.")
    db.add_addendum(1, 3, _d(-5), "Not Reviewed",
                    "Updated concrete notes and site plan.")

    for i in range(2, 9):
        db.add_addendum(i, 1, _d(-3 - i), "Reviewed", "Minor clarifications.")


def _seed_activities() -> None:
    activities = [
        (1, "AI analyzed Clearwater WRF opportunity", "ai"),
        (1, "Estimator assigned: Michael Carter", "assignment"),
        (1, "Bid package created for Electrical", "bid_package"),
        (1, "8 subcontractors invited", "invitation"),
        (1, "Mechanical quote received", "quote"),
        (1, "Addendum #1 reviewed", "addenda"),
        (1, "Addendum #2 uploaded", "addenda"),
        (1, "Addendum #3 uploaded", "addenda"),
        (2, "Scope breakdown completed", "scope"),
        (3, "Pre-bid meeting attended", "meeting"),
        (4, "Vendor quote received", "quote"),
        (5, "Estimate updated", "estimate"),
        (6, "Bid submitted", "submission"),
        (7, "Award notification received", "award"),
        (8, "Lost bid analysis completed", "loss"),
        (9, "Subcontractor follow-up sent", "followup"),
        (10, "Site visit scheduled", "meeting"),
        (11, "Addendum #1 reviewed", "addenda"),
        (12, "New opportunity added", "intake"),
        (13, "Estimate review meeting held", "meeting"),
    ]
    for (opp_id, msg, cat) in activities:
        db.create_activity(opp_id, msg, cat)


def _seed_notifications() -> None:
    notifications = [
        ("red", "Clearwater WRF — Bid due in 10 days", 1),
        ("orange", "Electrical quote pending for Clearwater WRF", 1),
        ("orange", "Addendum #2 needs review", 1),
        ("green", "Mechanical quote received", 1),
        ("blue", "Pre-bid meeting tomorrow", 2),
        ("red", "Bid due in 2 days", 3),
        ("orange", "Equipment pricing has not been confirmed", 1),
        ("green", "Structural concrete scope marked Ready", 1),
        ("blue", "Site visit scheduled for Sarasota Lift Station", 3),
        ("red", "Quote deadline approaching", 5),
        ("orange", "Insurance certificate expiring", 8),
        ("green", "Estimate approved for Tampa Transmission Main", 4),
        ("blue", "Project kickoff scheduled", 7),
        ("orange", "Missing specification sections", 12),
        ("red", "Final bid review in 1 day", 6),
    ]
    for (lvl, msg, opp_id) in notifications:
        db.create_notification(lvl, msg, opp_id)


def _seed_followups() -> None:
    followups = [
        (1, "City of Clearwater Water Reclamation Facility Improvements",
         "Submitted", _d(7), "Contact owner regarding bid status.",
         "Following up on our bid submission for the Clearwater WRF "
         "Improvements project. Please let us know if you have any "
         "questions or need additional information."),
        (2, "Palmetto Water Treatment Plant Expansion",
         "Submitted", _d(5), "Confirm receipt of bid package.",
         "Confirming receipt of our bid for the Palmetto WTP Expansion."),
        (3, "Sarasota Lift Station No. 14 Rehabilitation",
         "Clarification Request", _d(3), "Respond to clarification request.",
         "We received a clarification request and will respond by the "
         "requested date."),
        (4, "Tampa Bay Transmission Main Segment 3",
         "Awarded", _d(-2), "Schedule project kickoff.",
         "Award notification received. Schedule kickoff with the owner."),
        (5, "Bradenton Gravity Sewer Replacement",
         "Lost", _d(1), "Request debrief from owner.",
         "Request a debrief to understand the winning bid."),
        (6, "Pinellas County Pumping Station Upgrade",
         "Submitted", _d(9), "Follow up on bid status.",
         "Follow up with Pinellas County on bid status."),
        (7, "Orlando WRF Process Piping Modifications",
         "Submitted", _d(11), "Owner follow-up.",
         "Follow up with the City of Orlando."),
        (8, "Lee County Utility Extension Phase 2",
         "Submitted", _d(4), "Subcontractor follow-up.",
         "Confirm subcontractor pricing validity."),
        (9, "West Palm Beach Water Main Replacement",
         "Submitted", _d(6), "Owner follow-up.",
         "Follow up on bid status."),
        (10, "Miami-Dade Wastewater Rehab Program",
         "Submitted", _d(13), "Owner follow-up.",
         "Follow up on bid status."),
    ]
    for (opp_id, proj, status, nf, action, msg) in followups:
        db.create_followup({
            "opportunity_id": opp_id, "project": proj, "status": status,
            "next_followup": nf, "action": action, "message": msg,
        })


def _seed_projects() -> None:
    projects = [
        (4, "Tampa Bay Transmission Main Segment 3", "City of Tampa",
         "Tampa, FL", 22_800_000, "Robert Nguyen", "Active"),
        (7, "Lee County Utility Extension Phase 2", "Lee County Utilities",
         "Fort Myers, FL", 14_200_000, "Karen Delgado", "Active"),
        (10, "Clearwater Beach Lift Station Improvements",
         "City of Clearwater", "Clearwater, FL", 4_300_000,
         "Thomas Brennan", "Active"),
        (11, "Manatee County WRF Aeration Upgrade", "Manatee County",
         "Bradenton, FL", 11_900_000, "Lisa Park", "Active"),
        (12, "Sarasota Transmission Main Crossing", "Sarasota County",
         "Sarasota, FL", 8_700_000, "Robert Nguyen", "Active"),
        (13, "Tampa Heights Utility Relocation", "City of Tampa",
         "Tampa, FL", 2_950_000, "Karen Delgado", "Active"),
        (14, "St. Petersburg Water Treatment Filter Rehab",
         "City of St. Petersburg", "St. Petersburg, FL", 6_100_000,
         "Thomas Brennan", "Active"),
        (15, "Palmetto Force Main Replacement", "City of Palmetto",
         "Palmetto, FL", 3_850_000, "Lisa Park", "Active"),
        (16, "Orlando Southeast Pumping Station", "City of Orlando",
         "Orlando, FL", 5_200_000, "Robert Nguyen", "Active"),
        (17, "Fort Myers Beach Utility Restoration", "Lee County Utilities",
         "Fort Myers, FL", 7_800_000, "Karen Delgado", "Active"),
    ]
    for (opp_id, proj, owner, loc, val, pm, status) in projects:
        db.create_project({
            "opportunity_id": opp_id, "project": proj, "owner": owner,
            "location": loc, "contract_value": val, "project_manager": pm,
            "estimate_linked": 1, "subs_linked": 1, "vendors_linked": 1,
            "docs_linked": 1, "status": status, "start_date": _d(-30),
        })