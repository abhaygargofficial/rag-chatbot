# MF FAQ Assistant — RAG Bot

A facts-only mutual fund FAQ assistant that answers questions about HDFC mutual fund schemes using only official public sources (AMC, SEBI, AMFI).

## Features

- **Facts-only Q&A** — Answers factual queries about expense ratio, exit load, minimum SIP, ELSS lock-in, riskometer, benchmark, and more
- **Citation per answer** — Every answer includes one source link
- **Refusal handling** — Politely declines investment advice questions with educational links
- **Tiny UI** — Simple Streamlit interface with example questions
- **RAG architecture** — Full retrieval-augmented generation pipeline with ChromaDB

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up environment variables

Edit `.env` and add your Groq API key:

```bash
GROQ_API_KEY=gsk_your_actual_key_here
```

Get your API key from [console.groq.com](https://console.groq.com).

### 3. Run data ingestion

```bash
python -m src.ingestion.pipeline
```

This will:
- Fetch all 16 source URLs
- Chunk the content
- Generate embeddings
- Store in ChromaDB

### 4. Run the app

```bash
streamlit run src/ui/app.py
```

Open http://localhost:8501 in your browser.

## Demo

See [demo.ipynb](demo.ipynb) for a Jupyter notebook walkthrough of the full pipeline.

## Project Structure

```
ragbot/
├── PRD.md                          # Product Requirements
├── ARCHITECTURE.md                 # Architecture Design
├── IMPLEMENTATION.md               # Implementation Guide
├── README.md                       # This file
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables
├── verify.py                       # Verification script
│
├── src/
│   ├── config/
│   │   └── settings.py             # Configuration
│   ├── ingestion/                  # Stage 1: Data Ingestion
│   │   ├── loader.py               # URL loading + HTML/PDF parsing
│   │   ├── chunker.py              # Text chunking
│   │   ├── embedder.py             # Embedding generation
│   │   ├── vector_store.py         # ChromaDB storage
│   │   └── pipeline.py             # Ingestion orchestrator
│   ├── retrieval/                  # Stage 2: Data Retrieval
│   │   ├── query_processor.py      # Intent detection
│   │   ├── searcher.py             # Vector search
│   │   ├── context_builder.py      # Prompt construction
│   │   ├── generator.py            # LLM answer generation
│   │   └── pipeline.py             # Retrieval orchestrator
│   └── ui/
│       └── app.py                  # Streamlit interface
│
├── data/
│   ├── sources.csv                 # Source URL list
│   └── chroma_db/                  # ChromaDB storage
│
├── tests/
│   ├── test_ingestion.py           # Ingestion tests
│   ├── test_retrieval.py           # Retrieval tests
│   └── test_e2e.py                 # End-to-end tests
│
└── docs/
    ├── sample_qa.md                # Sample Q&A
    └── disclaimer.md               # Disclaimer
```

## Running Tests

```bash
pytest tests/ -v
```

## Deliverables

| Deliverable | Location |
|---|---|
| Working prototype | `src/ui/app.py` (Streamlit) |
| Demo notebook | `demo.ipynb` |
| Source list | `data/sources.csv` |
| README | `README.md` |
| Sample Q&A | `docs/sample_qa.md` |
| Disclaimer | `docs/disclaimer.md` |
| Verification script | `verify.py` |

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture design.

**RAG Pipeline:**
1. **Data Ingestion**: URLs → Load → Chunk → Embed → Store in ChromaDB
2. **Data Retrieval**: Query → Embed → Search → Context → LLM → Answer + Citation

**Tech Stack:**
- Embedding: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- Vector DB: ChromaDB (cosine similarity)
- LLM: Groq (`llama-3.1-8b-instant`)
- UI: Streamlit

## Known Limitations

- **Facts-only** — No investment advice or portfolio recommendations
- **Limited corpus** — Only HDFC Mutual Fund schemes (3 schemes)
- **No performance data** — Does not compute or compare returns
- **English only** — No multi-language support
- **Static corpus** — Requires manual re-ingestion for updates

## Disclaimer

**Facts-only. No investment advice.**

This assistant provides factual information from official public sources only. It does not recommend, endorse, or advise on any mutual fund scheme or investment decision. Please consult a SEBI-registered investment advisor for personalized advice.
