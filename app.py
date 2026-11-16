"""AssistLana RFP Intelligence - human-in-the-loop MVP."""

import os
import tempfile

import pandas as pd
import streamlit as st

from modules.pdf_processor import extract_pdf_text
from modules.requirement_extractor import extract_requirements
from modules.spreadsheet_processor import extract_spreadsheet_text
from modules.opportunity_storage import initialise_database, list_opportunities, load_opportunity, save_opportunity
from modules.rfp_analysis import (
    DEFAULT_CAPABILITIES,
    bid_recommendation,
    clarification_questions,
    identify_risks,
    match_requirements,
    parse_capabilities,
    proposal_mapping,
)


st.set_page_config(
    page_title="AssistLana | RFP Intelligence",
    page_icon=":material/description:",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Modern Enterprise SaaS Styling */
    .stApp {
        background-color: #0B0F19;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(17, 24, 39, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 12px 16px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 500;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _initialise_state() -> None:
    defaults = {
        "pages": [],
        "requirements": [],
        "matches": [],
        "risks": [],
        "questions": [],
        "proposal": [],
        "recommendation": {},
        "file_name": "",
        "opportunity_stage": "New",
        "human_decision": "Pending human review",
        "decision_notes": "",
        "opportunity_id": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _process_upload(uploaded_file) -> None:
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        suffix = os.path.splitext(uploaded_file.name)[1].casefold()
        if suffix == ".pdf":
            pages = extract_pdf_text(temp_path)
        elif suffix in {".xls", ".xlsx", ".xlx"}:
            pages = extract_spreadsheet_text(temp_path)
        else:
            raise ValueError("Supported formats are PDF, XLS, and XLSX")
        requirements = extract_requirements(pages)
        st.session_state.update({
            "pages": pages,
            "requirements": requirements,
            "matches": [],
            "risks": [],
            "questions": [],
            "proposal": [],
            "recommendation": {},
            "file_name": uploaded_file.name,
            "opportunity_stage": "Analysis",
            "opportunity_id": None,
        })
        source_units = "pages" if suffix == ".pdf" else "worksheets"
        st.success(f"Processed {uploaded_file.name}: {len(pages)} {source_units} and {len(requirements)} requirements found.", icon=":material/check_circle:")
    except Exception as error:
        st.error(f"Document processing failed: {error}", icon=":material/error:")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def _load_sample_file(file_path: str, file_name: str) -> None:
    try:
        suffix = os.path.splitext(file_name)[1].casefold()
        if suffix == ".pdf":
            pages = extract_pdf_text(file_path)
        elif suffix in {".xls", ".xlsx", ".xlx"}:
            pages = extract_spreadsheet_text(file_path)
        else:
            raise ValueError("Supported formats are PDF, XLS, and XLSX")
        requirements = extract_requirements(pages)
        st.session_state.update({
            "pages": pages,
            "requirements": requirements,
            "matches": [],
            "risks": [],
            "questions": [],
            "proposal": [],
            "recommendation": {},
            "file_name": file_name,
            "opportunity_stage": "Analysis",
            "opportunity_id": None,
        })
        _run_analysis("\n".join(DEFAULT_CAPABILITIES))
        st.toast(f"Loaded {file_name}: {len(requirements)} requirements extracted.", icon=":material/check_circle:")
        st.rerun()
    except Exception as error:
        st.error(f"Sample load failed: {error}", icon=":material/error:")


def _run_analysis(capability_text: str) -> None:
    requirements = st.session_state.get("requirements", [])
    matches = match_requirements(requirements, capability_text)
    risks = identify_risks(matches)
    st.session_state.update({
        "matches": matches,
        "risks": risks,
        "questions": clarification_questions(matches),
        "proposal": proposal_mapping(matches),
        "recommendation": bid_recommendation(matches, risks),
    })
    st.session_state["opportunity_stage"] = "Review"
    st.success("Capability comparison and decision-support analysis updated.", icon=":material/insights:")


def _current_payload() -> dict[str, object]:
    return {
        key: st.session_state[key]
        for key in ("pages", "requirements", "matches", "risks", "questions", "proposal", "recommendation", "file_name", "opportunity_stage", "human_decision", "decision_notes")
        if key in st.session_state
    }


def _normalise_proposal_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Migrate proposal rows created before the current proposal schema."""
    normalised = []
    for row in rows:
        item = dict(row)
        evidence = str(item.get("Evidence / Notes") or "No matching capability provided")
        item.setdefault("Draft Response", f"Draft: Confirm the requirement and supporting evidence: {evidence}.")
        item.setdefault("Human Approval", "Not Reviewed")
        normalised.append(item)
    return normalised


def _save_current_opportunity() -> None:
    if not st.session_state["file_name"]:
        st.warning("Process an RFP before saving an opportunity.", icon=":material/upload_file:")
        return
    opportunity_id = save_opportunity(_current_payload(), st.session_state.get("opportunity_id"))
    st.session_state["opportunity_id"] = opportunity_id
    st.success(f"Opportunity saved as #{opportunity_id}.", icon=":material/save:")


def _load_saved_opportunity(opportunity_id: int) -> None:
    payload = load_opportunity(opportunity_id)
    if not payload:
        st.error("Saved opportunity could not be loaded.", icon=":material/error:")
        return
    for key, value in payload.items():
        if key in {"opportunity_id", "pages", "requirements", "matches", "risks", "questions", "proposal", "recommendation", "file_name", "opportunity_stage", "human_decision", "decision_notes"}:
            st.session_state[key] = value
    st.session_state.pop("decision_center_select", None)
    st.session_state.pop("requirements_editor", None)
    st.session_state.pop("proposal_editor", None)
    st.rerun()


_initialise_state()
initialise_database()
st.session_state["proposal"] = _normalise_proposal_rows(st.session_state["proposal"])

st.title("AssistLana - RFP intelligence")
st.caption("AI-assisted tender analysis for evidence-led, human-approved decisions")

with st.sidebar:
    user_role = st.selectbox(
        "User Role",
        ["Business Development / Pre-Sales", "Admin"],
        index=0,
        help="Switch between Pre-Sales opportunity workflow and Admin capability & portfolio oversight.",
    )
    st.divider()
    st.header("Opportunity intake")
    uploaded_file = st.file_uploader("Upload an RFP or tender document", type=["pdf", "xls", "xlsx", "xlx"])
    if uploaded_file and st.button("Process document", width="stretch", type="primary"):
        _process_upload(uploaded_file)

    st.divider()
    st.subheader("Company capability profile")
    capability_text = st.text_area(
        "Add one capability per line",
        value="\n".join(DEFAULT_CAPABILITIES),
        height=180,
        help="This profile is used only to produce explainable matches and gaps.",
    )
    if st.button("Run capability analysis", width="stretch", disabled=not st.session_state["requirements"]):
        _run_analysis(capability_text)

    st.divider()
    stage_options = ["New", "Analysis", "Review", "Bid Decision", "Proposal", "Submitted", "Won", "Lost"]
    st.session_state["opportunity_stage"] = st.selectbox(
        "Opportunity stage", stage_options, index=stage_options.index(st.session_state["opportunity_stage"]),
    )
    st.caption(f"Human decision: **{st.session_state['human_decision']}**")
    st.divider()
    st.subheader("Saved opportunities")
    saved_opportunities = list_opportunities()
    opportunity_labels = ["Create new / current opportunity"] + [
        f"#{item['id']} · {item['file_name']} · {item['stage']}" for item in saved_opportunities
    ]
    selected_saved = st.selectbox("Load a saved opportunity", opportunity_labels, key="saved_opportunity_picker")
    if st.button("Load selected opportunity", width="stretch", disabled=selected_saved == opportunity_labels[0], icon=":material/folder_open:"):
        selected_id = saved_opportunities[opportunity_labels.index(selected_saved) - 1]["id"]
        _load_saved_opportunity(int(selected_id))
    if st.button("Save current opportunity", width="stretch", disabled=not st.session_state["file_name"], icon=":material/save:"):
        _save_current_opportunity()
    if st.button("Clear current opportunity", width="stretch"):
        for key in ("pages", "requirements", "matches", "risks", "questions", "proposal", "recommendation", "file_name"):
            st.session_state[key] = {} if key == "recommendation" else [] if key != "file_name" else ""
        st.session_state.pop("decision_center_select", None)
        st.session_state.pop("saved_opportunity_picker", None)
        st.session_state["opportunity_id"] = None
        st.session_state["opportunity_stage"] = "New"
        st.session_state["human_decision"] = "Pending human review"
        st.rerun()

requirements = st.session_state["requirements"]
matches = st.session_state["matches"]
risks = st.session_state["risks"]
recommendation = st.session_state["recommendation"]
if "decision_center_select" in st.session_state:
    st.session_state["human_decision"] = st.session_state["decision_center_select"]

if not requirements:
    if user_role == "Admin":
        st.info("Admin Mode: Manage organization capabilities and review historical portfolio metrics.", icon=":material/admin_panel_settings:")
        saved_rows = list_opportunities()
        if saved_rows:
            st.subheader("Organization Portfolio Overview")
            p_df = pd.DataFrame(saved_rows)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Tracked Opportunities", len(p_df))
            won_cnt = sum(p_df["stage"] == "Won")
            lost_cnt = sum(p_df["stage"] == "Lost")
            win_rate = f"{(won_cnt / (won_cnt + lost_cnt) * 100):.1f}%" if (won_cnt + lost_cnt) > 0 else "N/A"
            c2.metric("Won Opportunities", won_cnt)
            c3.metric("Lost Opportunities", lost_cnt)
            c4.metric("Win Rate", win_rate)

            st.dataframe(
                p_df.rename(columns={"id": "ID", "file_name": "RFP File", "stage": "Stage", "human_decision": "Decision", "updated_at": "Updated"}),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No saved opportunities in the database yet. Pre-Sales teams can upload and save opportunities to populate this view.")
    else:
        # Executive Command Hero Landing
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
                        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 26px; margin-bottom: 22px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.35);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3);
                                 padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                        ● System Active & Ready
                    </span>
                    <span style="color: #94A3B8; font-size: 13px;">Pre-Sales Intelligence Platform v2.0</span>
                </div>
                <h2 style="color: #F8FAFC; margin: 0 0 8px 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px;">
                    AI-Assisted Tender Intelligence & Bid Feasibility System
                </h2>
                <p style="color: #94A3B8; font-size: 15px; margin: 0; max-width: 820px; line-height: 1.6;">
                    Accelerate RFP review from days to seconds. Automatically extract complex compliance requirements, 
                    detect fatal capability gaps, analyze contractual liabilities, and produce explainable Bid / No-Bid recommendations.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.info("💡 Quick Start: Upload your tender document from the sidebar or click either pre-loaded sample below for an instant walkthrough.", icon=":material/lightbulb:")

        st.subheader("⚡ Quick Demo: Test with Pre-Loaded Tenders", anchor=False)
        st.caption("No tender file on hand? Click either button to load realistic sample RFPs and inspect the complete analysis immediately:")

        qc1, qc2 = st.columns(2)
        with qc1:
            with st.container(border=True):
                st.markdown("### 🏢 Smart City IoT Platform RFP (PDF)")
                st.caption("4-page municipal tender with ISO 27001 requirements, 5-yr experience, 99.9% SLA, and penalties.")
                if st.button("🚀 Load Smart City Tender (PDF)", type="primary", use_container_width=True):
                    sample_path = os.path.join(os.path.dirname(__file__), "test_files", "Sample_Enterprise_SmartCity_RFP.pdf")
                    _load_sample_file(sample_path, "Sample_Enterprise_SmartCity_RFP.pdf")
        with qc2:
            with st.container(border=True):
                st.markdown("### 📋 Sewage Treatment Plant BOQ (Excel)")
                st.caption("Real-world government Bill of Quantities workbook with operator mandates and supply items.")
                if st.button("📊 Load BOQ Tender (Excel)", type="secondary", use_container_width=True):
                    sample_path = os.path.join(os.path.dirname(__file__), "test_files", "BOQ_979798.xls")
                    _load_sample_file(sample_path, "BOQ_979798.xls")

        st.divider()
        st.subheader("🔍 4-Stage Decision-Support Pipeline", anchor=False)
        w1, w2, w3, w4 = st.columns(4)
        with w1:
            st.markdown("**1. Multi-Format Intake**")
            st.caption("Native parsing of PDFs, Excel workbooks (.xls, .xlsx), and portal HTML tables into traceable units.")
        with w2:
            st.markdown("**2. Clause Intelligence**")
            st.caption("Deterministic extraction across 9 categories (Technical, Eligibility, Timeline) with deadline detection.")
        with w3:
            st.markdown("**3. Capability Matching**")
            st.caption("Token overlap scoring against your company profile to surface fatal deal-breakers and core strengths.")
        with w4:
            st.markdown("**4. Human-in-the-Loop**")
            st.caption("Explainable 0–100 score. Proposal authoring strictly locked until human business approval.")
else:
    with st.container(border=True):
        st.subheader("What to do next", anchor=False)
        st.caption("Follow these steps before making a final business decision.")
        step_cols = st.columns(4)
        workflow_steps = [
            ("1", "Review requirements", "Confirm type, deadline, and source."),
            ("2", "Check capability match", "Validate matches and gaps."),
            ("3", "Review risks", "Assign actions for open risks."),
            ("4", "Make human decision", "Choose Bid, No-Bid, or Hold."),
        ]
        for column, (number, title, description) in zip(step_cols, workflow_steps):
            with column:
                st.markdown(f"**{number}. {title}**")
                st.caption(description)
        st.progress(
            {"New": 0.2, "Analysis": 0.4, "Review": 0.7, "Bid Decision": 0.85, "Proposal": 1.0}.get(
                st.session_state["opportunity_stage"], 0.7
            ),
            text=f"Current stage: {st.session_state['opportunity_stage']}",
        )

    st.subheader("Opportunity dashboard")
    metrics = [
        ("RFP pages", len(st.session_state["pages"])),
        ("Requirements", len(requirements)),
        ("Mandatory", sum(item.get("Type") == "Mandatory" for item in requirements)),
        ("Deadlines identified", sum(bool(item.get("Deadline")) for item in requirements)),
        ("Open risks", len(risks)),
        ("Human decision", st.session_state["human_decision"]),
    ]
    with st.container(horizontal=True):
        for label, value in metrics:
            st.metric(label, value, border=True)

    saved_label = f"Saved opportunity #{st.session_state['opportunity_id']}" if st.session_state.get("opportunity_id") else "Unsaved opportunity"
    st.caption(f"Opportunity: {st.session_state['file_name']} | Stage: {st.session_state['opportunity_stage']} | {saved_label}")
    tab_titles = ["Dashboard", "Requirements", "Capability match", "Risks and decision", "Proposal support"]
    if user_role == "Admin":
        tab_titles.append("Admin & Analytics")
    tab_objects = st.tabs(tab_titles)
    dashboard_tab, requirements_tab, matching_tab, decision_tab, proposal_tab = tab_objects[:5]

    with dashboard_tab:
        if not recommendation:
            st.info(
                "👉 To generate the Bid / No-Bid intelligence and feasibility score, "
                "click **'Run capability analysis'** in the sidebar. The system will compare requirements against your company profile.",
                icon=":material/info:",
            )
        else:
            score = recommendation.get("Score", 0)
            signal = recommendation.get("Signal", "")
            mandatory_total = recommendation.get("Mandatory Requirements", 0)
            mandatory_gaps_cnt = recommendation.get("Mandatory Gaps", 0)
            high_risks_cnt = recommendation.get("High Risks", 0)
            items_verify_cnt = recommendation.get("Items to Verify", 0)

            mandatory_gaps_list = [m for m in matches if m.get("Type") == "Mandatory" and m.get("Match Status") == "Gap"]
            matched_list = [m for m in matches if m.get("Match Status") == "Match"]

            # 1. Executive Verdict Card
            with st.container(border=True):
                st.subheader("🎯 Executive Bid / No-Bid Intelligence", anchor=False)
                st.caption("AI Decision Support — Transparent analysis based on company capabilities, mandatory compliance, and contract risks.")

                if "No-Bid" in signal or score < 70 or mandatory_gaps_cnt > 0:
                    st.error(
                        f"🛑 **RECOMMENDATION: NO-BID (High Disqualification Risk)**\n\n"
                        f"**Core Reason:** {mandatory_gaps_cnt} mandatory requirement(s) have zero matching capability evidence in your company profile. "
                        f"In enterprise/government tenders, failing a single mandatory specification causes automatic disqualification.",
                        icon=":material/cancel:",
                    )
                else:
                    st.success(
                        f"🟢 **RECOMMENDATION: BID (Strong Alignment)**\n\n"
                        f"**Core Reason:** Company capabilities meet all mandatory requirements with high confidence. Overall feasibility score is above threshold.",
                        icon=":material/check_circle:",
                    )

                # 4 Key Scorecard Metrics
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                with m_col1:
                    st.metric(
                        "Feasibility Score",
                        f"{score} / 100",
                        delta="Threshold: ≥ 70" if score >= 70 else "Below Threshold (< 70)",
                        delta_color="normal" if score >= 70 else "inverse",
                        help="Deduction-based score accounting for gaps, high risks, and verification items.",
                    )
                with m_col2:
                    met_mandatory = mandatory_total - mandatory_gaps_cnt
                    st.metric(
                        "Mandatory Compliance",
                        f"{met_mandatory} / {mandatory_total} Met",
                        delta=f"{mandatory_gaps_cnt} Fatal Gaps" if mandatory_gaps_cnt > 0 else "100% Compliant",
                        delta_color="inverse" if mandatory_gaps_cnt > 0 else "normal",
                        help="Mandatory requirements met vs gaps without evidence.",
                    )
                with m_col3:
                    st.metric(
                        "High-Severity Risks",
                        f"{high_risks_cnt} Risks",
                        delta="Penalties / SLAs" if high_risks_cnt > 0 else "Low Risk",
                        delta_color="inverse" if high_risks_cnt > 0 else "off",
                        help="Open contractual penalties, tight deadlines, or missing certifications.",
                    )
                with m_col4:
                    st.metric(
                        "Items to Clarify",
                        f"{items_verify_cnt} Items",
                        delta="Clarification Queue",
                        delta_color="off",
                        help="Unclear requirements or procedural checks needing review.",
                    )

            # 2. Side-by-Side: Fatal Deal-Breakers vs. Core Strengths
            col_gaps, col_strengths = st.columns(2)
            with col_gaps:
                with st.container(border=True):
                    st.subheader("🚨 Fatal Deal-Breakers (Why No-Bid?)", anchor=False)
                    st.caption("Mandatory requirements with ZERO supporting capability evidence:")
                    if mandatory_gaps_list:
                        for i, gap in enumerate(mandatory_gaps_list[:5], start=1):
                            page_ref = f"Page {gap.get('Source Page')}" if gap.get('Source Page') else "Workbook"
                            st.markdown(f"**{i}. [{gap.get('Category')}]** {gap.get('Requirement')}")
                            st.caption(f"📍 *Source: {page_ref}* · ❌ *Missing from company profile*")
                        if len(mandatory_gaps_list) > 5:
                            st.caption(f"*(and {len(mandatory_gaps_list) - 5} more mandatory gaps)*")
                    else:
                        st.success("✅ Zero mandatory capability gaps! All mandatory criteria are supported.")

            with col_strengths:
                with st.container(border=True):
                    st.subheader("✅ Company Strengths (Why Bid?)", anchor=False)
                    st.caption("Tender requirements with strong capability matches:")
                    if matched_list:
                        for i, match in enumerate(matched_list[:5], start=1):
                            page_ref = f"Page {match.get('Source Page')}" if match.get('Source Page') else "Workbook"
                            st.markdown(f"**{i}. [{match.get('Category')}]** {match.get('Requirement')}")
                            st.caption(f"📍 *Source: {page_ref}* · 🎯 *Evidence: {match.get('Capability Evidence')}*")
                        if len(matched_list) > 5:
                            st.caption(f"*(and {len(matched_list) - 5} more matching capabilities)*")
                    else:
                        st.info("No full capability matches found for current profile.")

            # 3. Transparent Mathematical Breakdown & Actionable Path
            with st.expander("🔢 How is the Feasibility Score Calculated? (Transparent Math)", expanded=False):
                st.markdown(
                    f"""
                    The score is calculated via an auditable deduction formula (starts at 100):
                    
                    $$\\text{{Score}} = \\max\\Big(0, \\min\\big(100, 100 - (30 \\times G) - (10 \\times R) - (3 \\times V)\\big)\\Big)$$
                    
                    | Factor | Quantity | Penalty per item | Deduction | Impact |
                    | :--- | :---: | :---: | :---: | :--- |
                    | **Base Score** | - | - | **100** | Starting point |
                    | **Mandatory Gaps ($G$)** | {mandatory_gaps_cnt} | -30 pts | **-{30 * mandatory_gaps_cnt}** | Fatal technical disqualification risk |
                    | **High Risks ($R$)** | {high_risks_cnt} | -10 pts | **-{10 * high_risks_cnt}** | Liquidated damages, harsh SLAs, short deadlines |
                    | **Verification Items ($V$)** | {items_verify_cnt} | -3 pts | **-{3 * items_verify_cnt}** | Unconfirmed scope, partial evidence |
                    | **Final Score** | - | - | **{score} / 100** | **{'Below Threshold (< 70)' if score < 70 else 'Viable for Bid (≥ 70)'}** |
                    """
                )
                if mandatory_gaps_cnt > 0:
                    st.info(
                        "💡 **How to turn this tender into a viable BID?**\n\n"
                        "1. **Consortium / Subcontractor:** Partner with an entity that holds the missing certifications (e.g., ISO 27001).\n"
                        "2. **Pre-Bid Query:** Request the client to accept equivalent ISO or industry experience during pre-bid meetings.\n"
                        "3. **Update Capability Profile:** If your company actually has these capabilities, add them to the company profile text area in the sidebar and click **'Run capability analysis'** again.",
                        icon=":material/lightbulb:",
                    )

            # 4. Human Decision Recording Gate
            with st.container(border=True):
                st.subheader("✍️ Record Human Bid / No-Bid Decision", anchor=False)
                st.caption("AI produces recommendations. Company governance requires a human business user to record the final call.")

                dec_col1, dec_col2 = st.columns([3, 2])
                with dec_col1:
                    decision_options = ["Pending human review", "Bid", "No-Bid", "Hold for clarification"]
                    selected_decision = st.radio(
                        "Select Decision",
                        decision_options,
                        index=decision_options.index(st.session_state["human_decision"]),
                        key="decision_center_select",
                        horizontal=True,
                    )
                    st.session_state["human_decision"] = selected_decision

                    decision_notes = st.text_input(
                        "Decision Justification / Reviewer Notes",
                        value=st.session_state.get("decision_notes", ""),
                        placeholder="e.g. Decided No-Bid due to ISO 27001 gap and harsh liquidated damages penalty.",
                        key="decision_notes_input",
                    )
                    st.session_state["decision_notes"] = decision_notes

                with dec_col2:
                    if selected_decision == "Bid":
                        st.success("Selected: **BID (Proceed with Proposal)**", icon=":material/check_circle:")
                        st.caption("Proposal preparation work queue is now unlocked.")
                        if st.button("Proceed to Proposal Authoring ➡️", type="primary", use_container_width=True):
                            st.session_state["opportunity_stage"] = "Proposal"
                            st.toast("Opportunity advanced to Proposal stage!", icon=":material/check_circle:")
                            st.rerun()
                    elif selected_decision == "No-Bid":
                        st.error("Selected: **NO-BID (Decline Opportunity)**", icon=":material/cancel:")
                        st.caption("Opportunity marked as declined to conserve team bandwidth.")
                    elif selected_decision == "Hold for clarification":
                        st.warning("Selected: **HOLD FOR CLARIFICATION**", icon=":material/pause_circle:")
                        st.caption("Awaiting response on pre-bid clarification questions.")
                    else:
                        st.info("Status: **PENDING HUMAN REVIEW**", icon=":material/pending:")

        category_counts = pd.Series([item["Category"] for item in requirements]).value_counts().rename_axis("Category").reset_index(name="Count")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Requirements by category")
            st.bar_chart(category_counts, x="Category", y="Count", alt="Requirements grouped by category")
        with col2:
            st.subheader("Risk register")
            risk_counts = pd.Series([item["Risk Level"] for item in risks]).value_counts().rename_axis("Risk Level").reset_index(name="Count") if risks else pd.DataFrame({"Risk Level": [], "Count": []})
            if risks:
                st.bar_chart(risk_counts, x="Risk Level", y="Count", alt="Open risks by severity")
            else:
                st.success("No risks generated yet. Run capability analysis to create the review register.")

        saved_rows = list_opportunities()
        if saved_rows:
            st.subheader("Opportunity portfolio")
            portfolio_df = pd.DataFrame(saved_rows).rename(columns={
                "id": "Opportunity ID",
                "file_name": "RFP file",
                "stage": "Stage",
                "human_decision": "Human decision",
                "updated_at": "Last updated",
            })
            st.dataframe(
                portfolio_df,
                width="stretch",
                hide_index=True,
                alt="Saved RFP opportunity portfolio",
            )

    with requirements_tab:
        st.subheader("Extracted requirements")
        requirements_df = pd.DataFrame(requirements)
        edited_df = st.data_editor(
            requirements_df,
            width="stretch",
            hide_index=True,
            num_rows="dynamic",
            disabled=["Source Page"],
            column_config={
                "Type": st.column_config.SelectboxColumn(
                    "Requirement type",
                    options=["Mandatory", "Optional", "Needs Verification"],
                    required=True,
                ),
                "Review Status": st.column_config.SelectboxColumn(
                    "Review status",
                    options=["Pending Review", "Verified", "Needs Clarification", "Rejected"],
                    required=True,
                ),
                "Deadline": st.column_config.TextColumn(
                    "Deadline / date",
                    help="Extracted date or reviewer correction",
                ),
                "Evidence": st.column_config.TextColumn("Evidence", help="Attach a document, link, or evidence description."),
                "Reviewer Notes": st.column_config.TextColumn("Reviewer notes", width="large"),
            },
            key="requirements_editor",
        )
        st.session_state["requirements"] = edited_df.to_dict("records")
        st.download_button("Download requirements CSV", requirements_df.to_csv(index=False).encode("utf-8"), "rfp_requirements.csv", "text/csv", width="content")
        with st.expander("Source document text"):
            for page in st.session_state["pages"]:
                st.markdown(f"**Page {page['page']}**")
                st.text(page["text"])

    with matching_tab:
        st.subheader("Requirement-to-capability comparison")
        if matches:
            st.dataframe(pd.DataFrame(matches), width="stretch", hide_index=True, alt="Requirement capability matching results", column_config={"Match Score": st.column_config.ProgressColumn("Match score", min_value=0, max_value=100, format="%d%%")})
        else:
            st.warning("Run capability analysis from the sidebar to create matches and gaps.")

    with decision_tab:
        st.subheader("Risk Register & Contractual Exposure")
        st.caption("Surfaces contractual liabilities, liquidated damages, tight milestones, and unverified obligations.")
        if recommendation:
            high_count = sum(r.get("Risk Level") == "High" for r in risks)
            med_count = sum(r.get("Risk Level") == "Medium" for r in risks)
            r_col1, r_col2, r_col3 = st.columns(3)
            r_col1.metric("Total Open Risks", len(risks))
            r_col2.metric("High-Severity Risks", high_count, delta="Immediate Mitigation Required" if high_count > 0 else "Clear", delta_color="inverse")
            r_col3.metric("Medium-Severity Risks", med_count)

            severity_filter = st.radio("Filter by Risk Level", ["All", "High", "Medium"], horizontal=True, key="risk_severity_filter")
            filtered_risks = [r for r in risks if severity_filter == "All" or r.get("Risk Level") == severity_filter]

            if filtered_risks:
                st.dataframe(
                    pd.DataFrame(filtered_risks),
                    width="stretch",
                    hide_index=True,
                    alt="Open risk register",
                    column_config={
                        "Risk Level": st.column_config.TextColumn("Severity"),
                        "Requirement": st.column_config.TextColumn("Clause / Requirement", width="large"),
                        "Reason": st.column_config.TextColumn("Risk Cause", width="medium"),
                        "Suggested Action": st.column_config.TextColumn("Recommended Mitigation", width="medium"),
                        "Source Page": st.column_config.TextColumn("Source Page"),
                    },
                )
            else:
                st.info(f"No risks found matching severity '{severity_filter}'.")

            st.download_button(
                "Download full risk register CSV",
                pd.DataFrame(risks).to_csv(index=False).encode("utf-8"),
                "rfp_risk_register.csv",
                "text/csv",
                width="content",
                icon=":material/download:",
            )

            if st.session_state["questions"]:
                st.divider()
                st.subheader("Pre-Bid Clarification Queue")
                st.caption("Draft clarification questions to submit to the procuring authority before the clarification deadline:")
                st.dataframe(pd.DataFrame(st.session_state["questions"]), width="stretch", hide_index=True, alt="Draft clarification questions")
                st.download_button(
                    "Download clarification questions CSV",
                    pd.DataFrame(st.session_state["questions"]).to_csv(index=False).encode("utf-8"),
                    "clarification_questions.csv",
                    "text/csv",
                    width="content",
                    icon=":material/download:",
                )
        else:
            st.info("Run capability analysis from the sidebar to generate the risk register and clarification queue.", icon=":material/info:")

    with proposal_tab:
        st.subheader("Proposal preparation work queue")
        if st.session_state["human_decision"] != "Bid":
            st.warning(
                "Proposal preparation is locked until the human decision is Bid. Review requirements, risks, and the decision centre first.",
                icon=":material/lock:",
            )
        else:
            st.info(
                "Use the draft as a starting point only. Assign an owner, add evidence, edit the response, and mark it approved before submission.",
                icon=":material/edit_document:",
            )
        if st.session_state["human_decision"] == "Bid" and st.session_state["proposal"]:
            proposal_df = pd.DataFrame(st.session_state["proposal"])
            edited_proposal = st.data_editor(
                proposal_df,
                width="stretch",
                hide_index=True,
                num_rows="dynamic",
                disabled=["Source Page"],
                column_config={
                    "Response Owner": st.column_config.TextColumn("Response owner", required=True),
                    "Response Status": st.column_config.SelectboxColumn(
                        "Response status",
                        options=["Not Started", "In Progress", "Ready for Review", "Complete"],
                        required=True,
                    ),
                    "Draft Response": st.column_config.TextColumn("Draft response", width="large"),
                    "Human Approval": st.column_config.SelectboxColumn(
                        "Human approval",
                        options=["Not Reviewed", "Approved", "Needs Changes", "Rejected"],
                        required=True,
                    ),
                },
                key="proposal_editor",
            )
            st.session_state["proposal"] = edited_proposal.to_dict("records")
            st.download_button(
                "Download proposal work queue",
                edited_proposal.to_csv(index=False).encode("utf-8"),
                "proposal_work_queue.csv",
                "text/csv",
                width="content",
                icon=":material/download:",
            )
        else:
            st.info("Run capability analysis to create the requirement-to-response queue.")
        if st.session_state["questions"]:
            st.subheader("Clarification questions")
            st.dataframe(pd.DataFrame(st.session_state["questions"]), width="stretch", hide_index=True, alt="Draft clarification questions")

    if user_role == "Admin" and len(tab_objects) > 5:
        with tab_objects[5]:
            st.subheader("Admin & Portfolio Analytics")
            st.caption("Cross-opportunity tracking and organizational performance metrics.")
            saved_all = list_opportunities()
            if saved_all:
                port_df = pd.DataFrame(saved_all)
                ac1, ac2, ac3, ac4 = st.columns(4)
                ac1.metric("Total Opportunities", len(port_df))
                won_n = sum(port_df["stage"] == "Won")
                lost_n = sum(port_df["stage"] == "Lost")
                win_pct = f"{(won_n / (won_n + lost_n) * 100):.1f}%" if (won_n + lost_n) > 0 else "N/A"
                ac2.metric("Won Opportunities", won_n)
                ac3.metric("Lost Opportunities", lost_n)
                ac4.metric("Win Rate", win_pct)

                sc1, sc2 = st.columns(2)
                with sc1:
                    st.subheader("Opportunities by Stage")
                    stage_s = port_df["stage"].value_counts().rename_axis("Stage").reset_index(name="Count")
                    st.bar_chart(stage_s, x="Stage", y="Count")
                with sc2:
                    st.subheader("Decisions Summary")
                    dec_s = port_df["human_decision"].value_counts().rename_axis("Decision").reset_index(name="Count")
                    st.bar_chart(dec_s, x="Decision", y="Count")
            else:
                st.info("No saved opportunities recorded in the portfolio yet.")
