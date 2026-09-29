# Product Requirements Document (PRD)
## Mutual Fund FAQ Assistant — Facts-Only Q&A RAG Bot

| Field | Value |
|---|---|
| **Product Name** | MF FAQ Assistant (RAG Bot) |
| **Version** | 1.0 (Working Prototype) |
| **Date** | 2026-09-29 |
| **Status** | Draft |
| **Author** | RAG Bot Team |

---

## 1. Problem Statement

Retail mutual fund investors and support/content teams need quick, accurate answers to repetitive factual questions about mutual fund schemes — such as expense ratio, exit load, minimum SIP, lock-in periods (ELSS), riskometer, benchmark, and how to download statements. Currently, users must navigate multiple official pages (AMC, SEBI, AMFI) to find this information, which is time-consuming and error-prone.

There is no lightweight, facts-only assistant that pulls exclusively from official public sources and provides a citation link with every answer.

---

## 2. Goals & Objectives

### 2.1 Primary Goal
Build a small FAQ assistant that answers factual queries about mutual fund schemes using **only official public pages**, with **one source link per answer**.

### 2.2 Secondary Goals
- Refuse opinionated/portfolio advice questions politely with an educational link.
- Keep answers concise (≤3 sentences) with a "Last updated from sources" note.
- Provide a tiny, focused UI with example questions and a clear disclaimer.

### 2.3 Non-Goals
- No investment advice or portfolio recommendations.
- No performance claims or return computations.
- No user accounts, PII storage, or authentication.
- No third-party blogs or unofficial sources.

---

## 3. Target Users

| User Type | Use Case |
|---|---|
| **Retail investors** | Comparing schemes; looking up fees, lock-in, minimums, statements |
| **Support / Content teams** | Answering repetitive MF questions quickly with verified sources |

---

## 4. Scope

### 4.1 In-Scope
- **Corpus**: One AMC (HDFC Mutual Fund) and 3–5 schemes under it:
  - HDFC Flexi Cap Fund (Direct)
  - HDFC Small Cap Fund (Direct)
  - HDFC ELSS Tax Saver Fund (Direct)
- **15 public pages** from AMC/SEBI/AMFI (factsheets, KIM/SID, scheme FAQs, fee/charges pages, riskometer/benchmark notes, statement/tax-doc guides).
- **Facts-only Q&A** covering: expense ratio, exit load, minimum SIP, ELSS lock-in, riskometer, benchmark, statement downloads.
- **Citation**: Every answer includes one clear source link.
- **Refusal handling**: Polite, facts-only message + relevant educational link for advice questions.
- **Tiny UI**: Welcome line + 3 example questions + "Facts-only. No investment advice." note.

### 4.2 Out-of-Scope
- Performance/return comparisons or computations.
- Multi-AMC coverage (future phase).
- User accounts, PII, or any personal data storage.
- Screenshots of app back-end.
- Third-party blogs as sources.

---

## 5. Source Corpus (15 Public Pages)

| # | Type | URL |
|---|---|---|
| 1 | Scheme page: Flexi Cap Direct | https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/direct |
| 2 | Scheme page: Small Cap Direct | https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct |
| 3 | Scheme page: ELSS Tax Saver Direct | https://www.hdfcfund.com/explore/mutual-funds/hdfc-elss-tax-saver-fund/direct |
| 4 | ELSS overview (lock-in, 80C) | https://www.hdfcfund.com/product-solutions/overview/hdfc-elss-tax-saver/direct |
| 5 | Factsheets | https://www.hdfcfund.com/mutual-funds/factsheets |
| 6 | KIM (all schemes) | https://www.hdfcfund.com/investor-services/fund-documents/kim |
| 7 | SID (all schemes) | https://www.hdfcfund.com/investor-services/fund-documents/sid |
| 8 | TER / expense ratio reports | https://www.hdfcfund.com/statutory-disclosure/total-expense-ratio-of-mutual-fund-schemes/reports |
| 9 | Request account/capital gains statement | https://www.hdfcfund.com/services/additional-info/request-statement |
| 10 | Consolidated Account Statement guide | https://www.hdfcfund.com/services/consolidated-account-statement |
| 11 | Capital gain statement guide | https://www.hdfcfund.com/learn/blog/how-get-capital-gain-statement-mutual-fund-schemes-india |
| 12 | Online services for investors (WhatsApp/online) | https://www.hdfcfund.com/information/online-services-investors |
| 13 | AMFI Riskometer | https://www.amfiindia.com/online-center/risk-o-meter |
| 14 | AMFI Investor Corner | https://www.amfiindia.com/investor |
| 15 | SEBI Mutual Funds page | https://www.sebi.gov.in/sebiweb/other/mutualfunds.jsp |
| 16 | SEBI investor education: mutual funds | https://www.sebi.gov.in/sebi_data/commondocs/siep_h.html |

---

## 6. Functional Requirements

### 6.1 FAQ Answering
- **FR-1**: The system shall answer factual queries about mutual fund schemes (expense ratio, exit load, minimum SIP, ELSS lock-in, riskometer, benchmark, statement downloads).
- **FR-2**: Every answer shall include **one clear citation link** to the source page.
- **FR-3**: Answers shall be **≤3 sentences** in length.
- **FR-4**: Each answer shall include a "Last updated from sources:" note with the source URL.

