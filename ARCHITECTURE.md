# Architecture Document
## Mutual Fund FAQ Assistant — RAG Bot

| Field | Value |
|---|---|
| **Document** | Architecture Design |
| **Version** | 1.0 |
| **Date** | 2026-09-29 |
| **Status** | Draft |
| **References** | PRD.md |

---

## 1. System Overview

The MF FAQ Assistant is a **Retrieval-Augmented Generation (RAG)** system that answers factual mutual fund questions using only official public sources. The architecture is divided into two primary stages:

1. **Data Ingestion Pipeline** — Collects, processes, and stores source documents as vector embeddings.
2. **Data Retrieval Pipeline** — Handles user queries, retrieves relevant context, and generates cited answers.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM ARCHITECTURE                              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                   STAGE 1: DATA INGESTION                       │    │
│  │                                                                 │    │
│  │  ┌────────┐  ┌──────────┐  ┌───────────┐  ┌────────────────┐  │    │
│  │  │ LOAD   │─▶│ CHUNK    │─▶│ EMBED     │─▶│ STORE VECTORS  │  │    │
│  │  │        │  │          │  │           │  │                │  │    │
│  │  │ 15-25  │  │ Recursive│  │ all-Mini  │  │ ChromaDB       │  │    │
│  │  │ URLs   │  │ Character│  │ LM-L6-v2  │  │ (persistent)   │  │    │
│  │  │        │  │ Splitter │  │ 384-dim   │  │                │  │    │
│  │  └────────┘  └──────────┘  └───────────┘  └────────────────┘  │    │
│  │                                                                 │    │
│  │  Sources: HDFC Fund │ SEBI │ AMFI                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                        │
│                                ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                   STAGE 2: DATA RETRIEVAL                       │    │
│  │                                                                 │    │
│  │  ┌────────┐  ┌──────────┐  ┌───────────┐  ┌────────────────┐  │    │
│  │  │ USER   │─▶│ EMBED    │─▶│ SEARCH    │─▶│ BUILD CONTEXT  │  │    │
│  │  │ QUERY  │  │ QUERY    │  │ ChromaDB  │  │                │  │    │
│  │  │        │  │          │  │           │  │ Top-k chunks   │  │    │
│  │  │        │  │ same     │  │ cosine    │  │ + metadata     │  │    │
│  │  │        │  │ model    │  │ similarity│  │                │  │    │
│  │  └────────┘  └──────────┘  └───────────┘  └───────┬────────┘  │    │
│  │                                                    │           │    │
│  │                                                    ▼           │    │
│  │                                           ┌────────────────┐   │    │
│  │                                           │ LLM GENERATION │   │    │
│  │                                           │                │   │    │
│  │                                           │ Answer +       │   │    │
│  │                                           │ Citation +     │   │    │
│  │                                           │ Disclaimer     │   │    │
│  │                                           └────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                        │
│                                ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                          UI LAYER                               │    │
│  │  Streamlit / Gradio — Welcome + Examples + Disclaimer            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        COMPONENT VIEW                                    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    INGESTION MODULES                            │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │ URL Loader   │  │ PDF Parser   │  │ Text Cleaner         │  │    │
│  │  │              │  │              │  │                      │  │    │
│  │  │ requests +   │  │ pdfplumber / │  │ - strip whitespace   │  │    │
│  │  │ BeautifulSoup│  │ PyPDF2       │  │ - remove nav/footer  │  │    │
│  │  │              │  │              │  │ - normalize text     │  │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │    │
│  │         │                 │                      │              │    │
│  │         └─────────────────┼──────────────────────┘              │    │
│  │                           ▼                                     │    │
│  │                  ┌────────────────┐                             │    │
│  │                  │ Raw Text Store │                             │    │
│  │                  │ (in-memory /   │                             │    │
│  │                  │  temp files)   │                             │    │
│  │                  └───────┬────────┘                             │    │
│  │                          │                                      │    │
│  │                          ▼                                      │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │                    CHUNKER                                │   │    │
│  │  │  RecursiveCharacterTextSplitter                          │   │    │
│  │  │  - chunk_size: 500-1000 tokens                           │   │    │
│  │  │  - chunk_overlap: 10-20%                                 │   │    │
│  │  │  - separators: [\n\n, \n, ". ", " ", ""]                  │   │    │
│  │  │  - metadata: source_url, doc_type, scheme_name, chunk_id │   │    │
│  │  └──────────────────────────┬───────────────────────────────┘   │    │
│  │                             │                                   │    │
│  │                             ▼                                   │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │                   EMBEDDING ENGINE                        │   │    │
│  │  │  sentence-transformers/all-MiniLM-L6-v2                  │   │    │
│  │  │  - 384-dimensional dense vectors                         │   │    │
│  │  │  - normalized embeddings                                 │   │    │
│  │  │  - batch processing for efficiency                       │   │    │
│  │  └──────────────────────────┬───────────────────────────────┘   │    │
│  │                             │                                   │    │
│  │                             ▼                                   │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │                   VECTOR STORE                            │   │    │
│  │  │  ChromaDB                                                │   │    │
│  │  │  - Collection: mutual_fund_faq                            │   │    │
│  │  │  - Persistence: local file-based                         │   │    │
│  │  │  - Index: HNSW (default)                                 │   │    │
│  │  │  - Distance: cosine similarity                           │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    RETRIEVAL MODULES                           │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │ Query        │  │ Vector       │  │ Context              │  │    │
│  │  │ Preprocessor │─▶│ Searcher     │─▶│ Builder              │  │    │
│  │  │              │  │              │  │                      │  │    │
│  │  │ - normalize  │  │ - embed query│  │ - concatenate chunks │  │    │
│  │  │ - detect     │  │ - cosine sim │  │ - attach metadata    │  │    │
│  │  │   intent     │  │ - top-k=3-5  │  │ - format prompt      │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────┬───────────┘  │    │
│  │                                                  │              │    │
│  │                                                  ▼              │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │                   LLM GENERATOR                           │   │    │
│  │  │  - System prompt (facts-only, citation, refusal rules)   │   │    │
│  │  │  - Context injection                                     │   │    │
│  │  │  - Answer generation (≤3 sentences)                     │   │    │
│  │  │  - Citation extraction from metadata                     │   │    │
│  │  │  - Refusal detection + educational link                  │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                       UI LAYER                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │    │
│  │  │ Welcome      │  │ Example       │  │ Disclaimer           │  │    │
│  │  │ Message      │  │ Questions    │  │ Banner               │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │    │
│  │                                                                 │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │              Chat Interface (Streamlit/Gradio)           │   │    │
│  │  │  - Input box  - Chat history  - Source citations         │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Module Design

