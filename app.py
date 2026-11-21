"""RFP Intelligence — professional monochrome procurement workspace.

The presentation layer is redesigned; the existing extraction, analysis,
storage and human-approval functions remain backed by the modules package.
"""
import os
import io
import tempfile
import html
from datetime import datetime
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
:root{
 --ink:#172033;--muted:#738096;--line:rgba(126,145,171,.24);
 --glass:rgba(255,255,255,.70);--glass-strong:rgba(255,255,255,.86);
 --navy:#111827;--blue:#3478f6;--cyan:#26b9c8;--violet:#8b70df;
 --green:#16834b;--amber:#b97813;--red:#c13b42;
}
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"]{
 background:
  radial-gradient(ellipse at 8% 8%,rgba(80,145,235,.22),transparent 38%),
  radial-gradient(ellipse at 92% 24%,rgba(76,198,210,.20),transparent 36%),
  radial-gradient(ellipse at 72% 92%,rgba(145,125,225,.13),transparent 38%),
  linear-gradient(135deg,#e8eef7 0%,#f3f6fa 46%,#e3eff2 100%)!important;
 color:var(--ink)!important;font-family:Inter,Arial,sans-serif!important;
}
[data-testid="stHeader"]{background:rgba(247,249,252,.78)!important;backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}
[data-testid="stMain"],[data-testid="stMainBlockContainer"]{background:transparent!important}
[data-testid="stMainBlockContainer"],.main .block-container{max-width:1700px!important;padding:1.2rem 1.5rem 3rem!important}

