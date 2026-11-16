# Test Cases: AssistLana RFP Intelligence

## 1. Test Suite Overview

The AssistLana test framework includes both automated pytest regression tests and structured functional test scenarios covering document intake, classification, capability matching, risk evaluation, decision locking, proposal drafting, and database persistence.

### Running Automated Test Suite:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

---

## 2. Test Cases Specification Matrix

| Test ID | Test Category | Scenario Description | Test Input / Preconditions | Step-by-Step Procedure | Expected Result | Status |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-01** | **Ingestion** | Ingest readable PDF document | `Sample_Enterprise_SmartCity_RFP.pdf` (4 pages) | 1. Upload PDF in sidebar.<br/>2. Click "Process document". | Extracted pages count = 4; page numbers mapped accurately; text clean. | **PASS** |
| **TC-02** | **Ingestion** | Ingest legacy `.xls` tender spreadsheet | `BOQ_979798.xls` | 1. Upload XLS in sidebar.<br/>2. Click "Process document". | Worksheets extracted via xlrd; tagged as `Sheet 1: ...`; no binary crash. | **PASS** |
| **TC-03** | **Ingestion** | Disguised HTML table with `.xls` suffix | Synthetic HTML file saved with `.xls` extension | 1. Upload disguised HTML file.<br/>2. Process document. | HTML table fallback parser extracts table rows without exception. | **PASS** |
| **TC-04** | **Extraction** | Obligation type classification | Sentences with *"must"*, *"shall"*, *"may"*, *"preferably"* | 1. Parse document containing diverse obligation verbs. | Mandatory patterns tagged `Mandatory`; permissive patterns tagged `Optional`. | **PASS** |
| **TC-05** | **Extraction** | Multi-category classification | Sentence with technical & submission keywords | 1. Parse requirement with multiple category markers. | Multiple categories assigned (e.g. `Technical, Submission`); ordered. | **PASS** |
| **TC-06** | **Extraction** | Submission deadline detection | Sentence: *"Submission deadline: 15 December 2026"* | 1. Extract requirements.<br/>2. Inspect `Deadline` column. | String `"15 December 2026"` populated in Deadline field; context validated. | **PASS** |
| **TC-07** | **Matching** | Exact capability matching | Requirement: *"Cloud deployment and infrastructure"* with exact capability | 1. Run capability analysis with default profile. | `Match Status` = `Match`; `Match Score` $\ge 67\%$; Evidence cited. | **PASS** |
| **TC-08** | **Matching** | Mandatory capability gap detection | Requirement: *"Must possess ISO 27001"* with capability lacking ISO | 1. Run capability analysis without ISO in profile. | `Match Status` = `Gap`; Evidence = `"No matching capability provided"`. | **PASS** |
| **TC-09** | **Matching** | BOQ submission non-penalty rule | Mandatory requirement in `Submission` category | 1. Run matching with missing capability. | `Match Status` = `Needs Verification` (NOT `Gap`); score not unfairly penalized. | **PASS** |
| **TC-10** | **Risk Engine** | High-risk penalty clause identification | Liquidated damages clause: *"1% penalty per week"* | 1. Inspect generated Risk Register. | Risk item created; `Risk Level` = `High`; Actionable mitigation suggested. | **PASS** |
| **TC-11** | **Decision Gate** | Explainable Bid/No-Bid scoring formula | Opportunity with 1 mandatory gap and 2 high risks | 1. Run analysis.<br/>2. Inspect decision center. | Score = $100 - (30 \times 1) - (10 \times 2) = 50$; Signal = `"No-Bid signal..."`. | **PASS** |
| **TC-12** | **Governance** | Human decision override & locking | Opportunity under review | 1. Select `No-Bid` in Decision Centre.<br/>2. Navigate to Proposal tab. | Decision saved; Proposal tab displays lock banner: `"Proposal preparation is locked..."`. | **PASS** |
| **TC-13** | **Proposal** | Proposal generation on Bid approval | Opportunity where human selects `Bid` | 1. Record decision as `Bid`.<br/>2. Move to Proposal tab. | Work queue unlocked; draft responses populated; status defaults to `Not Reviewed`. | **PASS** |
| **TC-14** | **Persistence** | SQLite save and reload round-trip | Fully analyzed opportunity | 1. Click "Save current opportunity".<br/>2. Clear session.<br/>3. Load saved opportunity from picker. | All requirements, matches, risks, decisions, and proposal state restored identically. | **PASS** |
| **TC-15** | **Role Control** | Admin vs. Pre-Sales persona toggle | Active application session | 1. Switch sidebar role to `Admin`. | Admin & Portfolio Analytics view displayed; portfolio aggregates visible. | **PASS** |

---

## 3. Automated Regression Tests (`pytest`)

The automated unit test suite covers core internal logic and guarantees zero regressions:

```
tests/test_app.py::test_app_starts_without_exception PASSED
tests/test_app.py::test_app_admin_role_switch PASSED
tests/test_opportunity_storage.py::test_opportunity_round_trip PASSED
tests/test_pdf_processor.py::test_extract_pdf_text_returns_one_record_per_page PASSED
tests/test_pdf_processor.py::test_extract_pdf_text_strips_page_text PASSED
tests/test_pdf_processor.py::test_extract_pdf_text_raises_for_missing_file PASSED
tests/test_requirement_extractor.py::test_extract_requirements_identifies_deadlines_and_categories PASSED
tests/test_requirement_extractor.py::test_extract_deadline_formats PASSED
tests/test_rfp_analysis.py::test_capability_matching_and_risk_register_are_explainable PASSED
tests/test_rfp_analysis.py::test_recommendation_and_review_queues_keep_human_in_control PASSED
tests/test_rfp_analysis.py::test_submission_instruction_is_not_counted_as_capability_gap PASSED
tests/test_spreadsheet_processor.py::test_extract_spreadsheet_text_from_xls PASSED
tests/test_spreadsheet_processor.py::test_extract_spreadsheet_text_from_html_table PASSED

============================= 13 passed in 4.12s =============================
```