### 3.1 Data Ingestion Pipeline

#### 3.1.1 URL Loader
```
┌─────────────────────────────────────────┐
│              URL LOADER                  │
│                                         │
│  Input: List of 15-25 URLs              │
│                                         │
│  ┌─────────────┐    ┌─────────────┐    │
│  │ HTTP Fetch  │───▶│ HTML Parse  │    │
│  │ (requests)  │    │ (BeautifulSoup)│  │
│  └─────────────┘    └──────┬──────┘    │
│                            │           │
│                   ┌────────▼────────┐  │
│                   │ Extract Content │  │
│                   │ - main text     │  │
│                   │ - tables        │  │
│                   │ - remove nav    │  │
│                   │ - remove footer │  │
│                   └────────┬────────┘  │
│                            │           │
│                   ┌────────▼────────┐  │
│                   │ PDF Detection   │  │
│                   │ - if URL is PDF │  │
│                   │ - download +    │  │
│                   │   parse         │  │
│                   └────────┬────────┘  │
│                            │           │
│                   ┌────────▼────────┐  │
│                   │ Raw Text Output │  │
│                   │ + source_url    │  │
│                   │ + doc_type      │  │
│                   └─────────────────┘  │
└─────────────────────────────────────────┘
```

**Key Decisions:**
- Use `requests` + `BeautifulSoup` for HTML pages
- Use `pdfplumber` for PDF documents (better table extraction than PyPDF2)
- Detect content type from URL extension or Content-Type header
- Strip navigation, footers, and boilerplate content

