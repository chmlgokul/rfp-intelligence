# Product Requirements & Workflow Document: AssistLana RFP Intelligence

## 1. Product Vision & Principles

**AssistLana RFP Intelligence** is an enterprise decision-support tool designed for Business Development (BD) and Pre-Sales teams. Its mission is to transform dense, unstructured tender documents into actionable intelligence, accelerate Bid / No-Bid decisions, eliminate compliance oversights, and scaffold proposal authoring—while keeping full governance in the hands of human business leaders.

### Core Product Principles:
- **Decision Support, Not Decision Automation:** AI provides explainable scores, gap analysis, and risk signals. It never accepts or rejects a tender automatically.
- **Traceability by Design:** Every extracted requirement, deadline, and risk is permanently mapped back to its source page or spreadsheet worksheet.
- **Human-in-the-Loop Review Gates:** AI outputs start as drafts (`Pending Review`, `Not Reviewed`). Human validation is mandatory before proceeding to downstream stages.
- **Strict Proposal Lock:** Proposal preparation is unlocked only when an authorized human explicitly records a `Bid` decision.

---

## 2. User Roles & Permissions

In accordance with enterprise procurement workflows, the product supports two primary roles:

### Role 1: Business Development / Pre-Sales Specialist
- **Core Goal:** Fast-track opportunity qualification, assess technical/commercial feasibility, and coordinate bid response.
- **Key Capabilities:**
  - Upload tender documents in PDF and Excel formats.
  - Review and edit extracted requirements, obligation types, and deadlines.
  - Run capability matching against current organizational profiles.
  - Review the Risk Register and draft clarification questions.
  - Record the final commercial decision: `Bid`, `No-Bid`, or `Hold for clarification`.
  - Author and approve requirement-level proposal drafts when bidding.
  - Save opportunities to the persistent database and track their lifecycle stage.

### Role 2: Admin / Executive Oversight
- **Core Goal:** Govern organizational capabilities, monitor portfolio health, and track win/loss analytics.
- **Key Capabilities:**
  - Manage and curate the company master capability profile.
  - Access executive portfolio analytics across all active and historical RFPs.
  - Monitor aggregate metrics: Total pipeline, Won/Lost ratio, Win rate (%), and pending reviews.
  - Audit requirement compliance matrices and historical decisions.

---

## 3. End-to-End 9-Stage Workflow

The system operationalizes the 9-stage lifecycle defined in the project specification:

```
[Stage 1: Intake] ──> [Stage 2: Understanding] ──> [Stage 3: Requirements]
                                                          │
[Stage 6: Bid Decision] <── [Stage 5: Gaps & Risks] <── [Stage 4: Matching]
       │
[Stage 7: Human Gate] ──> [Stage 8: Proposal Drafts] ──> [Stage 9: Lifecycle Tracking]
```

### Stage-by-Stage Breakdown:

| Stage | Name | System Responsibility | User Action |
| :---: | :--- | :--- | :--- |
| **1** | **RFP Intake** | Ingest PDF, XLS, XLSX, and portal exports; validate file integrity; strip text cleanly. | Upload tender file from sidebar. |
| **2** | **Document Understanding** | Partition document into traceable source pages or worksheets. | Inspect source text in the collapsible preview. |
| **3** | **Requirement Extraction & Classification** | Filter actionable sentences; classify into 9 categories (Technical, Eligibility, Timeline, etc.); detect obligation type (`Mandatory` vs. `Optional`); extract deadlines. | Edit extracted fields in interactive grid; update status (`Verified`, `Needs Clarification`). |
| **4** | **Company Capability Comparison** | Perform token-overlap matching between requirements and company capabilities; compute match score (0–100%) and evidence. | Adjust company capability profile; trigger analysis. |
| **5** | **Gap & Risk Identification** | Generate comprehensive Risk Register; surface mandatory gaps, ambiguous clauses, and high-risk terms; draft clarification queries. | Review risks by severity (`High`, `Medium`); assign mitigations. |
| **6** | **Bid / No-Bid Intelligence** | Compute explainable score (0–100) and recommendation signal based on gaps, risks, and verification items. | Review signal and mathematical deduction. |
| **7** | **Human Review & Decision Gate** | Display warning banners and disclaimers enforcing human agency. | Formally record decision (`Bid`, `No-Bid`, or `Hold`). |
| **8** | **Proposal Preparation Support** | If `Bid`, generate requirement-to-response work queue with draft answers, ownership fields, and approval toggles. | Assign response owners, edit responses, and set status to `Approved`. |
| **9** | **Opportunity Tracking** | Persist full opportunity payload to SQLite; update stage (`New → Analysis → Review → Bid Decision → Proposal → Submitted → Won/Lost`). | Advance stage dropdown and click Save. |

---

## 4. Core Functional Modules (A through I)

- **A. RFP Intake:** Multi-format parser handling PDFs and workbooks (including legacy OLE `.xls` and HTML table disguises).
- **B. Requirement Intelligence:** Rule-grounded classification across 9 categories; regex extraction of standard Indian and international date formats.
- **C. Company Capability Matching:** Transparent keyword-token overlap scoring; avoids black-box uncertainty.
- **D. Compliance Matrix:** Full tabular matrix with editable `Type`, `Review Status`, `Evidence`, and `Reviewer Notes`. CSV export enabled.
- **E. Risk Analysis:** Multi-factor risk engine covering technical gaps, timeline pressures, and liquidated damages penalties.
- **F. Bid / No-Bid Intelligence:** Explainable additive/subtractive scoring formula; disclaimers preventing automated decisioning.
- **G. Clarification Support:** Automatic draft generation of vendor clarification queries for ambiguous clauses.
- **H. Proposal Support:** Role-gated work queue with starter response templates, owner assignments, and human approval tracking.
- **I. Opportunity Tracking:** Local SQLite database storing the full state payload, stage history, and last-updated timestamps.

---

## 5. Dashboard Metrics & Business Justification

| Metric | Business Value & Justification |
| :--- | :--- |
| **RFP Pages / Sheets** | Indicates document complexity and review workload required. |
| **Total Requirements** | Quantifies total compliance scope to be covered in the bid. |
| **Mandatory Count** | Surfaces the non-negotiable clauses that could cause disqualification. |
| **Deadlines Identified** | Highlights immediate submission and clarification cutoff risks. |
| **Open Risks** | Highlights exposure to penalties, resource shortages, and legal liabilities. |
| **Decision-Support Score** | Summarizes feasibility into a clear, explainable 0–100 index. |
| **Portfolio Win Rate (%)** | Tracks team commercial effectiveness and informs future Bid/No-Bid thresholds. |
