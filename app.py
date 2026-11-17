"""RFP Intelligence — professional monochrome procurement workspace.

The presentation layer is redesigned; the existing extraction, analysis,
storage and human-approval functions remain backed by the modules package.
"""
import os
import tempfile
import html
import pandas as pd
import streamlit as st

from modules.pdf_processor import extract_pdf_text
from modules.requirement_extractor import extract_requirements
from modules.spreadsheet_processor import extract_spreadsheet_text
from modules.opportunity_storage import initialise_database, list_opportunities, load_opportunity, save_opportunity
from modules.rfp_analysis import (
    DEFAULT_CAPABILITIES, bid_recommendation, clarification_questions,
    identify_risks, match_requirements, parse_capabilities, proposal_mapping,
)

st.set_page_config(page_title="RFP Intelligence", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

st.markdown(r"""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--ink:#171717;--muted:#6b7280;--line:#dedede;--soft:#f6f6f6;--white:#fff;--black:#111}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{background:#f3f4f5!important;color:var(--ink)!important;font-family:Inter,Arial,sans-serif!important}
[data-testid="stHeader"]{background:rgba(255,255,255,.96)!important;border-bottom:1px solid #e7e7e7}
[data-testid="stMain"]{background:#f3f4f5!important}
[data-testid="stMainBlockContainer"],.main .block-container{max-width:1600px!important;padding:1.35rem 1.65rem 3rem!important}

/* Sidebar */
[data-testid="stSidebar"]{background:#151515!important;border-right:1px solid #303030!important}
[data-testid="stSidebar"]>div:first-child{background:transparent!important}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
[data-testid="stSidebar"] .stMarkdown,[data-testid="stSidebar"] .stMarkdown *,
[data-testid="stSidebar"] .stCaption,[data-testid="stSidebar"] .stCaption *,
[data-testid="stSidebar"] .stSubheader,[data-testid="stSidebar"] .stSubheader *{color:#f5f5f5!important}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{font-weight:650!important}

/* Sidebar action buttons */
[data-testid="stSidebar"] .stButton button,
[data-testid="stSidebar"] .stDownloadButton button{
 background:#f4f4f4!important;color:#111!important;border:1px solid #d0d0d0!important;
 border-radius:8px!important;font-weight:650!important;min-height:2.35rem!important;opacity:1!important
}
[data-testid="stSidebar"] .stButton button *,
[data-testid="stSidebar"] .stDownloadButton button *{color:#111!important;-webkit-text-fill-color:#111!important;fill:#111!important}
[data-testid="stSidebar"] .stButton button:hover,
[data-testid="stSidebar"] .stDownloadButton button:hover{background:#dedede!important;border-color:#bdbdbd!important}
[data-testid="stSidebar"] .stButton button:disabled,
[data-testid="stSidebar"] .stDownloadButton button:disabled{background:#3a3a3a!important;border-color:#555!important;color:#bdbdbd!important;opacity:1!important}
[data-testid="stSidebar"] .stButton button:disabled *,
[data-testid="stSidebar"] .stDownloadButton button:disabled *{color:#bdbdbd!important;-webkit-text-fill-color:#bdbdbd!important}

/* Upload area and uploaded file row */
[data-testid="stSidebar"] [data-testid="stFileUploader"],
[data-testid="stSidebar"] [data-testid="stFileUploader"] section{background:#202020!important;color:#f5f5f5!important;border-radius:10px!important}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section{border:1px dashed #888!important}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section *,
[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
[data-testid="stSidebar"] [data-testid="stFileUploader"] p,
[data-testid="stSidebar"] [data-testid="stFileUploader"] span{color:#f5f5f5!important;-webkit-text-fill-color:#f5f5f5!important}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button{background:#f4f4f4!important;color:#111!important;border:1px solid #d0d0d0!important;border-radius:8px!important}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button *,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button p,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button span{color:#111!important;-webkit-text-fill-color:#111!important;fill:#111!important}
[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] *{
 background:#f4f4f4!important;color:#171717!important;-webkit-text-fill-color:#171717!important
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button,
[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button *{
 color:#171717!important;-webkit-text-fill-color:#171717!important;fill:#171717!important
}

/* Selectbox value and dropdown menu */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div{
 background:#f4f4f4!important;border:1px solid #cfcfcf!important;border-radius:8px!important
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="value"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="value"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] input{
 color:#111!important;-webkit-text-fill-color:#111!important;opacity:1!important
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] svg{color:#111!important;fill:#111!important}
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] *,
[data-baseweb="menu"] [role="option"],
[data-baseweb="menu"] [role="option"] *{color:#171717!important;-webkit-text-fill-color:#171717!important}
[data-baseweb="popover"] [role="option"]{background:#fff!important}
[data-baseweb="popover"] [role="option"][aria-selected="true"]{background:#ededed!important}

/* Sidebar text area, radios and expanders */
[data-testid="stSidebar"] [data-testid="stTextArea"] textarea{
 background:#242424!important;color:#fff!important;-webkit-text-fill-color:#fff!important;border:1px solid #666!important;border-radius:8px!important
}
[data-testid="stSidebar"] [data-testid="stTextArea"] textarea::placeholder{color:#bdbdbd!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label{color:#f5f5f5!important;padding:.48rem .62rem;border-radius:8px;border:1px solid transparent}
[data-testid="stSidebar"] [data-testid="stRadio"] label *{color:#f5f5f5!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:#292929;border-color:#444}
[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"]{background:#303030;border-color:#777}
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] summary *{color:#f5f5f5!important}

/* Existing monochrome dashboard layout */
.rfp-topbar{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:.35rem .25rem 1rem;border-bottom:1px solid #dedede;margin-bottom:1.15rem}
.rfp-brand{font-size:1.2rem;font-weight:800;letter-spacing:-.035em;color:#111}
.rfp-brand span{color:#555}
.rfp-topmeta{font-size:.8rem;color:#737373;letter-spacing:.01em}
.rfp-hero{position:relative;overflow:hidden;border:1px solid #dedede;border-radius:15px;padding:1.45rem 1.6rem;margin:.25rem 0 1rem;background:#fff;box-shadow:0 4px 16px rgba(0,0,0,.035)}
.rfp-hero:before{content:"";position:absolute;right:0;top:0;width:7px;height:100%;background:#171717}
.rfp-hero h1{position:relative;color:#111!important;font-size:clamp(1.8rem,3vw,2.35rem)!important;font-weight:800!important;letter-spacing:-.045em!important;margin:0 0 .3rem!important}
.rfp-hero h1 span{color:#555}
.rfp-hero p{position:relative;color:#6b7280!important;margin:.15rem 0 0;font-size:.95rem}
.rfp-stage-pill{position:absolute;right:1.4rem;top:1.15rem;z-index:2;border:1px solid #d8d8d8;border-radius:10px;padding:.6rem .85rem;background:#f7f7f7;color:#222;font-weight:700;min-width:145px}
.rfp-workflow{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;position:relative;background:#fff;border:1px solid #dedede;border-radius:14px;padding:1rem 1.15rem .85rem;margin:1.05rem 0 1.35rem;box-shadow:0 4px 14px rgba(0,0,0,.025)}
.rfp-step{display:flex;gap:10px;align-items:flex-start;min-width:0}
.rfp-stepnum{flex:0 0 34px;height:34px;border-radius:50%;display:grid;place-items:center;font-weight:800;font-size:.95rem;background:#ededed;border:1px solid #d5d5d5;color:#222}
.rfp-stepnum.done{background:#171717;border-color:#171717;color:#fff}
.rfp-step strong{display:block;color:#171717;font-size:.86rem;margin:.1rem 0 .25rem}
.rfp-step small{color:#777;font-size:.74rem}
.rfp-flowbar{grid-column:1/-1;height:6px;border-radius:20px;background:#e8e8e8;overflow:hidden;margin:.15rem .15rem 0}
.rfp-flowbar span{display:block;height:100%;border-radius:20px;background:#171717;transition:width .35s ease}
.rfp-section-title{font-size:1.2rem;font-weight:800;color:#171717;margin:.65rem 0 .8rem;letter-spacing:-.025em}
.rfp-kpis{display:grid;grid-template-columns:repeat(5,minmax(115px,1fr)) minmax(220px,1.55fr);gap:12px;margin-bottom:.7rem}
.rfp-kpi{position:relative;overflow:hidden;min-height:112px;padding:.95rem 1rem;border-radius:12px;color:#171717;border:1px solid #dedede;border-top:3px solid #171717;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.035);transition:transform .18s ease,box-shadow .18s ease;animation:fadein .3s ease both}
.rfp-kpi:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,0,0,.07)}
.rfp-kpi .ico{font-size:1.1rem;margin-bottom:.35rem;color:#555}
.rfp-kpi .lab{font-size:.76rem;color:#666;font-weight:650}
.rfp-kpi .val{font-size:1.85rem;line-height:1.2;font-weight:800;color:#111;margin-top:.2rem;letter-spacing:-.04em}
.rfp-kpi.decision .val{font-size:1.18rem;letter-spacing:-.02em;margin-top:.55rem}
.rfp-kpi.cyan,.rfp-kpi.purple,.rfp-kpi.amber,.rfp-kpi.green,.rfp-kpi.pink,.rfp-kpi.teal{--a:#fff;--b:#fff;--edge:#171717;--glow:rgba(0,0,0,.04)}
.rfp-panel{border-radius:14px;padding:1.15rem 1.25rem;border:1px solid #dcdcdc;border-left:4px solid #222;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.025);margin-bottom:1rem}
.rfp-panel h3{color:#171717!important;font-size:1.08rem!important;font-weight:800!important;margin:0 0 .8rem!important}
.rfp-panel p,.rfp-panel li{color:#333;line-height:1.55}
.rfp-panel .muted{color:#777;font-size:.85rem}
.rfp-panel.pinkpanel{border-left-color:#171717;background:#fff}
.rfp-panel.bluepanel{border-left-color:#555;background:#fff;min-height:155px}
.rfp-verdict{display:inline-block;background:#ededed;border:1px solid #d5d5d5;color:#171717;padding:.25rem .6rem;border-radius:30px;font-size:.72rem;font-weight:800;vertical-align:middle}
.rfp-score{font-size:2.5rem;font-weight:800;letter-spacing:-.05em;color:#111;margin:.4rem 0}
.rfp-scorebar{height:10px;border-radius:20px;background:#e8e8e8;overflow:hidden;margin:.8rem 0}
.rfp-scorebar span{display:block;height:100%;background:#171717;border-radius:20px}
.rfp-risk{border-left-color:#555}.rfp-strength{border-left-color:#999}
.rfp-two-col{display:grid;grid-template-columns:1fr 1fr;gap:14px}
[data-testid="stMetric"]{background:#fff;border:1px solid #ddd;border-radius:12px;padding:.8rem!important}
[data-testid="stMetricLabel"],[data-testid="stMetricLabel"] p,[data-testid="stMetricValue"],[data-testid="stMetricValue"] div{color:#171717!important}
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff!important;border:1px solid #ddd!important;border-radius:13px!important;box-shadow:0 4px 14px rgba(0,0,0,.025)!important}

/* Main buttons and form widgets */
.stButton button,.stDownloadButton button{border-radius:8px!important;border:1px solid #171717!important;background:#171717!important;color:#fff!important;font-weight:650!important;transition:all .18s ease!important}
.stButton button *, .stDownloadButton button *{color:#fff!important;-webkit-text-fill-color:#fff!important}
.stButton button:hover,.stDownloadButton button:hover{background:#3b3b3b!important;border-color:#3b3b3b!important;transform:translateY(-1px)}
.stButton button:disabled,.stDownloadButton button:disabled{background:#e5e5e5!important;border-color:#d0d0d0!important;color:#777!important;opacity:1!important}
.stButton button:disabled *,.stDownloadButton button:disabled *{color:#777!important;-webkit-text-fill-color:#777!important}
.stTextInput input,.stTextArea textarea,[data-testid="stSelectbox"] [data-baseweb="select"] > div,[data-testid="stMultiSelect"] [data-baseweb="select"] > div{background:#fff!important;color:#171717!important;-webkit-text-fill-color:#171717!important;border:1px solid #d0d0d0!important;border-radius:8px!important}
[data-testid="stSelectbox"] [data-baseweb="select"] *,[data-testid="stMultiSelect"] [data-baseweb="select"] *,[data-testid="stSelectbox"] input,[data-testid="stMultiSelect"] input{color:#171717!important;-webkit-text-fill-color:#171717!important;opacity:1!important}
[data-testid="stSelectbox"] svg,[data-testid="stMultiSelect"] svg{fill:#171717!important;color:#171717!important}
.stTextInput input::placeholder,.stTextArea textarea::placeholder{color:#888!important;-webkit-text-fill-color:#888!important}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border:1px solid #ddd;border-radius:10px;overflow:hidden}
[data-testid="stAlert"]{border-radius:10px!important}
[data-testid="stCaptionContainer"] p{color:#777!important}
hr{border-color:#e2e2e2!important}
@keyframes fadein{from{opacity:.75;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:1050px){.rfp-kpis{grid-template-columns:repeat(3,1fr)}.rfp-workflow{grid-template-columns:repeat(2,1fr)}}
@media(max-width:650px){[data-testid="stMainBlockContainer"],.main .block-container{padding:.65rem .65rem 2rem!important}.rfp-kpis{grid-template-columns:repeat(2,1fr)}.rfp-two-col{grid-template-columns:1fr}.rfp-stage-pill{position:relative;right:auto;top:auto;margin-top:.8rem;display:inline-block}.rfp-workflow{grid-template-columns:1fr}.rfp-topbar{flex-wrap:wrap}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}

</style>
""", unsafe_allow_html=True)


def init_state():
    defaults={"pages":[],"requirements":[],"matches":[],"risks":[],"questions":[],"proposal":[],"recommendation":{},"file_name":"","opportunity_stage":"New","human_decision":"Pending human review","decision_notes":"","opportunity_id":None}
    for k,v in defaults.items(): st.session_state.setdefault(k,v)


def process_upload(uploaded_file):
    temp_path=None
    try:
        suffix=os.path.splitext(uploaded_file.name)[1].casefold()
        with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as f:
            f.write(uploaded_file.getvalue()); temp_path=f.name
        if suffix==".pdf": pages=extract_pdf_text(temp_path)
        elif suffix in {".xls",".xlsx",".xlx"}: pages=extract_spreadsheet_text(temp_path)
        else: raise ValueError("Supported formats are PDF, XLS and XLSX")
        reqs=extract_requirements(pages)
        st.session_state.update({"pages":pages,"requirements":reqs,"matches":[],"risks":[],"questions":[],"proposal":[],"recommendation":{},"file_name":uploaded_file.name,"opportunity_stage":"Analysis","opportunity_id":None,"human_decision":"Pending human review","decision_notes":""})
        st.success(f"Processed {uploaded_file.name}: {len(pages)} pages / worksheets and {len(reqs)} requirements found.")
    except Exception as e: st.error(f"Document processing failed: {e}")
    finally:
        if temp_path and os.path.exists(temp_path): os.remove(temp_path)


def run_analysis(capability_text):
    reqs=st.session_state.get("requirements",[])
    matches=match_requirements(reqs,capability_text); risks=identify_risks(matches)
    st.session_state.update({"matches":matches,"risks":risks,"questions":clarification_questions(matches),"proposal":proposal_mapping(matches),"recommendation":bid_recommendation(matches,risks),"opportunity_stage":"Review"})
    st.success("Capability comparison and decision-support analysis updated.")


def save_current():
    if not st.session_state.get("file_name"): st.warning("Process an RFP before saving."); return
    payload={k:st.session_state[k] for k in ("pages","requirements","matches","risks","questions","proposal","recommendation","file_name","opportunity_stage","human_decision","decision_notes")}
    oid=save_opportunity(payload,st.session_state.get("opportunity_id")); st.session_state["opportunity_id"]=oid; st.success(f"Opportunity saved as #{oid}.")


def load_saved(oid):
    payload=load_opportunity(oid)
    if not payload: st.error("Saved opportunity could not be loaded."); return
    for k,v in payload.items():
        if k in st.session_state: st.session_state[k]=v
        elif k in ("pages","requirements","matches","risks","questions","proposal","recommendation","file_name","opportunity_stage","human_decision","decision_notes","opportunity_id"): st.session_state[k]=v
    for k in ("requirements_editor","proposal_editor"): st.session_state.pop(k,None)
    st.rerun()


def safe(v): return html.escape(str(v if v is not None else ""))


def metric_card(icon,label,value,colour,decision=False):
    cls=f"rfp-kpi {colour}"+(" decision" if decision else "")
    return f'<div class="{cls}"><div class="ico">{icon}</div><div class="lab">{safe(label)}</div><div class="val">{safe(value)}</div></div>'


def main():
    init_state(); initialise_database()
    # Simple, always-visible workflow controls: upload -> review -> capability analysis.
    with st.sidebar:
        st.markdown("<div style='font-size:1.08rem;font-weight:800;letter-spacing:-.035em;margin:.25rem 0 1rem;color:#fff'>RFP INTELLIGENCE</div>",unsafe_allow_html=True)
        nav=st.radio("WORKSPACE",["⌂  Dashboard","▤  Requirements","◈  Capability Match","⚠  Risk Analysis","◎  Decision Centre","▣  Proposal Support","▦  Opportunities"],label_visibility="collapsed",key="main_navigation")
        st.markdown("<div style='height:1px;background:#444;margin:1rem 0'></div>",unsafe_allow_html=True)

        st.subheader("1. Opportunity intake")
        up=st.file_uploader("Upload RFP / tender document",type=["pdf","xls","xlsx","xlx"],key="rfp_upload")
        if up and st.button("Process document",type="primary",use_container_width=True): process_upload(up)

        st.markdown("<div style='height:1px;background:#444;margin:1.1rem 0'></div>",unsafe_allow_html=True)
        st.subheader("2. Company capability profile")
        cap=st.text_area("One capability per line",value="\n".join(DEFAULT_CAPABILITIES),height=155,key="capability_profile",help="Edit this profile to reflect the capabilities relevant to the current tender.")
        if st.button("Run capability analysis",use_container_width=True,disabled=not bool(st.session_state["requirements"])): run_analysis(cap)

        st.markdown("<div style='height:1px;background:#444;margin:1.1rem 0'></div>",unsafe_allow_html=True)
        stage_options=["New","Analysis","Review","Bid Decision","Proposal","Submitted","Won","Lost"]
        stage=st.selectbox("Opportunity stage",stage_options,index=stage_options.index(st.session_state["opportunity_stage"]) if st.session_state["opportunity_stage"] in stage_options else 0)
        st.session_state["opportunity_stage"]=stage
        st.caption(f"Human decision: **{st.session_state['human_decision']}**")

        with st.expander("Saved opportunities",expanded=False):
            saved=list_opportunities(); labels=["Create new / current opportunity"]+[f"#{x['id']} · {x['file_name']} · {x['stage']}" for x in saved]
            selected=st.selectbox("Load opportunity",labels)
            if st.button("Load selected",use_container_width=True,disabled=selected==labels[0]): load_saved(int(saved[labels.index(selected)-1]["id"]))
            if st.button("Save current opportunity",use_container_width=True,disabled=not bool(st.session_state["file_name"])): save_current()
            if st.button("Clear current opportunity",use_container_width=True):
                for k in ("pages","requirements","matches","risks","questions","proposal"): st.session_state[k]=[]
                st.session_state.update({"recommendation":{},"file_name":"","opportunity_stage":"New","human_decision":"Pending human review","decision_notes":"","opportunity_id":None}); st.rerun()

    reqs=st.session_state["requirements"]; matches=st.session_state["matches"]; risks=st.session_state["risks"]; rec=st.session_state["recommendation"]
    stage=st.session_state["opportunity_stage"]
    st.markdown(f"<div class='rfp-topbar'><div class='rfp-brand'>RFP <span>Intelligence</span></div><div class='rfp-topmeta'>Procurement Intelligence Workspace</div><div class='rfp-topmeta'>◉  Evidence-led · Human-approved</div></div>",unsafe_allow_html=True)
    st.markdown(f"<div class='rfp-hero'><div class='rfp-stage-pill'>▣ &nbsp; Current Stage<br><span style='font-size:1.05rem'>{safe(stage)}</span></div><h1>RFP Intelligence</h1><p>AI-assisted tender analysis for evidence-led, human-approved decisions.</p></div>",unsafe_allow_html=True)
    progress={"New":.15,"Analysis":.4,"Review":.7,"Bid Decision":.82,"Proposal":.92,"Submitted":1,"Won":1,"Lost":1}.get(stage,.15)
    step_html=''.join([f"<div class='rfp-step'><div class='rfp-stepnum {'done' if i==0 and reqs else ''}'>{'✓' if i==0 and reqs else i+1}</div><div><strong>{t}</strong><small>{d}</small></div></div>" for i,(t,d) in enumerate([("Review requirements","Confirm type, deadline and source."),("Check capability match","Validate matches and gaps."),("Review risks","Assign actions for open risks."),("Make human decision","Choose Bid, No-Bid, or Hold.")])])
    st.markdown(f"<div class='rfp-workflow'>{step_html}<div class='rfp-flowbar'><span style='width:{int(progress*100)}%'></span></div></div>",unsafe_allow_html=True)

    mandatory=sum(x.get("Type")=="Mandatory" for x in reqs); deadlines=sum(bool(x.get("Deadline")) for x in reqs)
    kpis=[metric_card("▤","RFP Pages",len(st.session_state["pages"]),"cyan"),metric_card("▱","Requirements",len(reqs),"purple"),metric_card("⬡","Mandatory",mandatory,"amber"),metric_card("▣","Deadlines Identified",deadlines,"green"),metric_card("⚠","Open Risks",len(risks),"pink"),metric_card("⌁","Human Decision",st.session_state["human_decision"],"teal",True)]
    st.markdown("<div class='rfp-section-title'>Opportunity dashboard</div><div class='rfp-kpis'>"+''.join(kpis)+"</div>",unsafe_allow_html=True)
    st.caption(f"Opportunity: {st.session_state['file_name'] or 'No document uploaded'}  |  Stage: {stage}  |  {'Saved #' + str(st.session_state['opportunity_id']) if st.session_state.get('opportunity_id') else 'Unsaved opportunity'}")

    # Dashboard landing view follows the supplied image composition.
    if nav.startswith("⌂"):
        if not reqs:
            st.info("Upload an RFP or tender document from the left navigation to begin.")
        else:
            if not rec:
                st.info("Run capability analysis from the left navigation to generate Bid / No-Bid intelligence.")
            else:
                score=rec.get("Score",0); signal=rec.get("Signal",""); mg=rec.get("Mandatory Gaps",0); mt=rec.get("Mandatory Requirements",0); hr=rec.get("High Risks",0); verify=rec.get("Items to Verify",0)
                met=mt-mg
                verdict="RECOMMENDATION: NO-BID" if ("No-Bid" in signal or score<70 or mg>0) else "RECOMMENDATION: BID"
                col1,col2=st.columns([1.2,1])
                with col1:
                    st.markdown(f"<div class='rfp-panel pinkpanel'><h3>◎ &nbsp; AI Bid Intelligence <span class='rfp-verdict'>{safe(verdict)}</span></h3><div style='display:grid;grid-template-columns:1fr 1fr;gap:1rem'><div><div class='rfp-score'>{score} / 100</div><div>Feasibility Score</div><div class='rfp-scorebar'><span style='width:{max(0,min(100,score))}%'></span></div><div class='muted'>Evidence-based feasibility estimate</div></div><div style='border-left:1px solid #dedede;padding-left:1.1rem'><div style='margin:.35rem 0'>▱ &nbsp; <b>{met} / {mt} Met</b><br><span class='muted'>Mandatory Compliance</span></div><div style='margin:.65rem 0'>⚠ &nbsp; <b>{hr} Risks</b><br><span class='muted'>High-Severity Risks</span></div><div style='margin:.65rem 0'>▤ &nbsp; <b>{verify} Items</b><br><span class='muted'>Clarifications Needed</span></div></div></div></div>",unsafe_allow_html=True)
                with col2:
                    category_counts=pd.Series([m.get("Category","Other") for m in matches]).value_counts().head(5)
                    st.markdown("<div class='rfp-panel bluepanel'><h3>▥ &nbsp; Requirements by Category</h3><div class='muted'>Extracted requirement distribution</div></div>",unsafe_allow_html=True)
                    if not category_counts.empty: st.bar_chart(category_counts, height=190, color="#171717")
                gaps=[m for m in matches if m.get("Type")=="Mandatory" and m.get("Match Status")=="Gap"]
                strengths=[m for m in matches if m.get("Match Status")=="Match"]
                a,b=st.columns(2)
                with a:
                    items="".join([f"<li>🔴 {safe(x.get('Requirement',''))[:230]}</li>" for x in gaps[:3]]) or "<li>No mandatory capability gaps identified.</li>"
                    st.markdown(f"<div class='rfp-panel rfp-risk'><h3>⚠ &nbsp; Fatal Deal-Breakers (Why No-Bid?)</h3><ul>{items}</ul></div>",unsafe_allow_html=True)
                with b:
                    items="".join([f"<li>🟢 {safe(x.get('Requirement',''))[:230]}</li>" for x in strengths[:3]]) or "<li>No full capability matches found for the current profile.</li>"
                    st.markdown(f"<div class='rfp-panel rfp-strength'><h3>✓ &nbsp; Company Strengths (Why Bid?)</h3><ul>{items}</ul></div>",unsafe_allow_html=True)
                with st.expander("Record human Bid / No-Bid decision",expanded=True):
                    decision=st.radio("Final decision",["Pending human review","Bid","No-Bid","Hold for clarification"],index=["Pending human review","Bid","No-Bid","Hold for clarification"].index(st.session_state["human_decision"]),horizontal=True,key="human_decision_radio")
                    st.session_state["human_decision"]=decision
                    st.session_state["decision_notes"]=st.text_input("Decision justification / reviewer notes",value=st.session_state.get("decision_notes",""),key="decision_notes_text")
                    st.caption("AI recommendation is advisory. The final decision must be recorded by an authorised human reviewer.")
    elif nav.startswith("▤"):
        st.subheader("Extracted requirements")
        if reqs:
            df=pd.DataFrame(reqs); edited=st.data_editor(df,use_container_width=True,hide_index=True,num_rows="dynamic",disabled=["Source Page"] if "Source Page" in df.columns else [],column_config={"Type":st.column_config.SelectboxColumn("Requirement type",options=["Mandatory","Optional","Needs Verification"]),"Review Status":st.column_config.SelectboxColumn("Review status",options=["Pending Review","Verified","Needs Clarification","Rejected"]),"Reviewer Notes":st.column_config.TextColumn("Reviewer notes",width="large")},key="requirements_editor")
            st.session_state["requirements"]=edited.to_dict("records")
            st.download_button("Download requirements CSV",edited.to_csv(index=False).encode(),"rfp_requirements.csv","text/csv")
            with st.expander("Source document text"):
                for p in st.session_state["pages"]: st.markdown(f"**Page / Sheet {p.get('page','')}**"); st.text(p.get("text",""))
        else: st.info("Upload and process an RFP to view extracted requirements.")
    elif nav.startswith("◈"):
        st.subheader("Requirement-to-capability comparison")
        if matches: st.dataframe(pd.DataFrame(matches),use_container_width=True,hide_index=True,column_config={"Match Score":st.column_config.ProgressColumn("Match score",min_value=0,max_value=100,format="%d%%")})
        else: st.info("Run capability analysis to create the requirement-to-response comparison.")
    elif nav.startswith("⚠"):
        st.subheader("Risk Register & Contractual Exposure")
        if risks:
            high=sum(x.get("Risk Level")=="High" for x in risks); med=sum(x.get("Risk Level")=="Medium" for x in risks)
            c1,c2,c3=st.columns(3); c1.metric("Total Open Risks",len(risks)); c2.metric("High-Severity Risks",high); c3.metric("Medium-Severity Risks",med)
            level=st.radio("Filter by risk level",["All","High","Medium"],horizontal=True); shown=[x for x in risks if level=="All" or x.get("Risk Level")==level]
            st.dataframe(pd.DataFrame(shown),use_container_width=True,hide_index=True)
            st.download_button("Download full risk register CSV",pd.DataFrame(risks).to_csv(index=False).encode(),"rfp_risk_register.csv","text/csv")
        else: st.info("Run capability analysis to generate the risk register.")
        if st.session_state["questions"]:
            st.subheader("Pre-Bid Clarification Queue"); st.dataframe(pd.DataFrame(st.session_state["questions"]),use_container_width=True,hide_index=True)
            st.download_button("Download clarification questions CSV",pd.DataFrame(st.session_state["questions"]).to_csv(index=False).encode(),"clarification_questions.csv","text/csv")
    elif nav.startswith("◎"):
        st.subheader("Human Decision Centre")
        st.info("AI analysis supports the reviewer; it does not make the final business decision.")
        decision=st.radio("Record final decision",["Pending human review","Bid","No-Bid","Hold for clarification"],index=["Pending human review","Bid","No-Bid","Hold for clarification"].index(st.session_state["human_decision"]),horizontal=True,key="decision_page_radio")
        st.session_state["human_decision"]=decision
        st.session_state["decision_notes"]=st.text_area("Decision justification / reviewer notes",value=st.session_state.get("decision_notes",""),key="decision_page_notes")
        if decision=="Bid": st.success("Bid selected. Proposal support is unlocked.")
        elif decision=="No-Bid": st.error("No-Bid selected. Opportunity marked as declined.")
        else: st.warning("Decision is awaiting final review.")
    elif nav.startswith("▣"):
        st.subheader("Proposal preparation work queue")
        if st.session_state["human_decision"]!="Bid": st.warning("Proposal preparation is locked until the human decision is Bid.")
        elif st.session_state["proposal"]:
            df=pd.DataFrame(st.session_state["proposal"]); edited=st.data_editor(df,use_container_width=True,hide_index=True,num_rows="dynamic",key="proposal_editor"); st.session_state["proposal"]=edited.to_dict("records")
            st.download_button("Download proposal work queue",edited.to_csv(index=False).encode(),"proposal_work_queue.csv","text/csv")
        else: st.info("Run capability analysis to create the requirement-to-response queue.")
        if st.session_state["questions"]: st.subheader("Clarification questions"); st.dataframe(pd.DataFrame(st.session_state["questions"]),use_container_width=True,hide_index=True)
    elif nav.startswith("▦"):
        st.subheader("Opportunity portfolio")
        saved=list_opportunities()
        if saved:
            df=pd.DataFrame(saved).rename(columns={"id":"Opportunity ID","file_name":"RFP file","stage":"Stage","human_decision":"Human decision","updated_at":"Last updated"})
            st.dataframe(df,use_container_width=True,hide_index=True)
        else: st.info("No saved opportunities yet. Process and save an RFP to populate the portfolio.")

if __name__=="__main__": main()