#### 3.1.2 Chunker
```
┌─────────────────────────────────────────┐
│               CHUNKER                    │
│                                         │
│  Input: Raw text + metadata             │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ RecursiveCharacterTextSplitter  │    │
│  │                                 │    │
│  │ chunk_size: 800 tokens          │    │
│  │ chunk_overlap: 160 tokens (20%) │    │
│  │ separators:                     │    │
│  │   1. \n\n (paragraph break)     │    │
│  │   2. \n   (line break)          │    │
│  │   3. ". "  (sentence end)       │    │
│  │   4. " "   (word boundary)      │    │
│  │   5. ""    (character)          │    │
│  └────────────┬────────────────────┘    │
│               │                         │
│               ▼                         │
│  ┌─────────────────────────────────┐    │
│  │ Chunk Output                    │    │
│  │ {                               │    │
│  │   chunk_id: "uuid",             │    │
│  │   text: "...",                  │    │
│  │   metadata: {                   │    │
│  │     source_url: "...",          │    │
│  │     doc_type: "factsheet",     │    │
│  │     scheme_name: "HDFC Flexi", │    │
│  │     chunk_index: 0,             │    │
│  │     char_start: 0,              │    │
│  │     char_end: 800               │    │
│  │   }                             │    │
│  │ }                               │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Key Decisions:**
- Recursive splitting preserves semantic structure (paragraphs → sentences → words)
- 20% overlap prevents context loss at chunk boundaries
- Metadata attached to every chunk for citation and filtering

#### 3.1.3 Embedding Engine
```
┌─────────────────────────────────────────┐
│           EMBEDDING ENGINE               │
│                                         │
│  Model: sentence-transformers/          │
│         all-MiniLM-L6-v2                │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Model Properties                │    │
│  │ - Dimensions: 384               │    │
│  │ - Max sequence length: 256      │    │
│  │ - Normalized embeddings: yes    │    │
│  │ - Similarity: cosine            │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Processing                      │    │
│  │ - Batch size: 32                │    │
│  │ - Convert to numpy arrays       │    │
│  │ - L2 normalize vectors          │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Output: 384-dim vector per chunk       │
└─────────────────────────────────────────┘
```

**Key Decisions:**
- `all-MiniLM-L6-v2` chosen for: small size (80MB), fast inference, good quality for semantic search
- 384 dimensions balance accuracy and storage efficiency
- L2 normalization ensures cosine similarity works correctly

#### 3.1.4 Vector Store (ChromaDB)
```
┌─────────────────────────────────────────┐
│              CHROMADB                    │
│                                         │
│  Collection: mutual_fund_faq            │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Document Schema                 │    │
│  │ {                               │    │
│  │   id: "chunk_uuid",             │    │
│  │   embedding: [0.12, -0.34, ...],│    │
│  │   document: "chunk text...",    │    │
│  │   metadata: {                   │    │
│  │     source_url: "...",          │    │
│  │     doc_type: "...",           │    │
│  │     scheme_name: "...",         │    │
│  │     chunk_index: 0              │    │
│  │   }                             │    │
│  │ }                               │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Index Configuration             │    │
│  │ - Index type: HNSW              │    │
│  │ - Distance: cosine              │    │
│  │ - M: 16 (connections per node)  │    │
│  │ - ef_construction: 100          │    │
│  │ - ef_search: 50                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Persistence: ./chroma_db/              │
└─────────────────────────────────────────┘
```

**Key Decisions:**
- ChromaDB chosen for: lightweight, embedded, no separate server needed
- HNSW index for fast approximate nearest neighbor search
- Cosine distance for semantic similarity
- File-based persistence for prototype simplicity

---

### 3.2 Data Retrieval Pipeline

#### 3.2.1 Query Preprocessor
```
┌─────────────────────────────────────────┐
│         QUERY PREPROCESSOR               │
│                                         │
│  Input: Raw user query                  │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Intent Detection                │    │
│  │                                 │    │
│  │ Advice keywords:                │    │
│  │ - "should I buy/sell"           │    │
│  │ - "best fund"                   │    │
│  │ - "recommend"                   │    │
│  │ - "which fund for me"           │    │
│  │ - "portfolio advice"            │    │
│  │                                 │    │
│  │ If advice → refusal path        │    │
│  │ If factual → retrieval path     │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Query Normalization             │    │
│  │ - lowercase                     │    │
│  │ - remove extra whitespace       │    │
│  │ - expand abbreviations          │    │
│  │   (ELSS, SIP, TER, KIM, SID)    │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Output: Normalized query + intent flag │
└─────────────────────────────────────────┘
```

#### 3.2.2 Vector Searcher
```
┌─────────────────────────────────────────┐
│           VECTOR SEARCHER                │
│                                         │
│  Input: Normalized query                │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Query Embedding                 │    │
│  │ - Same model: all-MiniLM-L6-v2  │    │
│  │ - 384-dim vector                │    │
│  └────────────┬────────────────────┘    │
│               │                         │
│               ▼                         │
│  ┌─────────────────────────────────┐    │
│  │ ChromaDB Query                  │    │
│  │ - collection.query()            │    │
│  │ - n_results: 5 (top-k)          │    │
│  │ - where: optional filters       │    │
│  │ - include: documents, metadatas,│    │
│  │           distances             │    │
│  └────────────┬────────────────────┘    │
│               │                         │
│               ▼                         │
│  ┌─────────────────────────────────┐    │
│  │ Results                         │    │
│  │ [                               │    │
│  │   {                             │    │
│  │     chunk_id: "...",            │    │
│  │     text: "...",                │    │
│  │     source_url: "...",          │    │
│  │     score: 0.87                 │    │
│  │   },                            │    │
│  │   ... (top 5)                   │    │
│  │ ]                               │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Key Decisions:**
- Top-k = 5 for balance between context richness and noise
- Cosine similarity score threshold: 0.5 (filter out irrelevant results)
- Optional metadata filtering by scheme_name or doc_type

