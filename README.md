# AssistLana RFP Intelligence

**AssistLana RFP Intelligence** is an AI-assisted tender decision and proposal system built for Pre-Sales and Business Development teams. It ingests multi-hundred-page RFPs in PDF and Excel formats, extracts source-grounded compliance requirements, compares them against company capabilities, surfaces potential risks and penalties, and generates an explainable Bid / No-Bid signal—keeping the final decision strictly in human hands.

---

## Quickstart: Run Locally

### 1. Launch the Application
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 2. Run Automated Regression Suite
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```
All 13 automated unit tests will execute and pass.

---

## Key Features & Highlights

- **Multi-Format Ingestion:** Native parsing of modern PDFs, modern Excel (`.xlsx`), legacy compound workbooks (`.xls`), and portal-exported HTML tables.
- **Requirement Intelligence:** Automatically categorizes clauses into 9 operational categories (`Technical`, `Eligibility`, `Certification`, `Experience`, `Submission`, `Timeline`, `Commercial`, `Compliance`, `Risk`), isolates `Mandatory` vs `Optional` obligations, and extracts submission deadlines.
- **Explainable Bid / No-Bid Scoring:** Mathematical deduction scoring formula with explicit disclaimers:
  $$\text{Score} = 100 - (30 \times \text{Mandatory Gaps}) - (10 \times \text{High Risks}) - (3 \times \text{Items to Verify})$$
- **Strict Human-in-the-Loop Governance:** Proposal drafting remains strictly locked until an authorized human reviewer records a `Bid` decision.
- **Zero Hallucination & 100% Traceability:** Every requirement, match, and risk links directly to its source page or sheet number. Immune to document prompt injections.
- **Dual User Roles:** Seamless persona toggle between **Business Development / Pre-Sales** and **Admin / Executive Oversight** (with cross-portfolio analytics & win-rate metrics).
- **Persistent Local Database:** Complete opportunity payloads are saved locally in SQLite (`rfp_intelligence.db`).

---

## Deliverables & Documentation Index

In full alignment with the internship assignment brief, all 7 required deliverables are documented:

| No. | Deliverable | Documentation File | Description |
| :---: | :--- | :--- | :--- |
| **1** | **Research Document** | [RESEARCH_DOCUMENT.md](./RESEARCH_DOCUMENT.md) | RFP lifecycle, Bid/No-Bid methodology, RAG vs Heuristics, and competitive benchmark of Loopio, Responsive, and AutoRFP.ai. |
| **2** | **Product Requirements & Workflow** | [PRODUCT_WORKFLOW.md](./PRODUCT_WORKFLOW.md) | 9-stage lifecycle, user roles, functional modules A–I, and dashboard KPI justifications. |
| **3** | **Working MVP** | [app.py](./app.py) & [modules/](./modules/) | Fully functional Streamlit MVP with modular processors, interactive editors, and SQLite storage. |
| **4** | **AI Evaluation Report** | [EVALUATION_REPORT.md](./EVALUATION_REPORT.md) | Quantitative accuracy/recall benchmarks, sample RFP evaluations, hallucination safety audit, and limitations. |
| **5** | **Test Cases** | [TEST_CASES.md](./TEST_CASES.md) | Structured test matrix (TC-01 through TC-15) and automated pytest test suite documentation. |
| **6** | **Technical Documentation** | [TECHNICAL_DOCUMENTATION.md](./TECHNICAL_DOCUMENTATION.md) | Architecture diagram (Mermaid), data models, security/prompt injection posture, and $0 tech stack justification. |
| **7** | **Presentation & Deployment Guide** | [PRESENTATION_AND_DEPLOYMENT_GUIDE.md](./PRESENTATION_AND_DEPLOYMENT_GUIDE.md) | Free 1-click Streamlit Cloud deployment guide, pitch deck outline, live demo script, and evaluator Q&A prep. |

---

## Sample Test Files

Pre-configured sample files are available in `test_files/` for immediate testing and demonstration:
- `test_files/Sample_Enterprise_SmartCity_RFP.pdf` – 4-page realistic municipal Smart City RFP with eligibility, ISO certifications, technical specs, penalties, and deadlines.
- `test_files/BOQ_979798.xls` – Real-world public sector Bill of Quantities workbook.
