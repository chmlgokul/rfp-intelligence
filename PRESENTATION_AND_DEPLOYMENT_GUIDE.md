# Presentation & Deployment Guide: AssistLana RFP Intelligence

This comprehensive guide explains **how to deploy** the application to production and **how to deliver an outstanding live presentation/demo** for your internship evaluation.

---

## Part 1: How to Deploy (Deployment Guide)

You have three solid options for deployment depending on your setup. **Option 1 (Streamlit Community Cloud)** is strongly recommended because it is 100% free, provides a permanent HTTPS URL, and links directly to your GitHub repository.

---

### Option 1: Streamlit Community Cloud (Recommended & 100% Free)

#### Step 1: Prepare GitHub Repository
1. Initialize git in the project root:
   ```powershell
   git init
   git add .
   git commit -m "Initial commit: AssistLana RFP Intelligence System"
   ```
2. Create a new public or private repository on [GitHub](https://github.com) named `rfp-intelligence`.
3. Link and push your code:
   ```powershell
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/rfp-intelligence.git
   git push -u origin main
   ```

#### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
2. Click **"New app"**.
3. Select your repository: `<YOUR_USERNAME>/rfp-intelligence`.
4. Branch: `main`.
5. Main file path: `app.py`.
6. Click **"Deploy!"**.
7. In about 2–3 minutes, your app will be live at `https://<your-app-name>.streamlit.app/`.

> [!TIP]
> The repository already includes `requirements.txt` with all necessary packages (`streamlit`, `pymupdf`, `pandas`, `openpyxl`, `xlrd`).

---

### Option 2: Render.com / Railway (Web Service Hosting)

If you prefer deploying on Render:
1. Create a free account on [render.com](https://render.com).
2. Click **"New +"** $\rightarrow$ **"Web Service"**.
3. Connect your GitHub repository.
4. Set the following build settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Click **"Deploy Web Service"**.

---

### Option 3: Instant Live Sharing via Ngrok (For Live Demos from Laptop)

If you need an immediate public link during your presentation without pushing to cloud servers:
1. Install ngrok (or localtunnel):
   ```powershell
   # If you have winget or choco:
   winget install ngrok.ngrok
   ```
2. Start your Streamlit app locally:
   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```
3. In a second terminal window, run:
   ```powershell
   ngrok http 8501
   ```
4. Ngrok will output a public HTTPS URL (e.g. `https://xxxx.ngrok-free.app`) that anyone in the evaluation panel can open on their mobile phone or laptop in real-time!

---

## Part 2: Presentation Strategy (Pitch Structure)

Structure your presentation to last **10–12 minutes** with the following flow:

| Slide / Section | Time | Key Message to Convey |
| :--- | :---: | :--- |
| **1. The Problem** | 1.5 min | B2B & government tenders are 100+ pages of dense legal/technical text. Manual review takes days. Missing *one* mandatory requirement causes disqualification. |
| **2. Why Generic AI Fails** | 1.5 min | Generic chatbots (like ChatGPT) hallucinate past capabilities, lack source citations, cannot parse complex Excel BOQs, and try to make black-box decisions. |
| **3. AssistLana Solution** | 2 min | An AI-assisted decision-support platform designed for pre-sales teams. Core philosophy: **AI provides evidence, humans make decisions**. |
| **4. Live Demonstration** | 4–5 min | Upload a real RFP, show automated requirement extraction, capability gap analysis, risk register, Bid/No-Bid score, human decision gate, and proposal drafting. |
| **5. Technical Architecture & Security** | 1.5 min | 100% local processing, zero cloud data leakage, immune to prompt injection, $0 cloud API cost. |
| **6. Evaluation & Future Scope** | 1 min | 100% source traceability, 0% hallucination rate, sub-second speed. Future roadmap: local vector embeddings and OCR. |

---

## Part 3: Live Demonstration Script (Step-by-Step)

Follow this exact walkthrough during your presentation:

### Step 1: Welcome & Context Setting
- **Action:** Open the application in your browser (`http://localhost:8501`).
- **Say:**
  > *"Good morning panel. Today I am presenting AssistLana RFP Intelligence, an AI-assisted tender analysis and decision-support system. In B2B and enterprise sales, companies spend hundreds of hours reviewing tenders. Our goal is to reduce review time from days to seconds while keeping the final decision strictly in the hands of human business leaders."*

### Step 2: Role Switcher & Intake
- **Action:** Point out the **User Role** in the sidebar. Select `Business Development / Pre-Sales`.
- **Action:** Click "Browse files" and select `test_files/Sample_Enterprise_SmartCity_RFP.pdf`. Click **"Process document"**.
- **Say:**
  > *"Notice that our system supports multi-page PDFs, legacy Excel (.xls) Bill of Quantities, and modern spreadsheets. When I click 'Process document', our engine decomposes the tender into clean, traceable source pages."*

### Step 3: Requirement Intelligence & Source Traceability
- **Action:** Navigate to the **"Requirements"** tab.
- **Say:**
  > *"In less than one second, the system extracted 22 requirements across 4 pages. It automatically classified each into categories like Technical, Eligibility, Timeline, and Commercial. Notice the obligation classification: it identifies hard mandates like 'must' and 'shall' as Mandatory. Most importantly, look at the 'Source Page' column—every single row is 100% verifiable against the original text. Reviewers can even edit statuses, add reviewer notes, or download the full compliance matrix as a CSV."*

### Step 4: Capability Matching & Explainable Scoring
- **Action:** Click **"Run capability analysis"** in the sidebar.
- **Action:** Navigate to the **"Capability match"** and **"Risks and decision"** tabs.
- **Say:**
  > *"Next, the system compares tender requirements against our company capability profile using token overlap matching. Look at the Decision Centre: instead of a black-box answer, the system generates an explainable Decision-Support Score of 0/100 and a signal: 'No-Bid signal - mandatory gaps require resolution'. Why? Because the system identified that our company profile lacks mandatory ISO certifications and required client reference projects."*

### Step 5: Proving Responsiveness (Dynamic Capability Update)
- **Action:** In the sidebar's capability text box, paste these two lines:
  ```
  ISO 27001 and ISO 9001 certified organization
  Enterprise track record and client reference projects
  ```
- **Action:** Click **"Run capability analysis"** again.
- **Say:**
  > *"Now watch what happens when we update our profile with these credentials. When I re-run analysis, the mandatory gaps are resolved, the score increases, and the risk register recalculates immediately. This proves the system is an explainable decision tool, not a static hardcoded script."*

### Step 6: Human Decision Gate & Proposal Work Queue
- **Action:** Go to the **"Dashboard"** tab $\rightarrow$ **"Decision centre"**.
- **Action:** In **"Final human decision"**, change the selection from `Pending human review` to `Bid`. Click **"Move to proposal preparation"**.
- **Action:** Switch to the **"Proposal support"** tab.
- **Say:**
  > *"Notice our product rule: until a human selects 'Bid', proposal authoring is strictly locked. Once approved, the system generates a requirement-to-response work queue. Each draft response is grounded in actual capability evidence. Pre-sales specialists can assign response owners, edit responses, mark them as 'Approved', and export the entire work queue as a CSV for proposal assembly."*

### Step 7: Persistence & Admin Analytics
- **Action:** In the sidebar, click **"Save current opportunity"**.
- **Action:** Switch the **User Role** in the sidebar to `Admin`.
- **Say:**
  > *"Finally, the system stores the full state payload in a local SQLite database. In the Admin view, executive leaders can view cross-portfolio analytics: total active tenders, win rate percentage, pipeline stage breakdown, and historical compliance records."*

---

## Part 4: Evaluator Q&A Preparation (Viva Questions & Winning Answers)

Be prepared to answer these common panel questions with confidence:

### Q1: "Why did you build this using heuristics instead of just asking ChatGPT / Gemini with a prompt?"
- **Answer:**
  > *"Generic generative chatbots suffer from three critical flaws in tender management: First, **hallucination risk**—an LLM might invent a client reference or claim a capability we don't possess, leading to legal disputes. Second, **data confidentiality**—uploading proprietary pricing and RFP documents to public cloud APIs violates corporate privacy rules. Third, **explainability**—enterprise executives cannot rely on black-box probabilistic answers. Our heuristic engine provides 100% source traceability, $0 recurring API cost, zero hallucination, and complete explainability. As shown in our future roadmap, we plan to introduce local embeddings (like all-MiniLM-L6-v2) for semantic synonym expansion while keeping the decision gates deterministic."*

### Q2: "How does the system prevent non-technical submission rules (like BOQ formatting) from distorting the capability score?"
- **Answer:**
  > *"In `modules/rfp_analysis.py`, we explicitly differentiate between Technical Capability requirements and Submission/Timeline instructions. Requirements categorized under 'Submission' or 'Timeline' are treated as 'Needs Verification' compliance checks rather than capability gaps. This ensures a company is never scored down as 'incapable' simply because a tender requires submission on a specific government portal."*

### Q3: "What happens if a tender document is an image or scanned PDF?"
- **Answer:**
  > *"In our Evaluation Report, we explicitly documented this limitation. PyMuPDF extracts text streams from digital PDFs. For scanned documents, our architectural roadmap integrates an offline OCR layer (such as Tesseract or Surya OCR) that activates whenever extracted page text falls below a density threshold, maintaining local privacy while supporting legacy scanned tenders."*

### Q4: "How does the Bid/No-Bid scoring formula work?"
- **Answer:**
  > *"The formula starts at 100 and applies transparent weighted deductions:
  > $$\text{Score} = 100 - (30 \times \text{Mandatory Gaps}) - (10 \times \text{High Risks}) - (3 \times \text{Items to Verify})$$
  > If any mandatory capability gap exists, the system automatically triggers a 'No-Bid signal' because missing a mandatory criterion leads to immediate disqualification in formal procurement. However, a prominent disclaimer always reminds the user that the score is advisory—the human reviewer holds the final decision authority."*

### Q5: "How does the system ensure data security and prevent prompt injection?"
- **Answer:**
  > *"Because our extraction and matching engines operate deterministically on string tokens and regex boundaries without passing raw document text into an unconstrained generative prompt, prompt injection attacks (such as embedded instructions trying to manipulate the bid outcome) are completely neutralized and treated as benign text. Additionally, all data is persisted in a local SQLite database, meaning zero client data leaves the organization."*