#### 3.2.3 Context Builder
```
┌─────────────────────────────────────────┐
│          CONTEXT BUILDER                 │
│                                         │
│  Input: Top-k chunks from ChromaDB      │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Prompt Construction             │    │
│  │                                 │    │
│  │ SYSTEM PROMPT:                  │    │
│  │ "You are a facts-only mutual    │    │
│  │  fund FAQ assistant. Answer     │    │
│  │  using ONLY the provided        │    │
│  │  context. Include one source    │    │
│  │  link. Keep answers to 3        │    │
│  │  sentences or fewer. If the    │    │
│  │  question asks for investment   │    │
│  │  advice, politely decline and   │    │
│  │  provide an educational link."  │    │
│  │                                 │    │
│  │ CONTEXT:                        │    │
│  │ [Chunk 1 text]                  │    │
│  │ Source: [URL 1]                 │    │
│  │                                 │    │
│  │ [Chunk 2 text]                  │    │
│  │ Source: [URL 2]                 │    │
│  │                                 │    │
│  │ ...                             │    │
│  │                                 │    │
│  │ USER QUERY:                     │    │
│  │ [Original question]             │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Output: Formatted prompt string        │
└─────────────────────────────────────────┘
```

#### 3.2.4 LLM Generator
```
┌─────────────────────────────────────────┐
│           LLM GENERATOR                  │
│                                         │
│  Input: Formatted prompt                │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ LLM Configuration               │    │
│  │ - Model: gpt-3.5-turbo /        │    │
│  │          open-source alternative│    │
│  │ - Temperature: 0.1 (low)        │    │
│  │ - Max tokens: 150               │    │
│  │ - Top_p: 0.9                    │    │
│  └────────────┬────────────────────┘    │
│               │                         │
│               ▼                         │
│  ┌─────────────────────────────────┐    │
│  │ Generated Output                │    │
│  │                                 │    │
│  │ Normal Answer:                  │    │
│  │ "The expense ratio of HDFC     │    │
│  │  Flexi Cap Fund Direct is       │    │
│  │  0.71% (as of [date]).          │    │
│  │  Source: [URL]                  │    │
│  │  Last updated from sources:     │    │
│  │  [URL]"                         │    │
│  │                                 │    │
│  │ Refusal Answer:                 │    │
│  │ "I can only provide factual     │    │
│  │  information, not investment    │    │
│  │  advice. For educational        │    │
│  │  resources, visit SEBI's        │    │
│  │  investor education page:       │    │
│  │  [URL]"                         │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

## 4. Data Flow Diagrams

### 4.1 Ingestion Flow
```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  START  │────▶│  LOAD   │────▶│  CLEAN  │────▶│  CHUNK  │────▶│  EMBED  │
│         │     │  URLS   │     │  TEXT   │     │         │     │         │
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └────┬────┘
                                                                      │
                                                                      ▼
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  DONE   │◀────│ VERIFY  │◀────│  STORE  │◀────│ BATCH   │◀────│ VECTOR  │
│         │     │  DATA   │     │ CHUNKS  │     │ EMBED   │     │ READY   │
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
```

### 4.2 Retrieval Flow
```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  USER   │────▶│ DETECT  │────▶│  EMBED  │────▶│ SEARCH  │────▶│ RANK &  │
│  QUERY  │     │  INTENT │     │  QUERY  │     │ CHROMA  │     │ FILTER  │
└─────────┘     └────┬────┘     └─────────┘     └─────────┘     └────┬────┘
                     │                                                │
                     │ advice                                         │ factual
                     ▼                                                ▼
              ┌─────────────┐                              ┌─────────────────┐
              │   REFUSAL   │                              │ BUILD CONTEXT   │
              │   PATH      │                              │ (top-k chunks)  │
              └──────┬──────┘                              └────────┬────────┘
                     │                                                │
                     │                                                ▼
                     │                                       ┌─────────────────┐
                     │                                       │  LLM GENERATE   │
                     │                                       │  (answer +      │
                     │                                       │   citation)     │
                     │                                       └────────┬────────┘
                     │                                                │
                     ▼                                                ▼
              ┌─────────────────────────────────────────────────────────────┐
              │                        FORMAT RESPONSE                       │
              │  - Answer text  - Source link  - "Last updated" note        │
              └─────────────────────────────────────────────────────────────┘