### 6.2 Refusal Handling
- **FR-5**: The system shall detect opinionated/portfolio advice questions (e.g., "Should I buy/sell?", "Which fund is best?").
- **FR-6**: For advice questions, the system shall respond with a polite, facts-only message and a relevant educational link (e.g., SEBI investor education page).

### 6.3 UI Requirements
- **FR-7**: The UI shall display a welcome line.
- **FR-8**: The UI shall show **3 example questions** as clickable suggestions.
- **FR-9**: The UI shall display the note: **"Facts-only. No investment advice."**
- **FR-10**: The UI shall be minimal — no complex navigation or settings.

---

## 7. Non-Functional Requirements

| ID | Requirement |
|---|---|
| **NFR-1** | **Public sources only** — no screenshots of app back-end; no third-party blogs as sources. |
| **NFR-2** | **No PII** — the system shall not accept or store PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers. |
| **NFR-3** | **No performance claims** — the system shall not compute or compare returns; it shall link to the official factsheet if asked. |
| **NFR-4** | **Clarity & transparency** — answers ≤3 sentences; "Last updated from sources:" note on every answer. |
| **NFR-5** | **Response time** — answers should be returned in ≤5 seconds. |
| **NFR-6** | **Availability** — prototype should be accessible via app link, notebook, or demo video. |

---

## 8. RAG Architecture

The system follows a full **Retrieval-Augmented Generation (RAG)** pipeline with distinct stages for data ingestion and data retrieval.

### 8.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RAG PIPELINE                                 │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  STAGE 1: DATA INGESTION                       │  │
│  │                                                               │  │
│  │  ┌──────────┐   ┌───────────┐   ┌───────────┐   ┌─────────┐ │  │
│  │  │ LOADING  │──▶│ CHUNKING  │──▶│ EMBEDDING │──▶│  STORE  │ │  │
│  │  │          │   │           │   │           │   │ VECTOR  │ │  │
│  │  │ 15 URLs  │   │ Split +   │   │ all-Mini  │   │  DATA   │ │  │
│  │  │ (HTML/   │   │ overlap   │   │ LM-L6-v2  │   │ ChromaDB│ │  │
│  │  │  PDF)    │   │           │   │           │   │         │ │  │
│  │  └──────────┘   └───────────┘   └───────────┘   └─────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  STAGE 2: DATA RETRIEVAL                      │  │
│  │                                                               │  │
│  │  ┌──────────┐   ┌───────────┐   ┌───────────┐   ┌─────────┐ │  │
│  │  │  USER    │──▶│  QUERY    │──▶│  SEARCH   │──▶│ RANK &  │ │  │
│  │  │  QUERY   │   │ EMBEDDING │   │ ChromaDB  │   │ CONTEXT │ │  │
│  │  │          │   │ (same     │   │ (top-k    │   │ BUILD   │ │  │
│  │  │          │   │  model)   │   │  chunks)  │   │         │ │  │
│  │  └──────────┘   └───────────┘   └───────────┘   └─────────┘ │  │
│  │                                                        │      │  │
│  │                                                        ▼      │  │
│  │                                               ┌──────────────┐ │  │
│  │                                               │  LLM GENERATION│ │  │
│  │                                               │  (answer +    │ │  │
│  │                                               │   citation)   │ │  │
│  │                                               └──────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Stage 1: Data Ingestion

#### 8.2.1 Loading
- **Input**: 15–25 public URLs (HTML pages, PDF documents).
- **Sources**: AMC website (HDFC Fund), SEBI, AMFI.
- **Method**: Web scraping / fetching of public pages; PDF parsing for factsheets, KIM, SID documents.
- **Output**: Raw text content from each source page.

#### 8.2.2 Chunking
- **Strategy**: Split documents into smaller, semantically meaningful chunks.
- **Chunk size**: ~500–1000 tokens (tunable).
- **Overlap**: ~10–20% overlap between consecutive chunks to preserve context.
- **Chunk metadata**: Each chunk stores:
  - `source_url` — the original page URL (for citation).
  - `chunk_id` — unique identifier.
  - `document_type` — factsheet, KIM, SID, scheme page, etc.
  - `scheme_name` — associated scheme (if applicable).
- **Output**: List of text chunks with metadata.

#### 8.2.3 Embedding
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Method**: Generate dense vector embeddings for each chunk using the embedding model.
- **Output**: Vector embeddings (numpy arrays / lists) for each chunk.

#### 8.2.4 Store Vector Data
- **Vector Database**: **ChromaDB**
- **Collection**: `mutual_fund_faq`
- **Storage**: Each chunk stored with:
  - `id` — chunk ID
  - `embedding` — vector from all-MiniLM-L6-v2
  - `document` — chunk text
  - `metadata` — source_url, document_type, scheme_name, etc.
- **Persistence**: Local ChromaDB instance (file-based persistence for prototype).

### 8.3 Stage 2: Data Retrieval