/* Dark navigation rail — high contrast controls */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#151b27 0%,#101722 100%)!important;border-right:1px solid rgba(255,255,255,.10)!important}
[data-testid="stSidebar"]>div:first-child{background:transparent!important}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
[data-testid="stSidebar"] .stMarkdown,[data-testid="stSidebar"] .stMarkdown *,
[data-testid="stSidebar"] .stCaption,[data-testid="stSidebar"] .stCaption *,
[data-testid="stSidebar"] .stSubheader,[data-testid="stSidebar"] .stSubheader *{
 color:#f3f6fb!important;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{font-weight:650!important}
[data-testid="stSidebar"] .stButton button,[data-testid="stSidebar"] .stDownloadButton button{
 background:#f5f7fb!important;color:#151b27!important;border:1px solid #d5dce7!important;
 border-radius:9px!important;font-weight:700!important;min-height:2.45rem!important;opacity:1!important;
}
[data-testid="stSidebar"] .stButton button *,
[data-testid="stSidebar"] .stDownloadButton button *{
 color:#151b27!important;-webkit-text-fill-color:#151b27!important;fill:#151b27!important;
}
[data-testid="stSidebar"] .stButton button:hover,[data-testid="stSidebar"] .stDownloadButton button:hover{
 background:#e5edf8!important;border-color:#a9bedb!important;transform:translateY(-1px)
}
[data-testid="stSidebar"] .stButton button:disabled,[data-testid="stSidebar"] .stDownloadButton button:disabled{
 background:#3b4555!important;border-color:#536075!important;color:#c5ceda!important;opacity:1!important
}
[data-testid="stSidebar"] .stButton button:disabled *,[data-testid="stSidebar"] .stDownloadButton button:disabled *{
 color:#c5ceda!important;-webkit-text-fill-color:#c5ceda!important
}
[data-testid="stSidebar"] [data-testid="stFileUploader"],
[data-testid="stSidebar"] [data-testid="stFileUploader"] section{
 background:rgba(255,255,255,.07)!important;color:#f5f7fb!important;border-radius:12px!important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section{border:1px dashed rgba(205,220,244,.52)!important}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section *,
[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
[data-testid="stSidebar"] [data-testid="stFileUploader"] p,
[data-testid="stSidebar"] [data-testid="stFileUploader"] span{
 color:#f5f7fb!important;-webkit-text-fill-color:#f5f7fb!important
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button{
 background:#f5f7fb!important;color:#151b27!important;border:1px solid #d5dce7!important;border-radius:8px!important
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button *,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button p,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button span{
 color:#151b27!important;-webkit-text-fill-color:#151b27!important;fill:#151b27!important
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] *{
 background:#f5f7fb!important;color:#172033!important;-webkit-text-fill-color:#172033!important
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"]>div{
 background:#f5f7fb!important;border:1px solid #d4dce8!important;border-radius:9px!important
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="value"] *,
[data-testid="stSidebar"] [data-testid="stSelectbox"] input{
 color:#172033!important;-webkit-text-fill-color:#172033!important;opacity:1!important
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] svg{color:#172033!important;fill:#172033!important}
[data-baseweb="popover"] [role="listbox"],[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] *,[data-baseweb="menu"] [role="option"] *{
 color:#172033!important;-webkit-text-fill-color:#172033!important
}
[data-baseweb="popover"] [role="option"]{background:#fff!important}
[data-baseweb="popover"] [role="option"][aria-selected="true"]{background:#e9eff8!important}
[data-testid="stSidebar"] [data-testid="stTextArea"] textarea{
 background:rgba(255,255,255,.10)!important;color:#fff!important;-webkit-text-fill-color:#fff!important;
 border:1px solid rgba(220,232,250,.35)!important;border-radius:9px!important
}
[data-testid="stSidebar"] [data-testid="stTextArea"] textarea::placeholder{color:#c2ccda!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label{color:#f5f7fb!important;padding:.5rem .62rem;border-radius:9px;border:1px solid transparent}
[data-testid="stSidebar"] [data-testid="stRadio"] label *{color:#f5f7fb!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.12)}
[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"]{background:rgba(89,143,232,.22);border-color:rgba(123,169,239,.4)}
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] summary *{color:#f5f7fb!important}

/* Header, welcome panel and workflow */
.rfp-topbar{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:.35rem .25rem 1rem;border-bottom:1px solid var(--line);margin-bottom:1.05rem}
.rfp-brand{font-size:1.12rem;font-weight:800;letter-spacing:-.035em;color:#172033}
.rfp-brand span{color:#66758c}
.rfp-topmeta{font-size:.78rem;color:#738096;letter-spacing:.01em}
.rfp-hero{position:relative;overflow:hidden;border:1px solid rgba(255,255,255,.72);border-radius:22px;padding:1.7rem 1.85rem;margin:.25rem 0 1rem;
 background:linear-gradient(112deg,rgba(255,255,255,.48),rgba(255,255,255,.25) 58%,rgba(194,231,239,.34));
 backdrop-filter:blur(28px) saturate(155%);-webkit-backdrop-filter:blur(28px) saturate(155%);
 box-shadow:0 18px 48px rgba(40,59,88,.09),inset 0 1px 0 rgba(255,255,255,.82)}
.rfp-hero:after{content:"";position:absolute;inset:0;pointer-events:none;border-radius:inherit;background:linear-gradient(125deg,rgba(255,255,255,.28),transparent 38%,rgba(255,255,255,.07));}
.rfp-hero:before{content:"";position:absolute;right:-55px;top:-110px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(80,148,220,.16),transparent 68%)}
.rfp-hero h1{position:relative;color:#172033!important;font-size:clamp(1.8rem,3vw,2.35rem)!important;font-weight:800!important;letter-spacing:-.045em!important;margin:0 0 .3rem!important}
.rfp-hero p{position:relative;color:#6d7b90!important;margin:.15rem 0 0;font-size:.94rem}
.rfp-stage-pill{position:absolute;right:1.4rem;top:1.15rem;z-index:2;border:1px solid rgba(255,255,255,.72);border-radius:13px;padding:.7rem .95rem;background:rgba(255,255,255,.34);backdrop-filter:blur(22px) saturate(150%);-webkit-backdrop-filter:blur(22px) saturate(150%);color:#27364b;font-weight:700;min-width:145px;box-shadow:0 8px 24px rgba(45,64,94,.07),inset 0 1px 0 rgba(255,255,255,.75)}
.rfp-workflow{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;position:relative;background:rgba(255,255,255,.34);backdrop-filter:blur(26px) saturate(155%);-webkit-backdrop-filter:blur(26px) saturate(155%);border:1px solid rgba(255,255,255,.78);border-radius:19px;padding:1.05rem 1.2rem .9rem;margin:1.05rem 0 1.35rem;box-shadow:0 14px 36px rgba(40,59,88,.075),inset 0 1px 0 rgba(255,255,255,.82)}
.rfp-step{display:flex;gap:10px;align-items:flex-start;min-width:0}
.rfp-stepnum{flex:0 0 34px;height:34px;border-radius:50%;display:grid;place-items:center;font-weight:800;font-size:.95rem;background:rgba(238,242,248,.95);border:1px solid #d9e1ec;color:#26364d}
.rfp-stepnum.done{background:#172033;border-color:#172033;color:#fff}
.rfp-step strong{display:block;color:#1b2940;font-size:.86rem;margin:.1rem 0 .25rem}
.rfp-step small{color:#738096;font-size:.74rem}
.rfp-flowbar{grid-column:1/-1;height:7px;border-radius:20px;background:rgba(135,151,174,.18);overflow:hidden;margin:.15rem .15rem 0}
.rfp-flowbar span{display:block;height:100%;border-radius:20px;background:linear-gradient(90deg,#3478f6,#35b8c5,#8b70df);transition:width .45s ease}
.rfp-section-title{font-size:1.22rem;font-weight:800;color:#1b2940;margin:.65rem 0 .8rem;letter-spacing:-.025em}
.rfp-import-shell{position:relative;overflow:hidden;margin:3.2rem auto 0;max-width:1080px;min-height:430px;padding:3.2rem 3.4rem;border:1px solid rgba(255,255,255,.82);border-radius:26px;background:linear-gradient(125deg,rgba(255,255,255,.58),rgba(255,255,255,.28) 58%,rgba(193,226,235,.34));backdrop-filter:blur(30px) saturate(165%);-webkit-backdrop-filter:blur(30px) saturate(165%);box-shadow:0 24px 65px rgba(42,61,91,.10),inset 0 1px 0 rgba(255,255,255,.9)}
.rfp-import-shell:after{content:"";position:absolute;right:-95px;top:-145px;width:390px;height:390px;border-radius:50%;background:radial-gradient(circle,rgba(74,157,209,.18),transparent 68%);pointer-events:none}
.rfp-import-eyebrow{position:relative;z-index:1;color:#3478a8;font-size:.74rem;font-weight:800;letter-spacing:.14em}
.rfp-import-title{position:relative;z-index:1;margin:1rem 0 .65rem;color:#172033;font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-.055em}
.rfp-import-copy{position:relative;z-index:1;max-width:720px;color:#66758c;font-size:1rem;line-height:1.75}
.rfp-import-steps{position:relative;z-index:1;display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:2.4rem 0 1.8rem}
.rfp-import-steps>div{display:flex;flex-direction:column;gap:7px;min-height:112px;padding:1rem;border:1px solid rgba(255,255,255,.85);border-radius:15px;background:rgba(255,255,255,.35);backdrop-filter:blur(16px)}
.rfp-import-steps span{color:#3478f6;font-size:.76rem;font-weight:800;letter-spacing:.08em}
.rfp-import-steps b{color:#25344b;font-size:.9rem}
.rfp-import-steps small{color:#7b899d;font-size:.76rem}
.rfp-import-hint{position:relative;z-index:1;padding:1rem 1.1rem;border:1px solid rgba(52,120,246,.14);border-radius:12px;background:rgba(52,120,246,.07);color:#46617f;font-size:.86rem}
@media(max-width:700px){.rfp-import-shell{margin:1.3rem auto 0;padding:1.5rem;min-height:0}.rfp-import-steps{grid-template-columns:1fr;gap:9px}.rfp-import-steps>div{min-height:0}}

/* KPI cards — larger, soft glass with restrained color accents */
.rfp-kpis{display:grid;grid-template-columns:repeat(5,minmax(125px,1fr)) minmax(230px,1.65fr);gap:13px;margin-bottom:.7rem}
.rfp-kpi{position:relative;overflow:hidden;min-height:142px;padding:1.1rem 1.15rem;border-radius:18px;color:#172033;
 border:1px solid rgba(255,255,255,.76);border-top:3px solid var(--accent,#7c8ba2);
 background:linear-gradient(145deg,rgba(255,255,255,.46),rgba(255,255,255,.20));
 backdrop-filter:blur(27px) saturate(165%);-webkit-backdrop-filter:blur(27px) saturate(165%);
 box-shadow:0 14px 34px rgba(44,64,94,.075),inset 0 1px 0 rgba(255,255,255,.86);
 transition:transform .24s ease,box-shadow .24s ease,border-color .24s ease;animation:fadein .35s ease both}
.rfp-kpi:after{content:"";position:absolute;right:-30px;top:-42px;width:118px;height:118px;border-radius:50%;background:var(--wash,rgba(52,120,246,.12));filter:blur(1px);box-shadow:0 0 38px var(--wash,rgba(52,120,246,.12))}
.rfp-kpi:before{content:"";position:absolute;inset:0;pointer-events:none;border-radius:inherit;background:linear-gradient(135deg,rgba(255,255,255,.30),transparent 42%,rgba(255,255,255,.05));}
.rfp-kpi:hover{transform:translateY(-5px);border-color:rgba(255,255,255,.98);box-shadow:0 20px 42px rgba(44,64,94,.14),inset 0 1px 0 rgba(255,255,255,.95)}
.rfp-kpi .ico{font-size:1.22rem;margin-bottom:.42rem;color:var(--accent,#53647c);position:relative;z-index:1}
.rfp-kpi .lab{font-size:.78rem;color:#64748b;font-weight:700;position:relative;z-index:1}
.rfp-kpi .val{font-size:2.05rem;line-height:1.15;font-weight:800;color:#172033;margin-top:.25rem;letter-spacing:-.045em;position:relative;z-index:1}
.rfp-kpi.decision .val{font-size:1.25rem;letter-spacing:-.02em;margin-top:.62rem}
.rfp-kpi.cyan{--accent:#168fa7;--wash:rgba(38,185,200,.12)}
.rfp-kpi.purple{--accent:#7860c8;--wash:rgba(139,112,223,.12)}
.rfp-kpi.amber{--accent:#b97813;--wash:rgba(224,163,67,.13)}
.rfp-kpi.green{--accent:#16834b;--wash:rgba(36,168,104,.12)}
.rfp-kpi.pink{--accent:#c04c83;--wash:rgba(218,92,151,.12)}
.rfp-kpi.teal{--accent:#168fa7;--wash:rgba(38,185,200,.12)}

/* Glass panels, decision and recommendation */
.rfp-panel{border-radius:19px;padding:1.25rem 1.35rem;border:1px solid rgba(255,255,255,.78);border-left:4px solid #8a9ab0;
 background:linear-gradient(140deg,rgba(255,255,255,.43),rgba(255,255,255,.22));backdrop-filter:blur(27px) saturate(155%);-webkit-backdrop-filter:blur(27px) saturate(155%);
 box-shadow:0 15px 36px rgba(44,64,94,.075),inset 0 1px 0 rgba(255,255,255,.82);margin-bottom:1rem}
.rfp-panel h3{color:#1b2940!important;font-size:1.08rem!important;font-weight:800!important;margin:0 0 .8rem!important}
.rfp-panel p,.rfp-panel li{color:#344258;line-height:1.58}
.rfp-panel .muted{color:#78869a;font-size:.85rem}
.rfp-panel.pinkpanel{border-left-color:#8b70df;background:linear-gradient(135deg,rgba(255,255,255,.48),rgba(226,218,255,.27))}
.rfp-panel.bluepanel{border-left-color:#3478f6;background:rgba(255,255,255,.34);min-height:145px}
.rfp-verdict{display:inline-block;background:#edf0f4;border:1px solid #d7dee8;color:#29384d;padding:.27rem .65rem;border-radius:30px;font-size:.72rem;font-weight:800;vertical-align:middle}
.rfp-verdict.bid{background:#e7f6ec!important;border-color:#8bc99d!important;color:#137333!important}
.rfp-verdict.review{background:#fff3df!important;border-color:#e9bd72!important;color:#9a5b00!important}
.rfp-verdict.no-bid{background:#fdeaea!important;border-color:#e5a0a0!important;color:#b42318!important}
.rfp-score.bid{color:#137333!important}.rfp-score.review{color:#b7791f!important}.rfp-score.no-bid{color:#b42318!important}
.rfp-scorebar.bid span{background:#16803c!important}.rfp-scorebar.review span{background:#d99016!important}.rfp-scorebar.no-bid span{background:#c62828!important}
.rfp-recommendation-note{font-size:.82rem;font-weight:650;margin-top:.35rem}
.rfp-recommendation-note.bid{color:#137333!important}.rfp-recommendation-note.review{color:#9a5b00!important}.rfp-recommendation-note.no-bid{color:#b42318!important}
.rfp-score{font-size:2.55rem;font-weight:800;letter-spacing:-.05em;color:#172033;margin:.4rem 0}
.rfp-scorebar{height:10px;border-radius:20px;background:#e5eaf1;overflow:hidden;margin:.8rem 0}
.rfp-scorebar span{display:block;height:100%;background:#3478f6;border-radius:20px}
.rfp-risk{border-left-color:#c04c55}.rfp-strength{border-left-color:#16834b}
.rfp-two-col{display:grid;grid-template-columns:1fr 1fr;gap:14px}
[data-testid="stMetric"]{background:rgba(255,255,255,.34);backdrop-filter:blur(24px) saturate(150%);-webkit-backdrop-filter:blur(24px) saturate(150%);border:1px solid rgba(255,255,255,.78);border-radius:16px;padding:.9rem!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.8),0 10px 26px rgba(44,64,94,.055)}
[data-testid="stMetricLabel"],[data-testid="stMetricLabel"] p,[data-testid="stMetricValue"],[data-testid="stMetricValue"] div{color:#172033!important}
[data-testid="stVerticalBlockBorderWrapper"]{background:rgba(255,255,255,.32)!important;border:1px solid rgba(255,255,255,.78)!important;border-radius:17px!important;box-shadow:0 12px 30px rgba(44,64,94,.055),inset 0 1px 0 rgba(255,255,255,.82)!important;backdrop-filter:blur(24px) saturate(150%)!important;-webkit-backdrop-filter:blur(24px) saturate(150%)!important}

/* Chart containers and native chart typography */
.rfp-chart-title{font-size:1rem;font-weight:800;color:#1b2940;margin:.15rem 0 .25rem}
.rfp-chart-subtitle{font-size:.78rem;color:#78869a;margin-bottom:.45rem}
.rfp-donut-wrap{display:flex;align-items:center;gap:22px;min-height:190px;padding:.5rem .3rem}
.rfp-donut{width:154px;height:154px;border-radius:50%;flex:0 0 154px;position:relative;box-shadow:inset 0 0 0 1px rgba(255,255,255,.5)}
.rfp-donut:after{content:"";position:absolute;inset:29px;border-radius:50%;background:rgba(246,250,255,.78);backdrop-filter:blur(12px);box-shadow:0 0 0 1px rgba(130,148,174,.16),inset 0 1px 0 rgba(255,255,255,.8)}
.rfp-donut-center{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;z-index:1;color:#172033;font-weight:800}
.rfp-donut-center strong{font-size:1.55rem;line-height:1.2}
.rfp-donut-center span{font-size:.68rem;color:#78869a;font-weight:650}
.rfp-legend{display:flex;flex-direction:column;gap:11px;min-width:0}
.rfp-legend-row{display:flex;align-items:center;gap:8px;color:#44536a;font-size:.82rem}
.rfp-dot{width:9px;height:9px;border-radius:50%;display:inline-block;flex:0 0 9px}
.rfp-legend-row b{margin-left:auto;color:#172033;padding-left:10px}
.rfp-chart-card{position:relative;overflow:hidden;border:1px solid rgba(255,255,255,.78);border-radius:19px;background:linear-gradient(145deg,rgba(255,255,255,.43),rgba(255,255,255,.20));backdrop-filter:blur(27px) saturate(160%);-webkit-backdrop-filter:blur(27px) saturate(160%);padding:1.05rem 1.1rem .75rem;box-shadow:0 15px 36px rgba(44,64,94,.065),inset 0 1px 0 rgba(255,255,255,.85);margin:.2rem 0 1rem;min-height:245px}
.rfp-chart-card-tall{min-height:100%;height:100%;box-sizing:border-box}
.rfp-chart-card:before{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(125deg,rgba(255,255,255,.23),transparent 44%);border-radius:inherit}
.rfp-chart-card [data-testid="stVegaLiteChart"],.rfp-chart-card [data-testid="stArrowVegaLiteChart"]{background:transparent!important}

.rfp-html-chart{width:100%;overflow:hidden}
.rfp-hbar-list{display:flex;flex-direction:column;gap:13px;padding:.65rem .1rem .35rem}
.rfp-hbar-row{display:grid;grid-template-columns:minmax(105px,1.1fr) minmax(80px,2fr) 32px;gap:10px;align-items:center}
.rfp-hbar-label{font-size:.76rem;color:#526178;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rfp-hbar-track{height:11px;border-radius:20px;background:#e9eef5;overflow:hidden}
.rfp-hbar-fill{height:100%;border-radius:20px;background:linear-gradient(90deg,#3478f6,#42b7c4)}
.rfp-hbar-value{font-size:.76rem;color:#26364d;font-weight:750;text-align:right}
.rfp-empty-chart{height:170px;display:flex;align-items:center;justify-content:center;text-align:center;color:#8491a4;font-size:.82rem}
.rfp-line-svg{display:block;width:100%;height:auto;max-height:205px}

/* Balanced post-analysis layout: one full-width composition card and two equal insight cards */
.rfp-composition-wide{min-height:0!important;padding:1.2rem 1.35rem!important;margin:.35rem 0 1.15rem!important}
.rfp-composition-layout{display:grid;grid-template-columns:minmax(260px,.9fr) minmax(320px,1.1fr);gap:2rem;align-items:center}
.rfp-composition-layout .rfp-donut-wrap{min-height:180px}
.rfp-composition-breakdown{display:flex;flex-direction:column;gap:1rem;padding:.5rem .25rem}
.rfp-composition-row{display:flex;flex-direction:column;gap:.45rem}
.rfp-composition-label{display:flex;align-items:center;gap:.8rem;color:#526178;font-size:.84rem}
.rfp-composition-label b{margin-left:auto;color:#172033;font-size:.95rem}
.rfp-composition-label small{color:#7c8aa0;min-width:42px;text-align:right}
.rfp-composition-track{height:10px;border-radius:20px;background:#e8edf4;overflow:hidden}
.rfp-composition-track span{display:block;height:100%;border-radius:20px}
.rfp-insight-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.1rem;align-items:stretch;margin:.15rem 0 1.1rem}
.rfp-insight-card{height:100%;min-height:230px;box-sizing:border-box;margin:0!important;padding:1.25rem 1.35rem!important;display:flex;flex-direction:column}
.rfp-insight-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:.7rem;margin-bottom:.55rem}
.rfp-insight-heading h3{margin:0!important}
.rfp-insight-count{flex:0 0 auto;border-radius:999px;padding:.25rem .65rem;background:rgba(255,255,255,.72);border:1px solid rgba(126,145,171,.22);color:#53647c;font-size:.72rem;font-weight:800}
.rfp-insight-card ul{margin:.3rem 0 0!important;padding-left:1.1rem!important}
.rfp-insight-card li{margin:.45rem 0;overflow-wrap:anywhere}
@media(max-width:850px){
 .rfp-composition-layout{grid-template-columns:1fr;gap:.7rem}
 .rfp-insight-grid{grid-template-columns:1fr}
 .rfp-insight-card{min-height:0}
}

.rfp-chart-foot{font-size:.7rem;color:#8793a5;margin-top:.15rem}
.rfp-donut-wrap{min-height:185px}
@media(max-width:700px){.rfp-hbar-row{grid-template-columns:90px minmax(60px,2fr) 25px;gap:7px}.rfp-hbar-label{font-size:.7rem}}



/* Frosted-glass consistency and subtle motion */
.rfp-hero,.rfp-workflow,.rfp-kpi,.rfp-panel,.rfp-chart-card,.rfp-stage-pill{
 -webkit-backdrop-filter:blur(26px) saturate(155%);
}
@keyframes glassFloatIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.rfp-hero,.rfp-workflow,.rfp-kpi,.rfp-panel,.rfp-chart-card{animation:glassFloatIn .42s ease both}
/* Refined motion layer: staggered entrance, gentle hover depth and chart reveals */
.rfp-hero{animation:heroReveal .65s cubic-bezier(.2,.75,.25,1) both}
.rfp-hero:before{animation:ambientDrift 9s ease-in-out infinite alternate}
.rfp-workflow{animation:glassFloatIn .52s .08s ease both}
.rfp-kpi{animation:cardRise .52s cubic-bezier(.2,.75,.25,1) both}
.rfp-kpi:nth-child(1){animation-delay:.04s}.rfp-kpi:nth-child(2){animation-delay:.09s}
.rfp-kpi:nth-child(3){animation-delay:.14s}.rfp-kpi:nth-child(4){animation-delay:.19s}
.rfp-kpi:nth-child(5){animation-delay:.24s}.rfp-kpi:nth-child(6){animation-delay:.29s}
.rfp-kpi,.rfp-panel,.rfp-chart-card{will-change:transform}
.rfp-panel,.rfp-chart-card{transition:transform .28s cubic-bezier(.2,.75,.25,1),box-shadow .28s ease,border-color .28s ease}
.rfp-panel:hover,.rfp-chart-card:hover{transform:translateY(-3px);box-shadow:0 20px 42px rgba(44,64,94,.12),inset 0 1px 0 rgba(255,255,255,.9)}
.rfp-kpi:hover{transform:translateY(-6px) scale(1.012)}
.rfp-chart-card:after,.rfp-panel:after{content:"";position:absolute;inset:0;pointer-events:none;border-radius:inherit;background:linear-gradient(112deg,transparent 20%,rgba(255,255,255,.30) 48%,transparent 72%);transform:translateX(-130%);opacity:0}
.rfp-chart-card:hover:after,.rfp-panel:hover:after{opacity:1;animation:softShimmer .9s ease}
.rfp-hbar-fill{transform-origin:left center;animation:barReveal .9s cubic-bezier(.18,.72,.25,1) both}
.rfp-hbar-row:nth-child(2) .rfp-hbar-fill{animation-delay:.08s}.rfp-hbar-row:nth-child(3) .rfp-hbar-fill{animation-delay:.16s}
.rfp-hbar-row:nth-child(4) .rfp-hbar-fill{animation-delay:.24s}.rfp-hbar-row:nth-child(5) .rfp-hbar-fill{animation-delay:.32s}
.rfp-donut{animation:donutReveal .8s cubic-bezier(.2,.75,.25,1) both}
.rfp-scorebar span{transform-origin:left center;animation:scoreReveal 1s .2s cubic-bezier(.2,.75,.25,1) both}
.rfp-verdict{animation:badgeReveal .45s .25s ease both}
.rfp-flowbar span{background-size:200% 100%;animation:flowShimmer 4s linear infinite}
@keyframes heroReveal{from{opacity:0;transform:translateY(12px) scale(.992)}to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes cardRise{from{opacity:0;transform:translateY(15px)}to{opacity:1;transform:translateY(0)}}
@keyframes ambientDrift{from{transform:translate3d(0,0,0) scale(.94)}to{transform:translate3d(-24px,18px,0) scale(1.08)}}
@keyframes softShimmer{0%{transform:translateX(-130%)}100%{transform:translateX(130%)}}
@keyframes barReveal{from{transform:scaleX(0);opacity:.45}to{transform:scaleX(1);opacity:1}}
@keyframes donutReveal{from{opacity:.4;transform:scale(.82) rotate(-35deg)}to{opacity:1;transform:scale(1) rotate(0)}}
@keyframes scoreReveal{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes badgeReveal{from{opacity:0;transform:scale(.92)}to{opacity:1;transform:scale(1)}}
@keyframes flowShimmer{0%{background-position:100% 0}100%{background-position:-100% 0}}
@media(prefers-reduced-motion:reduce){
 .rfp-hero,.rfp-workflow,.rfp-kpi,.rfp-panel,.rfp-chart-card,.rfp-donut,.rfp-hbar-fill,.rfp-scorebar span,.rfp-verdict,.rfp-flowbar span{animation:none!important;transition:none!important;will-change:auto!important}
 .rfp-panel:hover,.rfp-chart-card:hover,.rfp-kpi:hover{transform:none!important}
}

/* Main-window document importer */
[data-testid="stMain"] [data-testid="stFileUploader"] section{
 background:rgba(255,255,255,.72)!important;
 border:1px dashed rgba(65,105,155,.48)!important;
 border-radius:14px!important;
 padding:1rem!important;
}
[data-testid="stMain"] [data-testid="stFileUploader"] section,
[data-testid="stMain"] [data-testid="stFileUploader"] section *{
 color:#26364d!important;-webkit-text-fill-color:#26364d!important;opacity:1!important;
}
[data-testid="stMain"] [data-testid="stFileUploader"] button{
 background:#1b2940!important;color:#fff!important;border:1px solid #1b2940!important;
 border-radius:9px!important;font-weight:700!important;
}
[data-testid="stMain"] [data-testid="stFileUploader"] button *{
 color:#fff!important;-webkit-text-fill-color:#fff!important;
}

/* Main controls — visible text on every state */
.stButton button,.stDownloadButton button{border-radius:9px!important;border:1px solid #26364d!important;background:#1b2940!important;color:#fff!important;font-weight:700!important;transition:all .18s ease!important}
.stButton button *, .stDownloadButton button *{color:#fff!important;-webkit-text-fill-color:#fff!important}
.stButton button:hover,.stDownloadButton button:hover{background:#2e4668!important;border-color:#2e4668!important;transform:translateY(-1px)}
.stButton button:disabled,.stDownloadButton button:disabled{background:#e1e6ee!important;border-color:#d0d8e3!important;color:#758197!important;opacity:1!important}
.stButton button:disabled *,.stDownloadButton button:disabled *{color:#758197!important;-webkit-text-fill-color:#758197!important}
.stTextInput input,.stTextArea textarea,[data-testid="stSelectbox"] [data-baseweb="select"]>div,[data-testid="stMultiSelect"] [data-baseweb="select"]>div{
 background:rgba(255,255,255,.88)!important;color:#172033!important;-webkit-text-fill-color:#172033!important;border:1px solid #d5deea!important;border-radius:9px!important
}
[data-testid="stSelectbox"] [data-baseweb="select"] *,[data-testid="stMultiSelect"] [data-baseweb="select"] *,
[data-testid="stSelectbox"] input,[data-testid="stMultiSelect"] input{color:#172033!important;-webkit-text-fill-color:#172033!important;opacity:1!important}
[data-testid="stSelectbox"] svg,[data-testid="stMultiSelect"] svg{fill:#172033!important;color:#172033!important}
.stTextInput input::placeholder,.stTextArea textarea::placeholder{color:#8491a4!important;-webkit-text-fill-color:#8491a4!important}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border:1px solid rgba(150,166,188,.35);border-radius:11px;overflow:hidden}
[data-testid="stAlert"]{border-radius:12px!important}
[data-testid="stCaptionContainer"] p{color:#7c899c!important}
hr{border-color:rgba(126,145,171,.25)!important}
@keyframes fadein{from{opacity:.65;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:1150px){.rfp-kpis{grid-template-columns:repeat(3,1fr)}.rfp-workflow{grid-template-columns:repeat(2,1fr)}}
@media(max-width:700px){[data-testid="stMainBlockContainer"],.main .block-container{padding:.65rem .65rem 2rem!important}.rfp-kpis{grid-template-columns:repeat(2,1fr)}.rfp-two-col{grid-template-columns:1fr}.rfp-stage-pill{position:relative;right:auto;top:auto;margin-top:.8rem;display:inline-block}.rfp-workflow{grid-template-columns:1fr}.rfp-topbar{flex-wrap:wrap}.rfp-donut-wrap{flex-wrap:wrap}}
/* Premium glass finish: slightly clearer surfaces, stronger blur, and restrained motion */
[data-testid="stApp"]{
 background-size:145% 145%!important;
 animation:rfpAmbientCanvas 28s ease-in-out infinite alternate;
}
.rfp-hero{
 background:linear-gradient(112deg,rgba(255,255,255,.39),rgba(255,255,255,.18) 58%,rgba(194,231,239,.25))!important;
 backdrop-filter:blur(34px) saturate(170%)!important;-webkit-backdrop-filter:blur(34px) saturate(170%)!important;
}
.rfp-workflow{
 background:rgba(255,255,255,.27)!important;
 backdrop-filter:blur(32px) saturate(165%)!important;-webkit-backdrop-filter:blur(32px) saturate(165%)!important;
}
.rfp-kpi{
 background:linear-gradient(145deg,rgba(255,255,255,.39),rgba(255,255,255,.15))!important;
 backdrop-filter:blur(32px) saturate(175%)!important;-webkit-backdrop-filter:blur(32px) saturate(175%)!important;
}
.rfp-panel,.rfp-chart-card{
 background:linear-gradient(140deg,rgba(255,255,255,.34),rgba(255,255,255,.15))!important;
 backdrop-filter:blur(32px) saturate(170%)!important;-webkit-backdrop-filter:blur(32px) saturate(170%)!important;
 border-color:rgba(255,255,255,.84)!important;
}
.rfp-stage-pill,[data-testid="stMetric"],[data-testid="stVerticalBlockBorderWrapper"]{
 backdrop-filter:blur(30px) saturate(165%)!important;-webkit-backdrop-filter:blur(30px) saturate(165%)!important;
}
/* Gentle interactive feedback on controls without changing their behaviour */
.stButton button,.stDownloadButton button,[data-testid="stFormSubmitButton"] button{
 box-shadow:0 5px 14px rgba(28,48,78,.10)!important;
 transition:transform .2s ease,box-shadow .2s ease,background .2s ease!important;
}
.stButton button:hover,.stDownloadButton button:hover,[data-testid="stFormSubmitButton"] button:hover{
 transform:translateY(-2px)!important;box-shadow:0 9px 20px rgba(28,48,78,.17)!important;
}
.stTextInput input:focus,.stTextArea textarea:focus{
 border-color:#6b9df4!important;box-shadow:0 0 0 3px rgba(75,132,235,.14)!important;
}
[data-testid="stTabs"] button{transition:color .18s ease,background .18s ease!important}
[data-testid="stTabs"] button[aria-selected="true"]{color:#245fc5!important}
@keyframes rfpAmbientCanvas{
 0%{background-position:0% 35%}
 100%{background-position:100% 65%}
}
@media(prefers-reduced-motion:reduce){
 [data-testid="stApp"]{animation:none!important}
 *,*:before,*:after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}
}

/* Decision Centre: strong contrast, visible labels, glass panel and clear action */
.rfp-decision-shell{
  position:relative; overflow:hidden; margin:1rem 0 1.2rem; padding:1.35rem 1.45rem;
  border:1px solid rgba(255,255,255,.92); border-left:5px solid #3478f6;
  border-radius:20px;
  background:linear-gradient(135deg,rgba(255,255,255,.84),rgba(235,244,255,.70) 58%,rgba(220,244,246,.66));
  backdrop-filter:blur(28px) saturate(165%); -webkit-backdrop-filter:blur(28px) saturate(165%);
  box-shadow:0 16px 38px rgba(31,52,82,.10),inset 0 1px 0 rgba(255,255,255,.95);
  animation:decisionEnter .55s cubic-bezier(.2,.75,.25,1) both;
}
.rfp-decision-shell h2,.rfp-decision-shell h3{color:#172033!important;font-weight:800!important}
.rfp-decision-shell p,.rfp-decision-shell span{color:#43536b}
[data-testid="stExpander"]{
  background:rgba(255,255,255,.74)!important;
  border:1px solid rgba(116,139,170,.34)!important;border-radius:16px!important;
  overflow:hidden!important;box-shadow:0 12px 28px rgba(31,52,82,.07)!important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary *,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"],
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] *{
  color:#172033!important;-webkit-text-fill-color:#172033!important;opacity:1!important;
}
[data-testid="stExpander"] summary{background:rgba(255,255,255,.72)!important;font-weight:800!important}
[data-testid="stExpander"] details > div{background:rgba(255,255,255,.60)!important}
[data-testid="stForm"]{background:transparent!important;border:0!important;padding:0!important}
[data-testid="stRadio"] > label,
[data-testid="stTextArea"] > label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *{
  color:#172033!important;-webkit-text-fill-color:#172033!important;opacity:1!important;font-weight:700!important;
}
[data-testid="stRadio"] [role="radiogroup"] label{
  color:#172033!important;-webkit-text-fill-color:#172033!important;
  background:rgba(255,255,255,.84)!important;border:1px solid #d5deea!important;
  border-radius:12px!important;padding:.55rem .8rem!important;margin:.15rem .25rem .15rem 0!important;
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease!important;
}
[data-testid="stRadio"] [role="radiogroup"] label:hover{
  transform:translateY(-2px)!important;border-color:#7ba7ed!important;
  box-shadow:0 7px 16px rgba(48,91,155,.12)!important;
}
[data-testid="stRadio"] [role="radiogroup"] label *,
[data-testid="stRadio"] [role="radiogroup"] label p{
  color:#172033!important;-webkit-text-fill-color:#172033!important;opacity:1!important;
}
[data-testid="stTextArea"] textarea{
  min-height:112px!important;background:rgba(255,255,255,.96)!important;
  color:#172033!important;-webkit-text-fill-color:#172033!important;
  border:1px solid #cbd7e6!important;border-radius:12px!important;
  font-size:.96rem!important;line-height:1.5!important;
}
[data-testid="stTextArea"] textarea::placeholder{
  color:#718096!important;-webkit-text-fill-color:#718096!important;opacity:1!important;
}
[data-testid="stTextArea"] textarea:focus{
  border-color:#3478f6!important;box-shadow:0 0 0 3px rgba(52,120,246,.16)!important;
}
[data-testid="stFormSubmitButton"] button,
.rfp-decision-submit button{
  min-height:3rem!important;border-radius:12px!important;
  border:1px solid #245fc5!important;
  background:linear-gradient(105deg,#245fc5,#258fae)!important;
  color:#fff!important;-webkit-text-fill-color:#fff!important;
  font-size:1rem!important;font-weight:800!important;letter-spacing:.01em!important;
  box-shadow:0 9px 22px rgba(37,95,197,.22)!important;
  transition:transform .2s ease,box-shadow .2s ease,filter .2s ease!important;
}
[data-testid="stFormSubmitButton"] button *,
.rfp-decision-submit button *{
  color:#fff!important;-webkit-text-fill-color:#fff!important;opacity:1!important;
}
[data-testid="stFormSubmitButton"] button:hover,
.rfp-decision-submit button:hover{
  transform:translateY(-2px)!important;filter:brightness(1.06)!important;
  box-shadow:0 13px 27px rgba(37,95,197,.30)!important;
}
.rfp-decision-help{font-size:.82rem;color:#65758c!important;margin:.45rem 0 .8rem}
@keyframes decisionEnter{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@keyframes decisionGlow{0%,100%{box-shadow:0 16px 38px rgba(31,52,82,.10),inset 0 1px 0 rgba(255,255,255,.95)}50%{box-shadow:0 18px 42px rgba(52,120,246,.16),inset 0 1px 0 rgba(255,255,255,.98)}}
.rfp-decision-shell:hover{animation:decisionGlow 3.8s ease-in-out infinite}
@media(prefers-reduced-motion:reduce){
 .rfp-decision-shell,.rfp-decision-shell:hover{animation:none!important}
 [data-testid="stRadio"] [role="radiogroup"] label,
 [data-testid="stFormSubmitButton"] button,.rfp-decision-submit button{transition:none!important}
}

</style>

""", unsafe_allow_html=True)


def init_state():
    defaults={"pages":[],"requirements":[],"matches":[],"risks":[],"questions":[],"proposal":[],"recommendation":{},"file_name":"","opportunity_stage":"New","human_decision":"Pending human review","decision_notes":"","opportunity_id":None,"decision_save_notice":""}
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


def opportunity_payload():
    return {k:st.session_state[k] for k in ("pages","requirements","matches","risks","questions","proposal","recommendation","file_name","opportunity_stage","human_decision","decision_notes")}


def save_current():
    if not st.session_state.get("file_name"):
        st.warning("Process an RFP before saving.")
        return
    oid=save_opportunity(opportunity_payload(),st.session_state.get("opportunity_id"))
    st.session_state["opportunity_id"]=oid
    st.success(f"Opportunity saved as #{oid}.")


def confirm_human_decision(decision, notes):
    """Validate and persist the authorised reviewer's final decision."""
    if not st.session_state.get("file_name"):
        st.error("Import and process an RFP before confirming a decision.")
        return
    if decision == "Pending human review":
        st.warning("Choose Bid, No-Bid or Hold for clarification before confirming.")
        return
    clean_notes = str(notes or "").strip()
    if not clean_notes:
        st.warning("Please enter a decision justification before saving.")
        return

    st.session_state["human_decision"] = decision
    st.session_state["decision_notes"] = clean_notes
    try:
        oid=save_opportunity(opportunity_payload(),st.session_state.get("opportunity_id"))
        st.session_state["opportunity_id"] = oid
        st.session_state["decision_save_notice"] = f"{decision} decision saved successfully for opportunity #{oid}."
        st.rerun()
    except Exception as exc:
        st.error(f"Could not save the decision. Please try again. Details: {exc}")


def load_saved(oid):
    payload=load_opportunity(oid)
    if not payload: st.error("Saved opportunity could not be loaded."); return
    for k,v in payload.items():
        if k in st.session_state: st.session_state[k]=v
        elif k in ("pages","requirements","matches","risks","questions","proposal","recommendation","file_name","opportunity_stage","human_decision","decision_notes","opportunity_id"): st.session_state[k]=v
    # Keep decision widgets in sync with the loaded opportunity payload.
    st.session_state["human_decision_radio"] = st.session_state.get("human_decision","Pending human review")
    st.session_state["decision_notes_text"] = st.session_state.get("decision_notes","")
    for k in ("requirements_editor","proposal_editor"): st.session_state.pop(k,None)
    st.rerun()


def safe(v): return html.escape(str(v if v is not None else ""))


def metric_card(icon,label,value,colour,decision=False):
    cls=f"rfp-kpi {colour}"+(" decision" if decision else "")
    return f'<div class="{cls}"><div class="ico">{icon}</div><div class="lab">{safe(label)}</div><div class="val">{safe(value)}</div></div>'



def _export_frames():
    """Build consistent report tables from the current opportunity session."""
    reqs = st.session_state.get("requirements", [])
    matches = st.session_state.get("matches", [])
    risks = st.session_state.get("risks", [])
    questions = st.session_state.get("questions", [])
    proposal = st.session_state.get("proposal", [])
    rec = st.session_state.get("recommendation", {}) or {}

    summary = [
        ("RFP file", st.session_state.get("file_name", "")),
        ("Opportunity ID", st.session_state.get("opportunity_id") or "Not saved yet"),
        ("Exported at", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("Opportunity stage", st.session_state.get("opportunity_stage", "")),
        ("AI recommendation", rec.get("Signal", "Not analysed")),
        ("Feasibility score", rec.get("Score", "")),
        ("Mandatory requirements", rec.get("Mandatory Requirements", "")),
        ("Mandatory gaps", rec.get("Mandatory Gaps", "")),
        ("High risks", rec.get("High Risks", "")),
        ("Items to verify", rec.get("Items to Verify", "")),
        ("Human decision", st.session_state.get("human_decision", "Pending human review")),
        ("Decision justification", st.session_state.get("decision_notes", "")),
    ]
    return {
        "summary": pd.DataFrame(summary, columns=["Field", "Value"]),
        "requirements": pd.DataFrame(reqs),
        "capability_match": pd.DataFrame(matches),
        "risk_register": pd.DataFrame(risks),
        "clarifications": pd.DataFrame(questions),
        "proposal_queue": pd.DataFrame(proposal),
    }


def build_excel_export():
    """Return a multi-sheet XLSX workbook for the active RFP analysis."""
    frames = _export_frames()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        sheet_names = {
            "summary": "Executive Summary",
            "requirements": "Requirements",
            "capability_match": "Capability Match",
            "risk_register": "Risk Register",
            "clarifications": "Clarifications",
            "proposal_queue": "Proposal Queue",
        }
        for key, frame in frames.items():
            frame.to_excel(writer, sheet_name=sheet_names[key], index=False)
            ws = writer.sheets[sheet_names[key]]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for column_cells in ws.columns:
                values = [len(str(cell.value or "")) for cell in column_cells]
                width = min(max(max(values, default=10) + 2, 12), 58)
                ws.column_dimensions[column_cells[0].column_letter].width = width
            for cell in ws[1]:
                cell.font = cell.font.copy(bold=True, color="FFFFFF")
                cell.fill = __import__("openpyxl").styles.PatternFill(
                    "solid", fgColor="1B2940"
                )
    output.seek(0)
    return output.getvalue()


def build_pdf_export():
    """Return a clean, printable PDF summary with the opportunity evidence."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    )
    from xml.sax.saxutils import escape

    frames = _export_frames()
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=landscape(A4),
        rightMargin=13 * mm, leftMargin=13 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title="RFP Intelligence Analysis Report",
        author="RFP Intelligence",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], textColor=colors.HexColor("#172033"),
        fontName="Helvetica-Bold", fontSize=20, leading=24, alignment=TA_LEFT,
        spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        name="SectionHead", parent=styles["Heading2"],
        textColor=colors.HexColor("#245FC5"), fontSize=12, leading=15,
        spaceBefore=5 * mm, spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name="CellText", parent=styles["BodyText"], fontSize=7.5, leading=9,
        wordWrap="CJK",
    ))
    styles.add(ParagraphStyle(
        name="SmallText", parent=styles["BodyText"], fontSize=8, leading=10,
        textColor=colors.HexColor("#53647C"),
    ))

    def clean(value):
        text = str(value if value is not None else "")
        # Built-in PDF fonts do not cover every Unicode glyph.
        return text.replace("—", "-").replace("–", "-").replace("•", "-").replace("✓", "Yes")

    def make_table(frame, max_rows=250):
        if frame.empty:
            return [Paragraph("No records available.", styles["SmallText"])]
        display = frame.head(max_rows).fillna("")
        data = [[Paragraph(f"<b>{escape(clean(c))}</b>", styles["CellText"])
                 for c in display.columns]]
        for row in display.astype(str).itertuples(index=False, name=None):
            data.append([
                Paragraph(escape(clean(value)).replace("\n", "<br/>"), styles["CellText"])
                for value in row
            ])
        usable_width = landscape(A4)[0] - 26 * mm
        col_count = max(1, len(display.columns))
        widths = [usable_width / col_count] * col_count
        table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B2940")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6DEEA")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F2F6FB")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return [table]

    story = [
        Paragraph("RFP Intelligence", styles["ReportTitle"]),
        Paragraph("Procurement analysis report | Evidence-led, human-approved decision support",
                  styles["SmallText"]),
        Spacer(1, 4 * mm),
    ]
    story += make_table(frames["summary"], max_rows=50)
    for key, heading in [
        ("requirements", "Extracted Requirements"),
        ("capability_match", "Capability Match"),
        ("risk_register", "Risk Register"),
        ("clarifications", "Clarification Questions"),
        ("proposal_queue", "Proposal Work Queue"),
    ]:
        story.append(Paragraph(heading, styles["SectionHead"]))
        story += make_table(frames[key])
    doc.build(story)
    output.seek(0)
    return output.getvalue()


def render_save_export_controls(location="sidebar"):
    """Render persistent save and report-download controls for the active RFP."""
    if not st.session_state.get("file_name"):
        return
    st.markdown("**Save & export analysis**")
    if st.button("Save analysis to database", use_container_width=True,
                 key=f"{location}_save_analysis"):
        save_current()
    try:
        pdf_bytes = build_pdf_export()
        st.download_button(
            "Download PDF report", data=pdf_bytes,
            file_name=f"{os.path.splitext(st.session_state['file_name'])[0]}_analysis_report.pdf",
            mime="application/pdf", use_container_width=True,
            key=f"{location}_export_pdf",
        )
    except ImportError:
        st.warning("PDF export requires reportlab. Add `reportlab` to requirements.txt.")
    except Exception as exc:
        st.error(f"PDF export could not be prepared: {exc}")
    try:
        excel_bytes = build_excel_export()
        st.download_button(
            "Download Excel workbook", data=excel_bytes,
            file_name=f"{os.path.splitext(st.session_state['file_name'])[0]}_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, key=f"{location}_export_excel",
        )
    except ImportError:
        st.warning("Excel export requires openpyxl. Add `openpyxl` to requirements.txt.")
    except Exception as exc:
        st.error(f"Excel export could not be prepared: {exc}")


def main():
    init_state(); initialise_database()
    if st.session_state.get("decision_save_notice"):
        st.success(st.session_state["decision_save_notice"])
        st.session_state["decision_save_notice"] = ""
    # Import-first workspace: keep the sidebar focused until a document is processed.
    with st.sidebar:
        st.markdown("<div style='font-size:1.08rem;font-weight:800;letter-spacing:-.035em;margin:.25rem 0 1rem;color:#fff'>RFP INTELLIGENCE</div>",unsafe_allow_html=True)

        has_document = bool(st.session_state.get("file_name"))
        if has_document:
            nav=st.radio("WORKSPACE",["⌂  Dashboard","▤  Requirements","◈  Capability Match","⚠  Risk Analysis","◎  Decision Centre","▣  Proposal Support","▦  Opportunities"],label_visibility="collapsed",key="main_navigation")
            st.markdown("<div style='height:1px;background:#444;margin:1rem 0'></div>",unsafe_allow_html=True)
        else:
            nav="⌂  Dashboard"

        # Keep New RFP intake available in the sidebar at all times.
        st.subheader("New RFP / Upload")
        sidebar_upload = st.file_uploader(
            "Choose another tender document",
            type=["pdf", "xls", "xlsx", "xlx"],
            key="rfp_upload_sidebar",
            help="Uploading a new RFP replaces the active workspace. Previously saved opportunities remain in the database.",
        )
        if st.button(
            "Process new RFP",
            type="primary",
            use_container_width=True,
            disabled=sidebar_upload is None,
            key="sidebar_process_new_rfp",
        ):
            process_upload(sidebar_upload)
            if st.session_state.get("file_name"):
                st.rerun()

        if st.session_state.get("file_name"):
            st.caption("The active workspace will switch to the new RFP. Save this opportunity first if you want to preserve its latest unsaved edits.")
            st.markdown("<div style='height:1px;background:#444;margin:1.1rem 0'></div>",unsafe_allow_html=True)
            st.subheader("Company capability profile")
            cap=st.text_area("One capability per line",value="\n".join(DEFAULT_CAPABILITIES),height=155,key="capability_profile",help="Edit this profile to reflect the capabilities relevant to the current tender.")
            if st.button("Run capability analysis",use_container_width=True,disabled=not bool(st.session_state["requirements"])):
                run_analysis(cap)

            st.markdown("<div style='height:1px;background:#444;margin:1.1rem 0'></div>",unsafe_allow_html=True)
            stage_options=["New","Analysis","Review","Bid Decision","Proposal","Submitted","Won","Lost"]
            stage=st.selectbox("Opportunity stage",stage_options,index=stage_options.index(st.session_state["opportunity_stage"]) if st.session_state["opportunity_stage"] in stage_options else 0)
            st.session_state["opportunity_stage"]=stage
            st.caption(f"Human decision: **{st.session_state['human_decision']}**")

            with st.expander("Saved opportunities",expanded=False):
                saved=list_opportunities()
                labels=["Create new / current opportunity"]+[f"#{x['id']} · {x['file_name']} · {x['stage']}" for x in saved]
                selected=st.selectbox("Load opportunity",labels)
                if st.button("Load selected",use_container_width=True,disabled=selected==labels[0]):
                    load_saved(int(saved[labels.index(selected)-1]["id"]))
                if st.button("Save current opportunity",use_container_width=True,disabled=not bool(st.session_state["file_name"])):
                    save_current()
                if st.button("Clear current opportunity",use_container_width=True):
                    for k in ("pages","requirements","matches","risks","questions","proposal"):
                        st.session_state[k]=[]
                    st.session_state.update({"recommendation":{},"file_name":"","opportunity_stage":"New","human_decision":"Pending human review","decision_notes":"","opportunity_id":None})
                    st.rerun()

            st.markdown("<div style='height:1px;background:#444;margin:1.1rem 0'></div>",unsafe_allow_html=True)
            render_save_export_controls("sidebar")

    # Before import, show a focused welcome state and a central document importer —
    # no empty KPI cards, workflow cards, charts, or analysis panels.
    # workflow steps, charts, or analysis panels.
    if not st.session_state.get("file_name"):
        st.markdown(
            "<div class='rfp-topbar'><div class='rfp-brand'>RFP <span>Intelligence</span></div>"
            "<div class='rfp-topmeta'>Procurement Intelligence Workspace</div>"
            "<div class='rfp-topmeta'>Evidence-led · Human-approved</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<section class='rfp-import-shell'>"
            "<div class='rfp-import-eyebrow'>PROCUREMENT WORKSPACE</div>"
            "<div class='rfp-import-title'>Start with your tender document</div>"
            "<p class='rfp-import-copy'>Import an RFP or tender to extract requirements, compare company capabilities, identify risks and prepare an evidence-based bid recommendation.</p>"
            "<div class='rfp-import-steps'>"
            "<div><span>01</span><b>Import document</b><small>PDF, XLS or XLSX</small></div>"
            "<div><span>02</span><b>Review requirements</b><small>Extracted with source references</small></div>"
            "<div><span>03</span><b>Analyse opportunity</b><small>Capability, risks and bid signals</small></div>"
            "</div>"
            "</section>",
            unsafe_allow_html=True,
        )

        # Main-window upload area: wide, visible and easy to use.
        left, center, right = st.columns([1, 4, 1])
        with center:
            with st.container(border=True):
                st.markdown("### Import your RFP / tender document")
                st.caption("Choose a PDF, Excel XLS or XLSX file. Your dashboard will appear after processing.")
                main_upload = st.file_uploader(
                    "Select document",
                    type=["pdf", "xls", "xlsx", "xlx"],
                    key="rfp_upload_main",
                    help="Supported formats: PDF, XLS and XLSX",
                )
                if st.button(
                    "Import & process document",
                    type="primary",
                    use_container_width=True,
                    disabled=main_upload is None,
                    key="main_import_process_button",
                ):
                    process_upload(main_upload)
                    if st.session_state.get("file_name"):
                        st.rerun()
        return

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

    # Save and export actions are also available in the main dashboard.
    if nav.startswith("⌂"):
        with st.expander("Save & Export Analysis", expanded=False):
            st.caption("Save the current opportunity to the database, or export a report for sharing and review.")
            render_save_export_controls("dashboard")

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
                # Three-state advisory: mandatory gaps override the score.
                # Green = Bid, Orange = Review, Red = No-Bid.
                if mg > 0 or "No-Bid" in signal:
                    verdict = "RECOMMENDATION: NO-BID"
                    verdict_class = "no-bid"
                    recommendation_note = "Mandatory requirement gap detected — do not bid unless the gap is resolved."
                elif score >= 70:
                    verdict = "RECOMMENDATION: BID"
                    verdict_class = "bid"
                    recommendation_note = "Good capability alignment — suitable to proceed to human bid review."
                else:
                    verdict = "RECOMMENDATION: REVIEW"
                    verdict_class = "review"
                    recommendation_note = "Partial / incomplete evidence — clarify gaps and risks before deciding."
                # Prepare chart data before laying out the dashboard.
                category_counts=pd.Series([m.get("Category","Other") for m in matches]).value_counts().head(6)
                if not category_counts.empty:
                    max_category=max(int(category_counts.max()),1)
                    category_rows=[]
                    for label,count in category_counts.items():
                        width=max(3,round(int(count)/max_category*100))
                        category_rows.append(
                            f"<div class='rfp-hbar-row'><div class='rfp-hbar-label' title='{safe(label)}'>{safe(label)}</div>"
                            f"<div class='rfp-hbar-track'><div class='rfp-hbar-fill' style='width:{width}%'></div></div>"
                            f"<div class='rfp-hbar-value'>{int(count)}</div></div>"
                        )
                    category_chart="".join(category_rows)
                else:
                    category_chart="<div class='rfp-empty-chart'>Category data will appear after capability analysis.</div>"

                type_counts=pd.Series([str(x.get("Type","Needs Verification")) for x in reqs]).value_counts()
                type_palette={"Mandatory":"#3478f6","Optional":"#26b9c8","Needs Verification":"#8b70df"}
                donut_total=int(type_counts.sum())
                if donut_total:
                    donut_parts=[]; legend_parts=[]; cursor=0.0
                    for label,count in type_counts.items():
                        colour=type_palette.get(label,"#9aa7b8")
                        end_angle=cursor+(float(count)/donut_total*100)
                        donut_parts.append(f"{colour} {cursor:.2f}% {end_angle:.2f}%")
                        legend_parts.append(
                            f"<div class='rfp-legend-row'><span class='rfp-dot' style='background:{colour}'></span>"
                            f"<span>{safe(label)}</span><b>{int(count)}</b></div>"
                        )
                        cursor=end_angle
                    donut_gradient="conic-gradient("+", ".join(donut_parts)+")"
                    donut_chart=(
                        f"<div class='rfp-donut-wrap'><div class='rfp-donut' style='background:{donut_gradient}'>"
                        f"<div class='rfp-donut-center'><strong>{donut_total}</strong><span>Requirements</span></div></div>"
                        f"<div class='rfp-legend'>{''.join(legend_parts)}</div></div>"
                    )
                else:
                    donut_chart="<div class='rfp-empty-chart'>No requirement types found yet.</div>"

                # Count requirements by source page / worksheet.
                source_counts={}
                for item in reqs:
                    source=item.get("Source Page",item.get("Source",item.get("Page",item.get("page",""))))
                    if source not in (None,""):
                        source=str(source)
                        source_counts[source]=source_counts.get(source,0)+1

                if source_counts:
                    source_items=list(source_counts.items())
                    vals=[int(v) for _,v in source_items]
                    labels=[str(k) for k,_ in source_items]
                    width_svg=560; height_svg=190; left=42; right=18; top=16; bottom=42
                    plot_w=width_svg-left-right; plot_h=height_svg-top-bottom
                    max_val=max(vals+[1])
                    points=[]
                    for idx,val in enumerate(vals):
                        x=left+(plot_w/2 if len(vals)==1 else idx*plot_w/(len(vals)-1))
                        y=top+plot_h-(val/max_val)*plot_h
                        points.append((x,y))
                    polyline=" ".join(f"{x:.1f},{y:.1f}" for x,y in points)
                    grid_parts=[]
                    for fraction in (0,0.5,1):
                        gy=top+plot_h-(fraction*plot_h)
                        grid_parts.append(f"<line x1='{left}' y1='{gy:.1f}' x2='{width_svg-right}' y2='{gy:.1f}' stroke='#e6ebf2' stroke-width='1'/>")
                    point_parts=[]
                    for idx,((x,y),val,label) in enumerate(zip(points,vals,labels)):
                        point_parts.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='5' fill='#26a6b8' stroke='white' stroke-width='2'/>")
                        if len(vals)<=6:
                            point_parts.append(f"<text x='{x:.1f}' y='{height_svg-16}' text-anchor='middle' font-size='10' fill='#758399'>{safe(label[:13])}</text>")
                        point_parts.append(f"<text x='{x:.1f}' y='{y-11:.1f}' text-anchor='middle' font-size='11' font-weight='700' fill='#344258'>{val}</text>")
                    if len(points)==1:
                        line_markup=f"<line x1='{left+8}' y1='{points[0][1]:.1f}' x2='{width_svg-right-8}' y2='{points[0][1]:.1f}' stroke='#26a6b8' stroke-width='3' stroke-linecap='round' opacity='.45'/>"
                        source_note="One source unit in this document — trend will appear when multiple pages or sheets are available."
                    else:
                        line_markup=f"<polyline points='{polyline}' fill='none' stroke='#26a6b8' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>"
                        source_note=f"{len(vals)} source units"
                    line_chart=(
                        f"<svg class='rfp-line-svg' viewBox='0 0 {width_svg} {height_svg}' role='img' aria-label='Requirements by source page'>"
                        f"{''.join(grid_parts)}{line_markup}{''.join(point_parts)}</svg>"
                        f"<div class='rfp-chart-foot'>{safe(source_note)}</div>"
                    )
                else:
                    line_chart="<div class='rfp-empty-chart'>Source page references will appear here when available.</div>"

                # Balanced dashboard: score and category chart share the first row;
                # composition and source-page trend share the second row.
                col1,col2=st.columns([1.08,1],gap="large")
                with col1:
                    st.markdown(
                        f"<div class='rfp-panel pinkpanel'><h3>◎ &nbsp; AI Bid Intelligence <span class='rfp-verdict {verdict_class}'>{safe(verdict)}</span></h3>"
                        f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:1rem'>"
                        f"<div><div class='rfp-score {verdict_class}'>{score} / 100</div><div>Feasibility Score</div>"
                        f"<div class='rfp-scorebar {verdict_class}'><span style='width:{max(0,min(100,score))}%'></span></div>"
                        f"<div class='muted'>Evidence-based feasibility estimate</div>"
                        f"<div class='rfp-recommendation-note {verdict_class}'>{safe(recommendation_note)}</div></div>"
                        f"<div style='border-left:1px solid rgba(126,145,171,.25);padding-left:1.1rem'>"
                        f"<div style='margin:.35rem 0'>▱ &nbsp; <b>{met} / {mt} Met</b><br><span class='muted'>Mandatory Compliance</span></div>"
                        f"<div style='margin:.65rem 0'>⚠ &nbsp; <b>{hr} Risks</b><br><span class='muted'>High-Severity Risks</span></div>"
                        f"<div style='margin:.65rem 0'>▤ &nbsp; <b>{verify} Items</b><br><span class='muted'>Clarifications Needed</span></div>"
                        f"</div></div></div>",
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f"<div class='rfp-chart-card rfp-chart-card-tall'><div class='rfp-chart-title'>Requirements by Category</div>"
                        f"<div class='rfp-chart-subtitle'>Extracted requirement distribution</div>"
                        f"<div class='rfp-html-chart'><div class='rfp-hbar-list'>{category_chart}</div></div></div>",
                        unsafe_allow_html=True
                    )

                # Keep Requirement Composition, remove the low-value source-page trend
                # card, and use the freed space for a balanced full-width composition view.
                composition_rows=[]
                for label,count in type_counts.items():
                    pct=(float(count)/donut_total*100) if donut_total else 0
                    colour=type_palette.get(label,"#9aa7b8")
                    composition_rows.append(
                        f"<div class='rfp-composition-row'>"
                        f"<div class='rfp-composition-label'><span>{safe(label)}</span>"
                        f"<b>{int(count)}</b><small>{pct:.0f}%</small></div>"
                        f"<div class='rfp-composition-track'><span style='width:{pct:.1f}%;background:{colour}'></span></div>"
                        f"</div>"
                    )
                composition_summary="".join(composition_rows) or "<div class='rfp-empty-chart'>No requirement composition data available.</div>"
                st.markdown(
                    f"<div class='rfp-chart-card rfp-composition-wide'>"
                    f"<div class='rfp-chart-title'>Requirement Composition</div>"
                    f"<div class='rfp-chart-subtitle'>Mandatory, optional and verification workload</div>"
                    f"<div class='rfp-composition-layout'><div>{donut_chart}</div>"
                    f"<div class='rfp-composition-breakdown'>{composition_summary}</div></div></div>",
                    unsafe_allow_html=True
                )

                # Equal-height insight cards. When no blockers exist, show the
                # compliance summary so the left card remains informative rather
                # than leaving a large blank area beneath a single bullet.
                gaps=[m for m in matches if m.get("Type")=="Mandatory" and m.get("Match Status")=="Gap"]
                strengths=[m for m in matches if m.get("Match Status")=="Match"]
                gap_items="".join([f"<li>🔴 {safe(x.get('Requirement',''))[:230]}</li>" for x in gaps[:5]])
                if not gap_items:
                    gap_items=(
                        "<li>No mandatory capability gaps identified.</li>"
                        f"<li><b>Mandatory compliance:</b> {met} of {mt} requirements met.</li>"
                        f"<li><b>High-severity risks:</b> {hr} identified.</li>"
                    )
                strength_items="".join([f"<li>🟢 {safe(x.get('Requirement',''))[:230]}</li>" for x in strengths[:5]])
                if not strength_items:
                    strength_items="<li>No full capability matches found for the current profile.</li>"
                st.markdown(
                    f"<div class='rfp-insight-grid'>"
                    f"<section class='rfp-panel rfp-risk rfp-insight-card'>"
                    f"<div class='rfp-insight-heading'><h3>⚠ &nbsp; Fatal Deal-Breakers (Why No-Bid?)</h3>"
                    f"<span class='rfp-insight-count'>{len(gaps)} gaps</span></div>"
                    f"<ul>{gap_items}</ul></section>"
                    f"<section class='rfp-panel rfp-strength rfp-insight-card'>"
                    f"<div class='rfp-insight-heading'><h3>✓ &nbsp; Company Strengths (Why Bid?)</h3>"
                    f"<span class='rfp-insight-count'>{len(strengths)} matches</span></div>"
                    f"<ul>{strength_items}</ul></section></div>",
                    unsafe_allow_html=True
                )
                st.markdown("<div class='rfp-decision-shell'><h2>Final Bid Decision</h2><p class='rfp-decision-help'>Select the authorised reviewer's decision and enter a reason. The decision is saved to the opportunity database.</p></div>", unsafe_allow_html=True)
                decision=st.radio(
                    "Final decision",
                    ["Pending human review","Bid","No-Bid","Hold for clarification"],
                    index=["Pending human review","Bid","No-Bid","Hold for clarification"].index(st.session_state["human_decision"]),
                    horizontal=True,
                    key="human_decision_radio",
                )
                notes=st.text_area(
                    "Decision justification / reviewer notes",
                    value=st.session_state.get("decision_notes",""),
                    height=112,
                    key="decision_notes_text",
                    placeholder="Enter the reason for this decision...",
                )
                st.markdown("<div class='rfp-decision-help'>A justification is required. Pending human review cannot be confirmed.</div>", unsafe_allow_html=True)
                if st.button("✓  Save & Confirm Decision", type="primary", use_container_width=True, key="dashboard_save_decision"):
                    confirm_human_decision(decision,notes)
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
        st.markdown("<div class='rfp-decision-shell'><h2>Final Bid Decision</h2><p class='rfp-decision-help'>Choose the final human decision and record the reason before saving.</p></div>", unsafe_allow_html=True)
        decision=st.radio(
            "Record final decision",
            ["Pending human review","Bid","No-Bid","Hold for clarification"],
            index=["Pending human review","Bid","No-Bid","Hold for clarification"].index(st.session_state["human_decision"]),
            horizontal=True,
            key="human_decision_radio",
        )
        notes=st.text_area(
            "Decision justification / reviewer notes",
            value=st.session_state.get("decision_notes",""),
            height=125,
            key="decision_notes_text",
            placeholder="Enter the reason for this decision...",
        )
        st.markdown("<div class='rfp-decision-help'>A justification is required. Pending human review cannot be confirmed.</div>", unsafe_allow_html=True)
        if st.button("✓  Save & Confirm Decision", type="primary", use_container_width=True, key="centre_save_decision"):
            confirm_human_decision(decision,notes)
        if decision=="Bid": st.success("Bid selected. Proposal support is unlocked after the decision is saved.")
        elif decision=="No-Bid": st.error("No-Bid selected. The opportunity will be marked as declined when saved.")
        elif decision=="Hold for clarification": st.warning("The opportunity will remain on hold when saved.")
        else: st.warning("Decision is awaiting final human review.")
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