```

---

## 5. File Structure

```
ragbot/
├── PRD.md                          # Product Requirements
├── ARCHITECTURE.md                 # This document
├── README.md                       # Setup & usage
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (API keys)
│
├── src/
│   ├── __init__.py
│   │
│   ├── ingestion/                  # Stage 1: Data Ingestion
│   │   ├── __init__.py
│   │   ├── loader.py               # URL loading + HTML/PDF parsing
│   │   ├── chunker.py              # Text chunking with metadata
│   │   ├── embedder.py             # Embedding generation
│   │   └── vector_store.py         # ChromaDB storage
│   │
│   ├── retrieval/                  # Stage 2: Data Retrieval
│   │   ├── __init__.py
│   │   ├── query_processor.py      # Intent detection + normalization
│   │   ├── searcher.py             # ChromaDB vector search
│   │   ├── context_builder.py      # Prompt construction
│   │   └── generator.py            # LLM answer generation
│   │
│   ├── ui/                         # UI Layer
│   │   ├── __init__.py
│   │   └── app.py                  # Streamlit/Gradio interface
│   │
│   └── config/
│       ├── __init__.py
│       └── settings.py             # Configuration constants
│
├── data/
│   ├── sources.csv                 # Source URL list
│   ├── raw/                        # Raw scraped content (temp)
│   └── chroma_db/                  # ChromaDB persistent storage
│
├── notebooks/
│   └── demo.ipynb                  # Jupyter demo notebook
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   └── test_e2e.py
│
└── docs/
    ├── sample_qa.md                # Sample Q&A file
    └── disclaimer.md               # Disclaimer snippet
