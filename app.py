"""
TLC BidFlow AI
==============

From Plan Room Opportunity to Bid Submission

AI-powered bid intake, scope extraction, estimating, subcontractor
coordination, and bid follow-up for water & wastewater construction.

Concept Demo — Built around TLC Diversified's public workflow.
All data is fictional.
"""
from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import database as db
from data.demo_data import seed_demo_data, CLEARWATER_TEXT
from utils import ai, calculations, formatting as fmt
from utils import notifications as notif

# ---------------------------------------------------------------------------
# Page setup + theme
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="TLC BidFlow AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --navy: #0f172a;
        --blue: #1d4ed8;
        --blue-soft: #eff6ff;
        --gray-bg: #f8fafc;
        --gray-border: #e2e8f0;
        --gray-text: #475569;
        --green: #16a34a;
        --orange: #d97706;
        --red: #dc2626;
    }
    .main { background: #ffffff; }
    .block-container { padding-top: 1.2rem; padding-bottom: 3rem; }

    h1, h2, h3, h4 { color: var(--navy); font-family: 'Inter', sans-serif; }

    .top-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 14px 20px; border: 1px solid var(--gray-border);
        border-radius: 14px; background: #fff;
        box-shadow: 0 1px 2px rgba(15,23,42,0.04);
        margin-bottom: 16px;
    }
    .brand-title { font-size: 22px; font-weight: 700; color: var(--navy);
                   margin: 0; }
    .brand-sub { font-size: 13px; color: var(--gray-text); margin: 0; }
    .header-right { display: flex; gap: 8px; align-items: center; }
    .pill {
        display: inline-block; padding: 4px 10px; border-radius: 999px;
        font-size: 11px; font-weight: 600; letter-spacing: .04em;
        text-transform: uppercase;
    }
    .pill-demo { background: #fff7ed; color: #c2410c;
                 border: 1px solid #fed7aa; }
    .pill-concept { background: #eff6ff; color: #1d4ed8;
                    border: 1px solid #bfdbfe; }

    .kpi-card {
        background: #fff; border: 1px solid var(--gray-border);
        border-radius: 14px; padding: 16px 18px;
        box-shadow: 0 1px 2px rgba(15,23,42,0.04);
        height: 100%;
    }
    .kpi-label { font-size: 12px; color: var(--gray-text);
                 text-transform: uppercase; letter-spacing: .06em;
                 font-weight: 600; }
    .kpi-value { font-size: 26px; font-weight: 700; color: var(--navy);
                 margin-top: 4px; }
    .kpi-sub { font-size: 12px; color: var(--gray-text); margin-top: 4px; }

    .section-card {
        background: var(--gray-bg); border: 1px solid var(--gray-border);
        border-radius: 14px; padding: 18px 20px; margin-bottom: 14px;
    }
    .white-card {
        background: #fff; border: 1px solid var(--gray-border);
        border-radius: 14px; padding: 16px 18px; margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(15,23,42,0.04);
    }

    .badge {
        display: inline-block; padding: 3px 10px; border-radius: 999px;
        font-size: 11px; font-weight: 600; letter-spacing: .02em;
        white-space: nowrap;
    }
    .badge-gray { background: #f1f5f9; color: #475569;
                  border: 1px solid #e2e8f0; }
    .badge-blue { background: #eff6ff; color: #1d4ed8;
                  border: 1px solid #bfdbfe; }
    .badge-green { background: #f0fdf4; color: #15803d;
                   border: 1px solid #bbf7d0; }
    .badge-orange { background: #fff7ed; color: #c2410c;
                    border: 1px solid #fed7aa; }
    .badge-red { background: #fef2f2; color: #b91c1c;
                 border: 1px solid #fecaca; }

    .pipeline-col {
        background: var(--gray-bg); border: 1px solid var(--gray-border);
        border-radius: 12px; padding: 10px; min-height: 140px;
    }
    .pipeline-col h4 { font-size: 12px; text-transform: uppercase;
                       letter-spacing: .05em; color: var(--gray-text);
                       margin-bottom: 8px; }
    .pipeline-card {
        background: #fff; border: 1px solid var(--gray-border);
        border-radius: 10px; padding: 8px 10px; margin-bottom: 8px;
        font-size: 12px;
    }
    .pipeline-card b { color: var(--navy); }

    .timeline-item {
        border-left: 2px solid var(--gray-border); padding: 0 0 14px 14px;
        position: relative;
    }
    .timeline-item:before {
        content: ""; position: absolute; left: -6px; top: 4px;
        width: 10px; height: 10px; border-radius: 50%;
        background: var(--blue); border: 2px solid #fff;
    }
    .timeline-time { font-size: 11px; color: var(--gray-text); }
    .timeline-msg { font-size: 13px; color: var(--navy); }

    .attention-item {
        display: flex; gap: 10px; align-items: center;
        padding: 8px 12px; border: 1px solid var(--gray-border);
        border-radius: 10px; background: #fff; margin-bottom: 8px;
        font-size: 13px;
    }

    .stButton>button {
        border-radius: 10px; border: 1px solid var(--gray-border);
        background: #fff; color: var(--navy); font-weight: 600;
        padding: 6px 14px;
    }
    .stButton>button:hover { border-color: var(--blue); color: var(--blue); }
    .stButton>button[kind="primary"] {
        background: var(--blue); color: #fff; border-color: var(--blue);
    }

    section[data-testid="stSidebar"] {
        background: #ffffff; border-right: 1px solid var(--gray-border);
    }
    section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Bootstrap database
# ---------------------------------------------------------------------------

db.init_db()
seed_demo_data()

# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def ss(key: str, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


ss("page", "Overview")
ss("selected_opp", 1)
ss("intake_text", CLEARWATER_TEXT)
ss("intake_result", None)
ss("guide_step", 0)
ss("demo_mode", True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def header():
    st.markdown(
        """
        <div class="top-header">
          <div>
            <p class="brand-title">TLC BidFlow AI</p>
            <p class="brand-sub">Construction Estimating &amp; Bid Operations</p>
          </div>
          <div class="header-right">
            <span class="pill pill-concept">Concept Demo</span>
            <span class="pill pill-demo">DEMO MODE</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def concept_label():
    st.caption(
        "Concept Demo — Built around TLC Diversified's public workflow. "
        "All projects, vendors, and figures are fictional."
    )


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

PAGES = [
    ("Overview", "📊"),
    ("Bid Opportunities", "📋"),
    ("AI Bid Intake", "✨"),
    ("Bid Calendar", "📅"),
    ("Scope Breakdown", "🧱"),
    ("Estimates", "🧮"),
    ("Subcontractors", "🤝"),
    ("Vendor Quotes", "💬"),
    ("Bid Review", "🔍"),
    ("Submissions", "📤"),
    ("Projects", "🏗️"),
    ("Follow-Ups", "🔔"),
    ("Analytics", "📈"),
    ("AI Assistant", "🧠"),
    ("Settings", "⚙️"),
]


def sidebar():
    with st.sidebar:
        st.markdown(
            '<div style="padding: 4px 6px 12px 6px;">'
            '<div style="font-weight:800; color:#0f172a; font-size:16px;">'
            'TLC BidFlow AI</div>'
            '<div style="color:#64748b; font-size:11px;">'
            'Bid Operations Platform</div></div>',
            unsafe_allow_html=True,
        )
        for name, icon in PAGES:
            if st.button(f"{icon}  {name}", key=f"nav_{name}",
                         use_container_width=True):
                st.session_state.page = name
                st.rerun()

        st.divider()
        if st.button("▶ Launch Guided Demo", type="primary",
                     use_container_width=True):
            st.session_state.page = "AI Bid Intake"
            st.session_state.guide_step = 1
            st.rerun()

        st.markdown(
            '<div style="color:#94a3b8; font-size:11px; margin-top:12px;">'
            'Demo Mode · No external API required</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Reusable UI pieces
# ---------------------------------------------------------------------------

def kpi(label: str, value: str, sub: str = ""):
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def white_card_open():
    st.markdown('<div class="white-card">', unsafe_allow_html=True)


def white_card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def section(title: str, subtitle: str = ""):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def badge_row(levels: list[str]):
    html = " ".join(fmt.badge(l) for l in levels if l)
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page: Overview
# ---------------------------------------------------------------------------

def page_overview():
    opps = db.get_opportunities()
    quotes = db.get_quotes()
    followups = db.get_followups()

    pipeline_value = sum(o.get("estimated_value", 0) or 0 for o in opps)
    due_soon = sum(
        1 for o in opps
        if o.get("bid_due") and o["bid_due"][:10] >=
        datetime.now().strftime("%Y-%m-%d")
    )
    estimating = sum(1 for o in opps if o.get("status") == "Estimating")
    quotes_pending = sum(1 for q in quotes if q.get("status") == "Pending")
    submitted = sum(1 for o in opps if o.get("status") == "Submitted")
    awarded = sum(1 for o in opps if o.get("status") == "Awarded")

    st.markdown(
        '<h2 style="margin-bottom:4px;">Executive Overview</h2>'
        '<p style="color:#64748b; margin-top:0;">'
        'Real-time snapshot of the bid pipeline. '
        '<span style="color:#94a3b8;">(Fictional demo data)</span></p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Active Opportunities", f"{len(opps)}",
            "Across all pipeline stages")
    with c2:
        kpi("Bids Due This Month", f"{due_soon}", "Watch deadlines closely")
    with c3:
        kpi("Estimating", f"{estimating}", "Active estimating workspace")
    with c4:
        kpi("Quotes Pending", f"{quotes_pending}", "Sub / vendor quotes")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        kpi("Pipeline Value", fmt.money(pipeline_value, compact=True),
            "Total estimated construction value")
    with c6:
        kpi("Submitted", f"{submitted}", "Awaiting owner decision")
    with c7:
        kpi("Awarded", f"{awarded}", "Converted to projects")
    with c8:
        kpi("Follow-Ups Due", f"{len(followups)}", "Owner & sub follow-ups")

    st.markdown("---")

    left, right = st.columns([3, 2])
    with left:
        section("Today's Attention",
                "Fictional notifications from the demo pipeline.")
        notifs = db.get_notifications()[:5]
        for n in notifs:
            emoji = notif.emoji_for(n["level"])
            st.markdown(
                f'<div class="attention-item">{emoji} '
                f'<span>{n["message"]}</span></div>',
                unsafe_allow_html=True,
            )
    with right:
        section("Quick Actions", "Jump into the workflow.")
        if st.button("✨ Analyze New Opportunity", use_container_width=True):
            st.session_state.page = "AI Bid Intake"
            st.rerun()
        if st.button("📅 View Bids Due", use_container_width=True):
            st.session_state.page = "Bid Calendar"
            st.rerun()
        if st.button("💬 Review Pending Quotes", use_container_width=True):
            st.session_state.page = "Vendor Quotes"
            st.rerun()
        if st.button("🧮 Open Estimate", use_container_width=True):
            st.session_state.page = "Estimates"
            st.rerun()
        if st.button("🔍 Review Risks", use_container_width=True):
            st.session_state.page = "Bid Review"
            st.rerun()

    st.markdown("---")
    section("Bid Pipeline",
            "Opportunities across the full bid lifecycle.")
    render_pipeline(opps, compact=True)

    st.markdown("---")
    section("Recent Activity", "Latest actions across the demo workspace.")
    acts = db.get_activities(limit=6)
    render_timeline(acts)


def render_pipeline(opps: list[dict], compact: bool = False):
    stages = [
        "New Opportunity", "Under Review", "Qualified", "Estimating",
        "Quotes Pending", "Bid Review", "Submitted", "Awarded", "Lost",
    ]
    cols = st.columns(len(stages))
    for col, stage in zip(cols, stages):
        with col:
            st.markdown(
                f'<div class="pipeline-col"><h4>{stage}</h4>',
                unsafe_allow_html=True,
            )
            items = [o for o in opps if o.get("status") == stage]
            if not items:
                st.markdown(
                    '<div style="color:#94a3b8; font-size:11px;">'
                    'No opportunities</div>',
                    unsafe_allow_html=True,
                )
            for o in items[: (3 if compact else 6)]:
                st.markdown(
                    f'<div class="pipeline-card">'
                    f'<b>{o["project"][:38]}</b><br>'
                    f'<span style="color:#64748b;">{o.get("location", "")}'
                    f'</span><br>'
                    f'<span style="color:#1d4ed8;">'
                    f'{fmt.money(o.get("estimated_value", 0), compact=True)}'
                    f'</span> · '
                    f'<span style="color:#64748b;">'
                    f'{fmt.short_date(o.get("bid_due", ""))}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)


def render_timeline(activities: list[dict]):
    if not activities:
        st.info("No activity yet in the demo dataset.")
        return
    st.markdown('<div class="white-card">', unsafe_allow_html=True)
    for a in activities:
        st.markdown(
            f'<div class="timeline-item">'
            f'<div class="timeline-time">'
            f'{notif.time_ago(a.get("timestamp", ""))}</div>'
            f'<div class="timeline-msg">{a.get("message", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page: Bid Opportunities
# ---------------------------------------------------------------------------

def page_opportunities():
    st.markdown("## Bid Opportunities")
    st.caption("Fictional demo data. Search and filter the pipeline.")

    opps = db.get_opportunities()
    df = pd.DataFrame(opps)
    if df.empty:
        st.info("No opportunities in the demo dataset.")
        return

    with st.expander("Filters", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        status_filter = c1.multiselect(
            "Status", sorted(df["status"].dropna().unique().tolist())
        )
        type_filter = c2.multiselect(
            "Project Type", sorted(df["project_type"].dropna().unique().tolist())
        )
        loc_filter = c3.multiselect(
            "Location", sorted(df["location"].dropna().unique().tolist())
        )
        est_filter = c4.multiselect(
            "Estimator", sorted(df["estimator"].dropna().unique().tolist())
        )
        c5, c6, c7 = st.columns(3)
        risk_filter = c5.multiselect(
            "Risk", sorted(df["risk"].dropna().unique().tolist())
        )
        min_val, max_val = c6.slider(
            "Estimated Value ($M)",
            0.0,
            float(df["estimated_value"].max() / 1_000_000 + 1),
            (0.0, float(df["estimated_value"].max() / 1_000_000 + 1)),
        )
        due_after = c7.date_input("Bid Due After", value=None)

    filtered = df.copy()
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if type_filter:
        filtered = filtered[filtered["project_type"].isin(type_filter)]
    if loc_filter:
        filtered = filtered[filtered["location"].isin(loc_filter)]
    if est_filter:
        filtered = filtered[filtered["estimator"].isin(est_filter)]
    if risk_filter:
        filtered = filtered[filtered["risk"].isin(risk_filter)]
    filtered = filtered[
        (filtered["estimated_value"] >= min_val * 1_000_000)
        & (filtered["estimated_value"] <= max_val * 1_000_000)
    ]
    if due_after:
        filtered = filtered[
            filtered["bid_due"].fillna("") >= due_after.strftime("%Y-%m-%d")
        ]

    search = st.text_input("Search projects, owners, locations",
                           placeholder="e.g. Clearwater")
    if search:
        mask = (
            filtered["project"].str.contains(search, case=False, na=False)
            | filtered["owner"].str.contains(search, case=False, na=False)
            | filtered["location"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    st.markdown(
        f"**{len(filtered)}** opportunities match your filters."
    )

    show = filtered[[
        "id", "project", "owner", "location", "project_type",
        "estimated_value", "bid_due", "estimator", "status",
        "readiness", "risk",
    ]].rename(columns={
        "project": "Project", "owner": "Owner", "location": "Location",
        "project_type": "Type", "estimated_value": "Value",
        "bid_due": "Bid Due", "estimator": "Estimator",
        "status": "Status", "readiness": "Readiness", "risk": "Risk",
    })
    show["Value"] = show["Value"].apply(lambda v: fmt.money(v, compact=True))
    show["Bid Due"] = show["Bid Due"].apply(fmt.short_date)
    show["Readiness"] = show["Readiness"].apply(lambda v: f"{v}%")

    st.dataframe(
        show.drop(columns=["id"]),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Open an opportunity")
    options = {
        f"#{o['id']} — {o['project']}": o["id"] for o in filtered.to_dict("records")
    }
    if options:
        choice = st.selectbox("Select opportunity", list(options.keys()))
        if st.button("Open Opportunity", type="primary"):
            st.session_state.selected_opp = options[choice]
            st.session_state.page = "Opportunity Detail"
            st.rerun()

    if st.button("+ New Opportunity"):
        st.session_state.page = "AI Bid Intake"
        st.rerun()


# ---------------------------------------------------------------------------
# Page: Opportunity Detail
# ---------------------------------------------------------------------------

def page_opportunity_detail():
    opp_id = st.session_state.selected_opp
    opp = db.get_opportunity(opp_id)
    if not opp:
        st.warning("Opportunity not found. Returning to Bid Opportunities.")
        st.session_state.page = "Bid Opportunities"
        st.rerun()
        return

    if st.button("← Back to Bid Opportunities"):
        st.session_state.page = "Bid Opportunities"
        st.rerun()

    st.markdown(f"## {opp['project']}")
    badge_row([opp.get("status"), opp.get("risk"),
               f"Readiness {opp.get('readiness', 0)}%"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Estimated Value",
              fmt.money(opp.get("estimated_value", 0)))
    c2.metric("Bid Due", fmt.short_date(opp.get("bid_due", "")))
    c3.metric("Pre-Bid", fmt.short_date(opp.get("prebid", "")))
    c4.metric("Project Type", opp.get("project_type", "—"))

    st.markdown("---")
    left, right = st.columns([2, 1])
    with left:
        section("Project Overview")
        st.markdown(
            f"""
            <div class="white-card">
            <table style="width:100%; font-size:13px; color:#0f172a;">
            <tr><td style="color:#64748b;">Owner</td>
                <td>{opp.get('owner','—')}</td></tr>
            <tr><td style="color:#64748b;">Location</td>
                <td>{opp.get('location','—')}</td></tr>
            <tr><td style="color:#64748b;">Estimator</td>
                <td>{opp.get('estimator','—')}</td></tr>
            <tr><td style="color:#64748b;">Project Manager</td>
                <td>{opp.get('project_manager','—')}</td></tr>
            <tr><td style="color:#64748b;">Status</td>
                <td>{opp.get('status','—')}</td></tr>
            <tr><td style="color:#64748b;">Risk</td>
                <td>{opp.get('risk','—')}</td></tr>
            <tr><td style="color:#64748b;">Readiness</td>
                <td>{opp.get('readiness', 0)}%</td></tr>
            </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        section("Scope Summary")
        scope = json.loads(opp.get("scope_json") or "[]")
        divisions = json.loads(opp.get("divisions_json") or "[]")
        if scope:
            for s in scope:
                st.markdown(f"- {s}")
        else:
            st.caption("No scope extracted yet.")
        if divisions:
            st.markdown("**Recommended Divisions:**")
            badge_row(divisions)

    with right:
        section("Missing Information")
        missing = json.loads(opp.get("missing_json") or "[]")
        for m in missing:
            st.markdown(f"- {m}")

        section("Next Actions")
        actions = json.loads(opp.get("next_actions_json") or "[]")
        for i, a in enumerate(actions, 1):
            st.markdown(f"{i}. {a}")

    st.markdown("---")
    section("Activity Timeline")
    render_timeline(db.get_activities(opp_id, limit=10))

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🧱 Scope Breakdown", use_container_width=True):
        st.session_state.page = "Scope Breakdown"
        st.rerun()
    if c2.button("🧮 Estimate", use_container_width=True):
        st.session_state.page = "Estimates"
        st.rerun()
    if c3.button("💬 Quotes", use_container_width=True):
        st.session_state.page = "Vendor Quotes"
        st.rerun()
    if c4.button("🔍 Bid Review", use_container_width=True):
        st.session_state.page = "Bid Review"
        st.rerun()


# ---------------------------------------------------------------------------
# Page: AI Bid Intake
# ---------------------------------------------------------------------------

def page_ai_intake():
    st.markdown("## ✨ AI Bid Intake")
    st.caption(
        "Paste a plan-room opportunity or bid notice. BidFlow AI extracts "
        "structured project intelligence — scope, value, dates, divisions, "
        "and readiness. Demo mode uses a deterministic extractor; no paid "
        "API required."
    )

    if st.session_state.guide_step == 1:
        st.info("**Guided Demo · Step 1** — Paste the bid description and "
                "click **Analyze Opportunity**.")

    text = st.text_area(
        "Bid notice / opportunity description",
        value=st.session_state.intake_text,
        height=280,
        key="intake_text_area",
    )
    st.session_state.intake_text = text

    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        analyze = st.button("Analyze Opportunity", type="primary",
                            use_container_width=True)
    with c2:
        if st.button("Load Clearwater Example", use_container_width=True):
            st.session_state.intake_text = CLEARWATER_TEXT
            st.session_state.intake_result = None
            st.rerun()

    if analyze:
        if not text.strip():
            st.error("Please paste a bid notice before analyzing.")
        else:
            with st.spinner("Analyzing opportunity..."):
                result = ai.analyze_bid_notice(text)
            st.session_state.intake_result = result
            notif.activity("AI analyzed opportunity", None, "ai")

    result = st.session_state.intake_result
    if not result:
        st.markdown("---")
        st.caption("Paste a bid notice and click Analyze to see structured "
                   "results here.")
        return

    st.markdown("---")
    st.markdown("### Extracted Project Intelligence")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi("Project", result["project"][:28])
    with c2:
        kpi("Location", result["location"])
    with c3:
        kpi("Project Type", result["project_type"])

    c4, c5, c6 = st.columns(3)
    with c4:
        kpi("Estimated Value", fmt.money(result["estimated_value"],
                                         compact=True))
    with c5:
        kpi("Bid Due", fmt.short_date(result["bid_due"]))
    with c6:
        kpi("Pre-Bid", fmt.short_date(result["prebid"]))

    st.markdown("---")
    left, right = st.columns([2, 2])
    with left:
        section("Bid Scope")
        for s in result["scope"]:
            st.markdown(f"- {s}")
        st.markdown("**Recommended Divisions**")
        badge_row(result["divisions"])

    with right:
        section("Bid Complexity")
        st.markdown(fmt.badge(result["complexity"]),
                    unsafe_allow_html=True)
        section("Bid Readiness")
        st.progress(int(result["readiness"]) / 100)
        st.caption(f"{result['readiness']}% ready for estimating.")

        section("Missing Information")
        for m in result["missing"]:
            st.markdown(f"- {m}")

    section("Recommended Next Actions")
    for i, a in enumerate(result["next_actions"], 1):
        st.markdown(f"{i}. {a}")

    st.markdown("---")
    st.markdown("### Create the Opportunity")
    c1, c2, c3 = st.columns(3)
    estimator = c1.selectbox(
        "Assign Estimator",
        ["Michael Carter", "Priya Raman", "Daniel Okafor",
         "Sofia Alvarez", "Jason Whitfield"],
    )
    status = c2.selectbox(
        "Initial Status",
        ["New Opportunity", "Under Review", "Qualified", "Estimating"],
    )
    risk = c3.selectbox("Risk", ["Low", "Medium", "High"],
                        index=["Low", "Medium", "High"].index(result["complexity"])
                        if result["complexity"] in ["Low", "Medium", "High"]
                        else 1)

    if st.button("Create Opportunity", type="primary"):
        opp_id = db.create_opportunity({
            **result,
            "estimator": estimator,
            "status": status,
            "risk": risk,
        })
        # Seed scope items
        for s in result["scope"]:
            db.add_scope_item(opp_id, {
                "scope": s,
                "quantity": result["quantities"].get("underground_lf", 1)
                if "Underground Piping" in s else 1,
                "unit": "LF" if "Underground Piping" in s else "LS",
                "self_perform": "Yes" if "Concrete" in s or "Earthwork" in s
                else "Partial" if "Process" in s else "No",
                "subcontract": "Yes" if "Electrical" in s or
                "Equipment" in s else "No",
                "quote_required": "Yes" if "Electrical" in s or
                "Equipment" in s or "Process" in s else "No",
                "status": "Pending",
            })
        notif.activity(f"Opportunity created: {result['project']}",
                       opp_id, "intake")
        notif.notify("green", f"Opportunity created: {result['project']}",
                     opp_id)
        st.session_state.selected_opp = opp_id
        st.session_state.guide_step = 2
        st.success(f"Opportunity created — ID #{opp_id}. "
                   "Opening opportunity detail.")
        st.session_state.page = "Scope Breakdown"
        st.rerun()


# ---------------------------------------------------------------------------
# Page: Bid Calendar
# ---------------------------------------------------------------------------

def page_calendar():
    st.markdown("## 📅 Bid Calendar")
    st.caption("Upcoming bid deadlines, pre-bid meetings, and reviews. "
               "Fictional demo data.")

    opps = db.get_opportunities()
    today = datetime.now().date()

    rows = []
    for o in opps:
        if o.get("bid_due"):
            rows.append({
                "Project": o["project"],
                "Event": "Bid Due",
                "Date": o["bid_due"][:10],
                "Urgency": fmt.relative_day(o["bid_due"]),
                "Owner": o.get("owner", ""),
                "Value": fmt.money(o.get("estimated_value", 0),
                                   compact=True),
            })
        if o.get("prebid"):
            rows.append({
                "Project": o["project"],
                "Event": "Pre-Bid Meeting",
                "Date": o["prebid"][:10],
                "Urgency": fmt.relative_day(o["prebid"]),
                "Owner": o.get("owner", ""),
                "Value": fmt.money(o.get("estimated_value", 0),
                                   compact=True),
            })

    # Quote deadlines from followups
    for f in db.get_followups():
        if f.get("next_followup"):
            rows.append({
                "Project": f.get("project", ""),
                "Event": "Follow-Up",
                "Date": f["next_followup"],
                "Urgency": fmt.relative_day(f["next_followup"]),
                "Owner": "",
                "Value": "",
            })

    if not rows:
        st.info("No calendar events in the demo dataset.")
        return

    df = pd.DataFrame(rows).sort_values("Date")
    df = df[df["Date"] >= today.strftime("%Y-%m-%d")]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### Urgency Summary")
    for label in ["Due Today", "Due Tomorrow", "Due This Week", "Upcoming"]:
        count = (df["Urgency"] == label).sum()
        st.markdown(f"- **{label}**: {count} event(s)")


# ---------------------------------------------------------------------------
# Page: Scope Breakdown
# ---------------------------------------------------------------------------

def page_scope():
    st.markdown("## 🧱 Scope Breakdown")
    st.caption("Self-perform vs. subcontract matrix. Edit rows and save.")

    opp_id = st.session_state.selected_opp
    opp = db.get_opportunity(opp_id)
    if not opp:
        st.warning("No opportunity selected.")
        return

    st.markdown(f"**Project:** {opp['project']}")

    items = db.get_scope_items(opp_id)
    if not items:
        st.info("No scope items yet. Create an opportunity from AI Bid "
                "Intake first.")
        return

    df = pd.DataFrame(items)
    edited = st.data_editor(
        df[["id", "scope", "quantity", "unit", "self_perform",
            "subcontract", "quote_required", "status"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "self_perform": st.column_config.SelectboxColumn(
                "Self Perform", options=["Yes", "No", "Partial"]),
            "subcontract": st.column_config.SelectboxColumn(
                "Subcontract", options=["Yes", "No", "Partial"]),
            "quote_required": st.column_config.SelectboxColumn(
                "Quote Required", options=["Yes", "No"]),
            "status": st.column_config.SelectboxColumn(
                "Status", options=["Ready", "Pending", "Quotes Pending",
                                   "Clarification Needed"]),
        },
        disabled=["id", "scope"],
        key="scope_editor",
    )

    if st.button("Save Scope Changes", type="primary"):
        for _, row in edited.iterrows():
            db.update_scope_item(int(row["id"]), {
                "quantity": float(row["quantity"] or 0),
                "unit": row["unit"],
                "self_perform": row["self_perform"],
                "subcontract": row["subcontract"],
                "quote_required": row["quote_required"],
                "status": row["status"],
            })
        notif.activity("Scope breakdown updated", opp_id, "scope")
        st.success("Scope changes saved.")

    st.markdown("---")
    st.markdown("### Create Subcontractor Bid Package")
    c1, c2, c3 = st.columns(3)
    trade = c1.selectbox(
        "Trade",
        ["Electrical", "Mechanical", "Process Piping", "Concrete",
         "Survey", "HVAC", "Specialty Equipment", "Traffic Control",
         "Landscaping", "Other"],
    )
    plan_section = c2.text_input("Plan Sections", "E-1 through E-12, "
                                                  "Spec 26 00 00")
    due_date = c3.date_input("Quote Due Date")

    notes = st.text_area("Notes to subcontractors",
                         "Please review the attached scope and submit "
                         "pricing by the due date.")
    if st.button("Create Bid Package", type="primary"):
        notif.activity(f"Bid package created for {trade}", opp_id,
                       "bid_package")
        st.session_state[f"pkg_{opp_id}_{trade}"] = {
            "trade": trade, "plan_section": plan_section,
            "due_date": str(due_date), "notes": notes,
        }
        st.success(f"Bid package created for {trade}.")

    pkg = st.session_state.get(f"pkg_{opp_id}_{trade}")
    if pkg:
        st.markdown("#### Generated Bid Package Preview")
        st.markdown(
            f"""
            <div class="white-card">
            <b>Project:</b> {opp['project']}<br>
            <b>Trade:</b> {pkg['trade']}<br>
            <b>Plan Sections:</b> {pkg['plan_section']}<br>
            <b>Pricing Deadline:</b> {pkg['due_date']}<br>
            <b>Documents:</b> Plans, Specs, Addenda 1–3<br>
            <b>Submission Instructions:</b> Submit pricing via the
            BidFlow portal or email the estimating department.<br>
            <b>Notes:</b> {pkg['notes']}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Send to 8 Subcontractors", type="primary"):
            notif.activity(
                f"8 {trade} subcontractors invited for {opp['project']}",
                opp_id, "invitation",
            )
            notif.notify("blue",
                         f"8 {trade} bid invitations queued for "
                         f"{opp['project']}", opp_id)
            st.info("Demo mode — 8 bid invitations queued.")


# ---------------------------------------------------------------------------
# Page: Estimates
# ---------------------------------------------------------------------------

def page_estimates():
    st.markdown("## 🧮 Estimating Workspace")
    st.caption("Fictional demo values. Edit direct, indirect, contingency, "
               "and markup to recalculate the final bid.")

    opp_id = st.session_state.selected_opp
    opp = db.get_opportunity(opp_id)
    if not opp:
        st.warning("No opportunity selected.")
        return

    st.markdown(f"**Project:** {opp['project']} · "
                f"**Value:** {fmt.money(opp.get('estimated_value', 0))}")

    est = db.get_estimate(opp_id) or {}

    with st.form("estimate_form"):
        st.markdown("### Direct Costs")
        c1, c2, c3, c4 = st.columns(4)
        labor = c1.number_input("Labor", value=float(est.get("labor", 3_200_000)),
                                step=10_000.0, format="%.0f")
        materials = c2.number_input("Materials",
                                    value=float(est.get("materials", 4_100_000)),
                                    step=10_000.0, format="%.0f")
        equipment = c3.number_input("Equipment",
                                    value=float(est.get("equipment", 1_900_000)),
                                    step=10_000.0, format="%.0f")
        subcontractors = c4.number_input(
            "Subcontractors",
            value=float(est.get("subcontractors", 4_650_000)),
            step=10_000.0, format="%.0f")

        st.markdown("### Indirect Costs")
        c1, c2, c3, c4, c5 = st.columns(5)
        mobilization = c1.number_input(
            "Mobilization", value=float(est.get("mobilization", 350_000)),
            step=5_000.0, format="%.0f")
        temp = c2.number_input(
            "Temporary Facilities",
            value=float(est.get("temp_facilities", 180_000)),
            step=5_000.0, format="%.0f")
        supervision = c3.number_input(
            "Supervision", value=float(est.get("supervision", 420_000)),
            step=5_000.0, format="%.0f")
        insurance = c4.number_input(
            "Insurance", value=float(est.get("insurance", 120_000)),
            step=5_000.0, format="%.0f")
        permits = c5.number_input(
            "Permits", value=float(est.get("permits", 80_000)),
            step=5_000.0, format="%.0f")

        st.markdown("### Risk / Contingency")
        contingency_pct = st.slider(
            "Contingency %", 0.0, 15.0,
            float(est.get("contingency_pct", 5.0)), 0.5)

        st.markdown("### Markup")
        c1, c2 = st.columns(2)
        overhead_pct = c1.slider(
            "Overhead %", 0.0, 15.0,
            float(est.get("overhead_pct", 8.0)), 0.5)
        profit_pct = c2.slider(
            "Profit %", 0.0, 15.0,
            float(est.get("profit_pct", 6.0)), 0.5)

        submitted = st.form_submit_button("Save & Recalculate",
                                          type="primary")

    payload = {
        "labor": labor, "materials": materials, "equipment": equipment,
        "subcontractors": subcontractors, "mobilization": mobilization,
        "temp_facilities": temp, "supervision": supervision,
        "insurance": insurance, "permits": permits,
        "contingency_pct": contingency_pct,
        "overhead_pct": overhead_pct, "profit_pct": profit_pct,
    }

    if submitted:
        db.upsert_estimate(opp_id, payload)
        notif.activity("Estimate updated", opp_id, "estimate")
        st.success("Estimate saved and recalculated.")

    calc = calculations.compute_estimate(payload)

    st.markdown("---")
    st.markdown("### Estimate Summary")
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi("Direct Cost", fmt.money(calc["direct_cost"], compact=True))
        kpi("Indirect Cost", fmt.money(calc["indirect_cost"], compact=True))
    with c2:
        kpi("Contingency", fmt.money(calc["contingency"], compact=True))
        kpi("Total Cost", fmt.money(calc["total_cost"], compact=True))
    with c3:
        kpi("Markup", fmt.money(calc["markup"], compact=True))
        kpi("Final Bid", fmt.money(calc["final_bid"], compact=True))
    st.markdown(
        f"**Gross Margin:** {calc['gross_margin']:.1f}%"
    )

    st.markdown("---")
    st.markdown("### Estimate Health")
    items = db.get_scope_items(opp_id)
    quotes = db.get_quotes(opp_id)
    health = calculations.estimate_health(items, quotes)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Scope Coverage", f"{health['scope_coverage']:.0f}%")
    c2.metric("Quote Coverage", f"{health['quote_coverage']:.0f}%")
    c3.metric("Material Coverage", f"{health['material_coverage']:.0f}%")
    c4.metric("Risk Coverage", f"{health['risk_coverage']:.0f}%")
    c5.metric("Completeness", f"{health['completeness']:.0f}%")

    st.progress(int(health["completeness"]) / 100)

    st.markdown("**Warnings**")
    for w in health["warnings"]:
        st.markdown(f"- {w}")


# ---------------------------------------------------------------------------
# Page: Subcontractors
# ---------------------------------------------------------------------------

def page_subcontractors():
    st.markdown("## 🤝 Subcontractors")
    st.caption("Fictional demo subcontractor directory and quote status.")

    subs = db.get_subcontractors()
    if not subs:
        st.info("No subcontractors in the demo dataset.")
        return

    df = pd.DataFrame(subs)
    trades = sorted(df["trade"].dropna().unique().tolist())
    trade_filter = st.multiselect("Filter by Trade", trades)
    status_filter = st.multiselect(
        "Filter by Quote Status",
        sorted(df["quote_status"].dropna().unique().tolist()),
    )

    filtered = df.copy()
    if trade_filter:
        filtered = filtered[filtered["trade"].isin(trade_filter)]
    if status_filter:
        filtered = filtered[filtered["quote_status"].isin(status_filter)]

    st.markdown(f"**{len(filtered)}** subcontractors.")
    st.dataframe(
        filtered[[
            "company", "trade", "contact", "email", "phone", "location",
            "insurance_status", "w9_status", "quote_status", "last_contact",
            "projects_worked",
        ]].rename(columns={
            "company": "Company", "trade": "Trade", "contact": "Contact",
            "email": "Email", "phone": "Phone", "location": "Location",
            "insurance_status": "Insurance", "w9_status": "W-9",
            "quote_status": "Quote Status", "last_contact": "Last Contact",
            "projects_worked": "Projects",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Update Subcontractor Status")
    options = {f"{s['company']} — {s['trade']}": s["id"] for s in subs}
    choice = st.selectbox("Select subcontractor", list(options.keys()))
    new_status = st.selectbox(
        "Quote Status",
        ["Invited", "Plans Sent", "Pricing Pending", "Quote Received",
         "Clarification Needed", "Selected", "Not Selected"],
    )
    if st.button("Update Status", type="primary"):
        db.update_subcontractor(options[choice], {
            "quote_status": new_status,
            "last_contact": datetime.now().strftime("%Y-%m-%d"),
        })
        notif.activity(f"Subcontractor status updated: {choice} → "
                       f"{new_status}", None, "subcontractor")
        st.success("Status updated.")


# ---------------------------------------------------------------------------
# Page: Vendor Quotes
# ---------------------------------------------------------------------------

def page_vendor_quotes():
    st.markdown("## 💬 Vendor Quotes")
    st.caption("Quote comparison — price, lead time, validity, compliance, "
               "and completeness. Fictional demo data.")

    opp_id = st.session_state.selected_opp
    opp = db.get_opportunity(opp_id)
    if not opp:
        st.warning("No opportunity selected.")
        return

    st.markdown(f"**Project:** {opp['project']}")

    quotes = db.get_quotes(opp_id)
    if not quotes:
        st.info("No quotes yet for this opportunity.")
        return

    df = pd.DataFrame(quotes)
    display = df[[
        "vendor", "scope", "amount", "lead_time_weeks", "validity_days",
        "compliance", "status", "exceptions",
    ]].rename(columns={
        "vendor": "Vendor", "scope": "Scope", "amount": "Quote",
        "lead_time_weeks": "Lead Time (wks)",
        "validity_days": "Validity (days)", "compliance": "Compliance",
        "status": "Status", "exceptions": "Exceptions",
    })
    display["Quote"] = display["Quote"].apply(
        lambda v: fmt.money(v, compact=True) if v else "Pending"
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

    if st.button("Compare Quotes", type="primary"):
        compared = calculations.compare_quotes(quotes)
        if not compared:
            st.warning("No comparable quotes (all amounts are zero or "
                       "pending).")
            return
        st.markdown("### Quote Comparison")
        st.markdown(
            "This comparison surfaces price, scope coverage, lead time, "
            "compliance, quote completeness, exceptions, and commercial "
            "terms. It does **not** simply recommend the lowest price."
        )
        for q in compared:
            with st.container():
                st.markdown(
                    f"""
                    <div class="white-card">
                    <b>{q['vendor']}</b> — {q['scope']}<br>
                    <b>Price:</b> {fmt.money(q['amount'])} ·
                    <b>Delta vs. low:</b> {fmt.money(q['delta_vs_low'])} ·
                    <b>Price Rank:</b> {q['price_rank']}<br>
                    <b>Lead Time:</b> {q['lead_time_weeks']} weeks ·
                    <b>Validity:</b> {q['validity_days']} days ·
                    <b>Compliance:</b> {q['compliance']}<br>
                    <b>Completeness:</b> {q['completeness']} ·
                    <b>Exceptions:</b> {q['exceptions']}<br>
                    <b>Commercial Terms:</b> Net 30, freight as noted.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# Page: Bid Review
# ---------------------------------------------------------------------------

def page_bid_review():
    st.markdown("## 🔍 Bid Review Center")
    st.caption("Management review before submission. Fictional demo data.")

    opp_id = st.session_state.selected_opp
    opp = db.get_opportunity(opp_id)
    if not opp:
        st.warning("No opportunity selected.")
        return

    st.markdown(f"**Project:** {opp['project']}")

    est = db.get_estimate(opp_id) or {}
    calc = calculations.compute_estimate(est)
    items = db.get_scope_items(opp_id)
    quotes = db.get_quotes(opp_id)
    addenda = db.get_addenda(opp_id)

    risk = ai.analyze_risks(opp, quotes, items, addenda)

    c1, c2, c3 = st.columns(3)
    c1.metric("Bid Amount", fmt.money(calc["final_bid"], compact=True))
    c2.metric("Estimated Cost", fmt.money(calc["total_cost"], compact=True))
    c3.metric("Gross Margin", f"{calc['gross_margin']:.1f}%")

    c4, c5, c6 = st.columns(3)
    c4.metric("Scope Coverage", f"{risk['scope_coverage']:.0f}%")
    c5.metric("Quote Coverage", f"{risk['quote_coverage']:.0f}%")
    c6.metric("Overall Readiness", f"{risk['overall_readiness']:.0f}%")

    st.markdown("---")
    st.markdown("### Critical Items")
    critical = []
    if risk["pending_quotes"]:
        critical.append("Electrical quote pending")
    if risk["missing_docs"]:
        critical.append("Equipment lead time not confirmed")
    if risk["unresolved_addenda"]:
        critical.append("Addendum review pending")
    critical.append("Insurance requirements need confirmation")
    critical.append("DBE/SBE participation requirements need review")
    for c in critical:
        st.markdown(f"- {c}")

    st.markdown("---")
    st.markdown("### AI Bid Risk Analysis")
    for key, r in risk["risks"].items():
        st.markdown(
            f"""
            <div class="white-card">
            <b>{key.replace('_', ' ').title()} Risk —</b>
            {fmt.badge(r['level'])}<br>
            <span style="color:#64748b;">{r['reason']}</span><br>
            <b>Recommended action:</b> {r['action']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Request Final Quotes", use_container_width=True):
        notif.activity("Requested final quotes", opp_id, "review")
        st.success("Demo mode — final quote requests queued.")
    if c2.button("Review Risks", use_container_width=True):
        st.session_state.page = "Bid Review"
        st.rerun()
    if c3.button("Mark Ready for Submission", use_container_width=True):
        db.update_opportunity(opp_id, {"status": "Bid Review",
                                       "readiness": 85})
        notif.activity("Marked ready for submission", opp_id, "review")
        st.success("Opportunity marked ready for submission.")
    if c4.button("Create Bid Summary", use_container_width=True):
        notif.activity("Bid summary created", opp_id, "review")
        st.success("Demo mode — bid summary created.")


# ---------------------------------------------------------------------------
# Page: Submissions
# ---------------------------------------------------------------------------

CHECKLIST = [
    "Plans reviewed",
    "Specifications reviewed",
    "Addenda reviewed",
    "Scope assigned",
    "Subcontractor quotes received",
    "Vendor quotes reviewed",
    "Estimate approved",
    "Bonds confirmed",
    "Insurance requirements reviewed",
    "Required forms completed",
    "Final bid reviewed",
    "Submission package ready",
]


def page_submissions():
    st.markdown("## 📤 Bid Submission")
    st.caption("Final bid checklist and submission package prep. "
               "Fictional demo data.")

    opp_id = st.session_state.selected_opp
    opp = db.get_opportunity(opp_id)
    if not opp:
        st.warning("No opportunity selected.")
        return

    st.markdown(f"**Project:** {opp['project']}")

    key = f"checklist_{opp_id}"
    if key not in st.session_state:
        st.session_state[key] = {c: False for c in CHECKLIST}

    st.markdown("### Final Bid Checklist")
    for c in CHECKLIST:
        st.session_state[key][c] = st.checkbox(
            c, value=st.session_state[key][c], key=f"chk_{opp_id}_{c}"
        )

    done = sum(1 for v in st.session_state[key].values() if v)
    pct_done = done / len(CHECKLIST) * 100
    st.progress(pct_done / 100)
    st.caption(f"{done} of {len(CHECKLIST)} complete ({pct_done:.0f}%)")

    if st.button("Prepare Submission Package", type="primary"):
        notif.activity("Submission package prepared", opp_id, "submission")
        notif.notify("green",
                     f"Submission package prepared for {opp['project']}",
                     opp_id)
        st.success("Submission package prepared in Demo Mode.")

    st.markdown("---")
    st.markdown("### Addenda Tracking")
    addenda = db.get_addenda(opp_id)
    if not addenda:
        st.caption("No addenda recorded.")
    for a in addenda:
        c1, c2, c3 = st.columns([1, 3, 1])
        c1.markdown(f"**Addendum #{a['number']}**")
        c2.markdown(
            f"Received {fmt.short_date(a.get('received_date', ''))} — "
            f"{a.get('notes', '')}"
        )
        if a.get("status") == "Reviewed":
            c3.markdown(fmt.badge("Reviewed"), unsafe_allow_html=True)
        else:
            if c3.button("Mark Reviewed", key=f"add_{a['id']}"):
                db.update_addendum(a["id"], {"status": "Reviewed"})
                notif.activity(
                    f"Addendum #{a['number']} marked reviewed", opp_id,
                    "addenda",
                )
                st.rerun()

    st.markdown("---")
    st.markdown("### Submission Actions")
    c1, c2 = st.columns(2)
    if c1.button("Mark Submitted", type="primary", use_container_width=True):
        db.update_opportunity(opp_id, {"status": "Submitted"})
        notif.activity(f"Bid submitted for {opp['project']}", opp_id,
                       "submission")
        notif.notify("blue", f"Bid submitted: {opp['project']}", opp_id)
        st.success("Bid marked submitted.")
    if c2.button("Mark Awarded", use_container_width=True):
        db.update_opportunity(opp_id, {"status": "Awarded"})
        notif.activity(f"Bid awarded: {opp['project']}", opp_id, "award")
        notif.notify("green", f"Bid awarded: {opp['project']}", opp_id)
        st.success("Bid marked awarded. Ready for project handoff.")
        st.session_state.page = "Projects"
        st.rerun()


# ---------------------------------------------------------------------------
# Page: Projects
# ---------------------------------------------------------------------------

def page_projects():
    st.markdown("## 🏗️ Projects")
    st.caption("Bid → Project handoff. Fictional demo data.")

    opp_id = st.session_state.selected_opp
    opp = db.get_opportunity(opp_id)

    if opp and opp.get("status") == "Awarded":
        st.markdown("### Convert to Project")
        st.info(
            f"**{opp['project']}** is awarded. Convert it into a project "
            "record with estimate, scope, vendors, subcontractors, "
            "documents, and budget linked."
        )
        if st.button("Convert to Project", type="primary"):
            pid = db.create_project({
                "opportunity_id": opp_id,
                "project": opp["project"],
                "owner": opp.get("owner", ""),
                "location": opp.get("location", ""),
                "contract_value": opp.get("estimated_value", 0),
                "project_manager": opp.get("project_manager", "TBD"),
                "estimate_linked": 1, "subs_linked": 1,
                "vendors_linked": 1, "docs_linked": 1,
                "status": "Active",
                "start_date": datetime.now().strftime("%Y-%m-%d"),
            })
            notif.activity(
                f"Project created from awarded bid: {opp['project']}",
                opp_id, "handoff",
            )
            notif.notify("green",
                         f"Bid → Project handoff complete: "
                         f"{opp['project']}", opp_id)
            st.session_state[f"handoff_{opp_id}"] = pid
            st.success("Bid → Project Handoff Complete")

    projects = db.get_projects()
    if not projects:
        st.info("No projects yet. Mark a bid as Awarded and convert it.")
        return

    df = pd.DataFrame(projects)
    st.markdown(f"**{len(df)}** active projects.")
    st.dataframe(
        df[[
            "project", "owner", "location", "contract_value",
            "project_manager", "status", "start_date",
        ]].rename(columns={
            "project": "Project", "owner": "Owner", "location": "Location",
            "contract_value": "Contract Value",
            "project_manager": "Project Manager", "status": "Status",
            "start_date": "Start Date",
        }),
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# Page: Follow-Ups
# ---------------------------------------------------------------------------

def page_followups():
    st.markdown("## 🔔 Follow-Ups")
    st.caption("Owner, subcontractor, and clarification follow-ups. "
               "Fictional demo data.")

    followups = db.get_followups()
    if not followups:
        st.info("No follow-ups scheduled.")
        return

    df = pd.DataFrame(followups)
    st.dataframe(
        df[["project", "status", "next_followup", "action"]].rename(columns={
            "project": "Project", "status": "Status",
            "next_followup": "Next Follow-Up", "action": "Action",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.markdown("### Generate Follow-Up Message")
    options = {f["project"]: f["id"] for f in followups}
    choice = st.selectbox("Select project", list(options.keys()))
    selected = next(f for f in followups if f["id"] == options[choice])

    msg = selected.get("message") or (
        f"Following up on {selected['project']}. Please let us know if "
        "you need any additional information."
    )
    st.text_area("Draft message", value=msg, height=140)
    if st.button("Generate Follow-Up", type="primary"):
        notif.activity(
            f"Follow-up generated for {selected['project']}", None,
            "followup",
        )
        st.success("Demo mode — follow-up message generated (not sent).")


# ---------------------------------------------------------------------------
# Page: Analytics
# ---------------------------------------------------------------------------

def page_analytics():
    st.markdown("## 📈 Analytics")
    st.caption("Fictional demo data. Clean, professional charts.")

    opps = pd.DataFrame(db.get_opportunities())
    quotes = pd.DataFrame(db.get_quotes())

    if opps.empty:
        st.info("No data to chart.")
        return

    c1, c2 = st.columns(2)
    with c1:
        by_type = opps.groupby("project_type")["estimated_value"].sum()\
            .reset_index().sort_values("estimated_value", ascending=False)
        fig = px.bar(by_type, x="project_type", y="estimated_value",
                     title="Opportunity Pipeline Value by Project Type")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          font_color="#0f172a")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        by_status = opps.groupby("status").size().reset_index(name="count")
        fig = px.pie(by_status, names="status", values="count",
                     title="Bids by Status", hole=0.45)
        fig.update_layout(paper_bgcolor="white", font_color="#0f172a")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        fig = px.histogram(opps, x="readiness", nbins=10,
                           title="Bid Readiness Distribution")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          font_color="#0f172a")
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        if not quotes.empty:
            qc = quotes.groupby("status").size().reset_index(name="count")
            fig = px.bar(qc, x="status", y="count",
                         title="Quote Coverage by Status")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                              font_color="#0f172a")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Win / Loss History")
    win_loss = opps[opps["status"].isin(["Awarded", "Lost"])]\
        .groupby("status").size().reset_index(name="count")
    if not win_loss.empty:
        fig = px.bar(win_loss, x="status", y="count",
                     title="Win / Loss History",
                     color="status",
                     color_discrete_map={"Awarded": "#16a34a",
                                         "Lost": "#dc2626"})
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          font_color="#0f172a")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Upcoming Bid Deadlines")
    upcoming = opps.copy()
    upcoming["bid_due_date"] = upcoming["bid_due"].str[:10]
    upcoming = upcoming[upcoming["bid_due_date"] >=
                        datetime.now().strftime("%Y-%m-%d")]
    upcoming = upcoming.sort_values("bid_due_date").head(10)
    if not upcoming.empty:
        fig = px.bar(upcoming, x="bid_due_date", y="estimated_value",
                     color="project_type",
                     title="Upcoming Bid Deadlines (Value)")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                          font_color="#0f172a")
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Page: AI Assistant
# ---------------------------------------------------------------------------

def page_assistant():
    st.markdown("## 🧠 AI Assistant")
    st.caption("Internal construction estimating assistant. Answers are "
               "generated deterministically from the local demo dataset. "
               "No external API required.")

    st.markdown("**Example questions:**")
    st.markdown(
        "- What bids are due this week?\n"
        "- Which bids have missing subcontractor quotes?\n"
        "- Show projects with low estimate readiness.\n"
        "- Which opportunities have unresolved addenda?\n"
        "- What needs attention before the Clearwater bid?\n"
        "- What subcontractor quotes are still pending?\n"
        "- Show me all high-risk bids."
    )

    question = st.text_input("Ask a question",
                             placeholder="e.g. What bids are due this week?")
    if st.button("Ask", type="primary") and question:
        data = {
            "opportunities": db.get_opportunities(),
            "quotes": db.get_quotes(),
            "subcontractors": db.get_subcontractors(),
            "addenda": db.get_addenda(),
            "followups": db.get_followups(),
            "notifications": db.get_notifications(),
            "projects": db.get_projects(),
        }
        answer = ai.assistant_answer(question, data)
        st.markdown("### Answer")
        st.markdown(answer)
        notif.activity(f"AI Assistant query: {question}", None, "ai")


# ---------------------------------------------------------------------------
# Page: Settings
# ---------------------------------------------------------------------------

def page_settings():
    st.markdown("## ⚙️ Settings")
    st.caption("Demo configuration. Changes are session-only.")

    st.markdown("### Demo Mode")
    st.toggle("Demo Mode enabled", value=True, disabled=True)

    st.markdown("### AI Provider")
    hf = bool(__import__("os").environ.get("HF_TOKEN"))
    st.markdown(
        f"- Hugging Face token detected: **{'Yes' if hf else 'No'}**\n"
        "- Deterministic extractor: **Always on**\n"
        "- Paid APIs required: **No**"
    )
    st.info(
        "The demo works perfectly without any API key. If you set the "
        "`HF_TOKEN` environment variable, BidFlow AI may optionally use a "
        "Hugging Face model to augment text extraction. The deterministic "
        "extractor always remains the source of truth."
    )

    st.markdown("### Data")
    st.markdown(
        f"- Opportunities: {db.count_rows('opportunities')}\n"
        f"- Subcontractors: {db.count_rows('subcontractors')}\n"
        f"- Vendors: {db.count_rows('vendors')}\n"
        f"- Quotes: {db.count_rows('quotes')}\n"
        f"- Projects: {db.count_rows('projects')}\n"
        f"- Activities: {db.count_rows('activities')}\n"
        f"- Notifications: {db.count_rows('notifications')}\n"
        f"- Addenda: {db.count_rows('addenda')}\n"
        f"- Follow-ups: {db.count_rows('followups')}"
    )

    st.markdown("### Reset Demo Data")
    st.caption("Deletes the local SQLite demo database and reseeds it.")
    if st.button("Reset Demo Database"):
        import os
        path = os.path.join("data", "tlc_bidflow.db")
        if os.path.exists(path):
            os.remove(path)
        db.init_db()
        seed_demo_data()
        st.success("Demo database reset and reseeded.")
        st.rerun()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def route():
    page = st.session_state.page
    if page == "Overview":
        page_overview()
    elif page == "Bid Opportunities":
        page_opportunities()
    elif page == "Opportunity Detail":
        page_opportunity_detail()
    elif page == "AI Bid Intake":
        page_ai_intake()
    elif page == "Bid Calendar":
        page_calendar()
    elif page == "Scope Breakdown":
        page_scope()
    elif page == "Estimates":
        page_estimates()
    elif page == "Subcontractors":
        page_subcontractors()
    elif page == "Vendor Quotes":
        page_vendor_quotes()
    elif page == "Bid Review":
        page_bid_review()
    elif page == "Submissions":
        page_submissions()
    elif page == "Projects":
        page_projects()
    elif page == "Follow-Ups":
        page_followups()
    elif page == "Analytics":
        page_analytics()
    elif page == "AI Assistant":
        page_assistant()
    elif page == "Settings":
        page_settings()
    else:
        page_overview()


def main():
    header()
    sidebar()
    concept_label()
    route()


if __name__ == "__main__":
    main()