#### 8.3.1 Query Embedding
- **Input**: User query (text).
- **Method**: Embed the query using the **same** `sentence-transformers/all-MiniLM-L6-v2` model.
- **Output**: Query vector (384-dim).

#### 8.3.2 Vector Search
- **Method**: Cosine similarity search in ChromaDB.
- **Top-k**: Retrieve top 3–5 most relevant chunks (tunable).
- **Output**: Ranked list of chunks with similarity scores.

#### 8.3.3 Context Building
- **Method**: Concatenate retrieved chunks into a context prompt.
- **Prompt structure**:
  - System prompt: "You are a facts-only mutual fund FAQ assistant. Answer using only the provided context. Include one source link. Keep answers to 3 sentences or fewer. If the question asks for investment advice, politely decline and provide an educational link."
  - Context: Retrieved chunks with source URLs.
  - User query: The original question.

#### 8.3.4 LLM Generation
- **Method**: Send the constructed prompt to an LLM (e.g., OpenAI GPT, or open-source alternative).
- **Output**: Generated answer with:
  - Concise factual answer (≤3 sentences).
  - One citation link from the retrieved context.
  - "Last updated from sources:" note.
  - Refusal message + educational link (if advice question detected).

---

## 9. Technology Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Vector Database** | ChromaDB |
| **LLM** | OpenAI API / open-source LLM (configurable) |
| **Web Scraping** | `requests` + `BeautifulSoup` / `selenium` (if JS-rendered) |
| **PDF Parsing** | `PyPDF2` / `pdfplumber` |
| **Chunking** | LangChain `RecursiveCharacterTextSplitter` (or custom) |
| **UI** | Streamlit / Gradio (tiny prototype) |
| **Orchestration** | LangChain / LlamaIndex (optional) |

---

## 10. Data Flow

```
1. INGESTION (one-time / periodic):
   URLs → Scrape/Parse → Raw Text → Chunk → Embed → ChromaDB

2. RETRIEVAL (per query):
   User Query → Embed → ChromaDB Search → Top-k Chunks → Context → LLM → Answer + Citation
```

---

## 11. Deliverables

| # | Deliverable | Description |
|---|---|---|
| 1 | **Working prototype** | App link (Streamlit/Gradio) or notebook; or ≤3-min demo video if hosting isn't possible |
| 2 | **Source list** | CSV/MD of the 15–25 URLs used |
| 3 | **README** | Setup steps, scope (AMC + schemes), known limits |
| 4 | **Sample Q&A file** | 5–10 queries with the assistant's answers + links |
| 5 | **Disclaimer snippet** | Facts-only, no advice disclaimer used in UI |

---

## 12. Sample Q&A

| Question | Expected Behavior |
|---|---|
| "What is the expense ratio of HDFC Flexi Cap Fund?" | Factual answer with TER report link |
| "What is the ELSS lock-in period?" | 3-year lock-in answer with ELSS overview link |
| "What is the minimum SIP amount?" | Factual answer with scheme page link |
| "What is the exit load for HDFC Small Cap Fund?" | Factual answer with scheme page/SID link |
| "How do I download my capital gains statement?" | Step-by-step answer with statement guide link |
| "What is the riskometer of HDFC Flexi Cap Fund?" | Risk level answer with AMFI riskometer link |
| "Should I buy HDFC Flexi Cap Fund?" | **Refusal** — polite decline + SEBI investor education link |
| "Which mutual fund is best for me?" | **Refusal** — polite decline + educational link |

---

## 13. Disclaimer Snippet (UI)

> **Facts-only. No investment advice.**
> This assistant provides factual information from official public sources only. It does not recommend, endorse, or advise on any mutual fund scheme or investment decision. Please consult a SEBI-registered investment advisor for personalized advice.

---

## 14. Known Limitations

| Limitation | Mitigation |
|---|---|
| Corpus limited to one AMC (HDFC) and 3 schemes | Future phase: expand to more AMCs/schemes |
| Static corpus — no real-time data refresh | Periodic re-ingestion pipeline (manual or scheduled) |
| No performance/return data | Link to official factsheet when asked |
| LLM may hallucinate if context is insufficient | Strict prompt engineering; fallback to "I don't have information on that" |
| PDF parsing accuracy for KIM/SID | Manual verification of parsed chunks |
| No multi-language support | English-only for prototype |

---

## 15. Success Criteria

| Criterion | Target |
|---|---|
| Answer accuracy (factual correctness) | ≥90% on sample Q&A |
| Citation presence | 100% of answers include a source link |
| Refusal accuracy | 100% of advice questions refused politely |
| Answer length | ≤3 sentences |
| Response time | ≤5 seconds |
| Corpus coverage | All 15 source pages ingested and searchable |

---

## 16. Future Enhancements (Post-Prototype)

- Expand corpus to multiple AMCs and 20+ schemes.
- Add periodic auto-refresh of corpus (cron/scheduled re-ingestion).
- Add multi-language support (Hindi, regional languages).
- Add feedback mechanism (thumbs up/down) to improve retrieval.
- Add conversation memory for follow-up questions.
- Deploy as a chatbot widget on AMC/SEBI educational pages.

---

*End of PRD*