```

---

## 6. API Design

### 6.1 Ingestion API

```python
# src/ingestion/pipeline.py

class IngestionPipeline:
    """Stage 1: Data Ingestion Pipeline"""

    def __init__(self, config: dict):
        self.loader = URLLoader()
        self.chunker = Chunker(
            chunk_size=config.get("chunk_size", 800),
            chunk_overlap=config.get("chunk_overlap", 160)
        )
        self.embedder = Embedder(
            model_name=config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        )
        self.vector_store = VectorStore(
            persist_dir=config.get("persist_dir", "./data/chroma_db"),
            collection_name=config.get("collection_name", "mutual_fund_faq")
        )

    def run(self, urls: list[str]) -> dict:
        """
        Execute full ingestion pipeline.

        Args:
            urls: List of source URLs to ingest

        Returns:
            {
                "status": "success",
                "urls_processed": 15,
                "chunks_created": 250,
                "errors": []
            }
        """
        results = {"status": "success", "urls_processed": 0, "chunks_created": 0, "errors": []}

        for url in urls:
            try:
                # Step 1: Load
                raw_text, metadata = self.loader.load(url)

                # Step 2: Chunk
                chunks = self.chunker.split(raw_text, metadata)

                # Step 3: Embed
                embeddings = self.embedder.embed_batch(chunks)

                # Step 4: Store
                self.vector_store.add(chunks, embeddings)

                results["urls_processed"] += 1
                results["chunks_created"] += len(chunks)

            except Exception as e:
                results["errors"].append({"url": url, "error": str(e)})

        return results
```

### 6.2 Retrieval API

```python
# src/retrieval/pipeline.py

class RetrievalPipeline:
    """Stage 2: Data Retrieval Pipeline"""

    def __init__(self, config: dict):
        self.query_processor = QueryProcessor()
        self.searcher = Searcher(
            persist_dir=config.get("persist_dir", "./data/chroma_db"),
            collection_name=config.get("collection_name", "mutual_fund_faq"),
            embedding_model=config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        )
        self.context_builder = ContextBuilder(max_chunks=config.get("top_k", 5))
        self.generator = Generator(
            model=config.get("llm_model", "gpt-3.5-turbo"),
            temperature=config.get("temperature", 0.1)
        )

    def query(self, question: str) -> dict:
        """
        Execute full retrieval pipeline.

        Args:
            question: User's question

        Returns:
            {
                "answer": "...",
                "source_url": "...",
                "is_refusal": false,
                "confidence": 0.87
            }
        """
        # Step 1: Process query
        processed = self.query_processor.process(question)

        # Step 2: Check intent
        if processed["is_advice"]:
            return self._refusal_response()

        # Step 3: Search
        results = self.searcher.search(processed["normalized_query"])

        # Step 4: Build context
        prompt = self.context_builder.build(processed["normalized_query"], results)

        # Step 5: Generate
        response = self.generator.generate(prompt)

        return {
            "answer": response["answer"],
            "source_url": response["source_url"],
            "is_refusal": False,
            "confidence": results[0]["score"] if results else 0.0
        }

    def _refusal_response(self) -> dict:
        return {
            "answer": "I can only provide factual information, not investment advice. "
                      "For educational resources, visit SEBI's investor education page.",
            "source_url": "https://www.sebi.gov.in/sebi_data/commondocs/siep_h.html",
            "is_refusal": True,
            "confidence": 1.0
        }
```

---

## 7. Configuration

### 7.1 Default Configuration

```python
# src/config/settings.py

CONFIG = {
    # Ingestion
    "chunk_size": 800,
    "chunk_overlap": 160,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",

    # Vector Store
    "persist_dir": "./data/chroma_db",
    "collection_name": "mutual_fund_faq",

    # Retrieval
    "top_k": 5,
    "similarity_threshold": 0.5,

    # LLM
    "llm_model": "gpt-3.5-turbo",
    "temperature": 0.1,
    "max_tokens": 150,

    # UI
    "app_title": "MF FAQ Assistant",
    "welcome_message": "Ask me factual questions about HDFC mutual fund schemes.",
    "example_questions": [
        "What is the expense ratio of HDFC Flexi Cap Fund?",
        "What is the ELSS lock-in period?",
        "How do I download my capital gains statement?"
    ]
}
```

### 7.2 Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./data/chroma_db
```

---

## 8. Error Handling

| Error Type | Handling Strategy |
|---|---|
| URL fetch failure | Log error, skip URL, continue with others |
| PDF parse failure | Try alternative parser (PyPDF2), then skip |
| Embedding failure | Retry with smaller batch, then skip chunk |
| ChromaDB connection failure | Fallback to in-memory collection |
| LLM API failure | Retry with backoff, then return fallback message |
| No relevant chunks found | Return "I don't have information on that topic" |
| Advice question detected | Return refusal with educational link |

---

## 9. Performance Considerations

| Aspect | Target | Strategy |
|---|---|---|
| Ingestion time | <5 min for 15 URLs | Batch embedding, parallel URL fetching |
| Query response | <5 seconds | HNSW index, cached embeddings, top-k=5 |
| Embedding speed | ~100 chunks/sec | all-MiniLM-L6-v2 is lightweight |
| ChromaDB search | <100ms | HNSW approximate nearest neighbor |
| LLM generation | <3 seconds | Low temperature, max_tokens=150 |

---

## 10. Security & Privacy

| Requirement | Implementation |
|---|---|
| No PII storage | No user data persistence; stateless queries |
| No authentication | Public read-only access to prototype |
| API key security | Environment variables only; never in code |
| Input sanitization | Strip special characters from queries |
| Rate limiting | N/A for prototype (local deployment) |

---

## 11. Deployment Architecture (Prototype)

```
┌─────────────────────────────────────────┐
│           LOCAL DEPLOYMENT              │
│                                         │
│  ┌─────────────┐    ┌─────────────┐    │
│  │  Streamlit  │    │  ChromaDB   │    │
│  │  App        │◀──▶│  (local)    │    │
│  │  :8501      │    │  ./data/    │    │
│  └──────┬──────┘    └─────────────┘    │
│         │                               │
│         ▼                               │
│  ┌─────────────┐                        │
│  │  OpenAI API │                        │
│  │  (cloud)    │                        │
│  └─────────────┘                        │
│                                         │
│  All data flows through local machine   │
│  No PII leaves the system               │
└─────────────────────────────────────────┘
```

---

## 12. Testing Strategy

| Test Type | Scope | Method |
|---|---|---|
| Unit tests | Individual modules | pytest |
| Integration tests | Full pipeline | pytest + fixtures |
| E2E tests | User scenarios | Manual + sample Q&A |
| Accuracy tests | Answer correctness | Human evaluation on 5-10 Q&A |
| Performance tests | Response time | timing benchmarks |

---

## 13. Monitoring & Logging

```python
# Logging configuration
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/ragbot.log"),
        logging.StreamHandler()
    ]
)

# Key events to log:
# - Ingestion: URL fetch success/failure, chunks created
# - Retrieval: Query received, intent detected, search results, response generated
# - Errors: Full stack traces for debugging
```

---

*End of Architecture Document*
