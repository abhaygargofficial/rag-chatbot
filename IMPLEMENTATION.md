# Implementation Guide
## Mutual Fund FAQ Assistant — RAG Bot

| Field | Value |
|---|---|
| **Document** | Phase-wise Implementation Guide |
| **Version** | 2.0 |
| **Date** | 2026-09-29 |
| **Status** | Draft |
| **References** | PRD.md, ARCHITECTURE.md |

---

## How to Use This Document

This guide is designed to be used with **Cursor** (or any AI coding assistant) in sequential phases. Each phase contains:

- **Objective** — What to accomplish
- **Files to Create** — Exact file paths
- **Cursor Prompts** — Copy-paste prompts for Cursor (one per sub-module)
- **Verification** — How to verify the phase is complete
- **Exit Criteria** — When to move to the next phase

---

## Phase 1: Project Setup

### Objective
Initialize the project structure, install dependencies, and set up configuration.

### Files to Create
```
ragbot/
├── requirements.txt
├── .env
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
├── data/
│   ├── sources.csv
│   ├── raw/
│   └── chroma_db/
├── tests/
│   └── __init__.py
├── docs/
│   └── disclaimer.md
└── logs/
```

### Cursor Prompt
```
Set up a Python project at the current directory with the following structure:

1. Create requirements.txt with these dependencies:
   - chromadb>=0.4.0
   - sentence-transformers>=2.2.0
   - openai>=1.0.0
   - beautifulsoup4>=4.12.0
   - requests>=2.31.0
   - pdfplumber>=0.9.0
   - streamlit>=1.28.0
   - python-dotenv>=1.0.0
   - langchain>=0.0.300
   - tiktoken>=0.5.0
   - pytest>=7.4.0

2. Create .env with placeholder:
   OPENAI_API_KEY=your-key-here
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   CHROMA_PERSIST_DIR=./data/chroma_db

3. Create .gitignore:
   - .env
   - __pycache__/
   - *.pyc
   - data/chroma_db/
   - data/raw/
   - logs/
   - .venv/

4. Create src/config/settings.py with a CONFIG dict containing:
   - chunk_size: 800
   - chunk_overlap: 160
   - embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
   - persist_dir: "./data/chroma_db"
   - collection_name: "mutual_fund_faq"
   - top_k: 5
   - similarity_threshold: 0.5
   - llm_model: "gpt-3.5-turbo"
   - temperature: 0.1
   - max_tokens: 150
   - app_title: "MF FAQ Assistant"
   - welcome_message: "Ask me factual questions about HDFC mutual fund schemes."
   - example_questions: list of 3 example questions

5. Create data/sources.csv with columns: id, type, url, scheme_name
   Include all 16 URLs from the PRD source corpus table.

6. Create docs/disclaimer.md with the disclaimer text from the PRD.

7. Create empty __init__.py files in src/, src/config/, tests/

Do NOT create any Python implementation files yet. Just the project skeleton.
```

### Verification
```bash
ls -la requirements.txt .env .gitignore
ls -la src/config/settings.py
ls -la data/sources.csv
cat data/sources.csv | wc -l
```

### Exit Criteria
- [ ] All directories created
- [ ] requirements.txt has all dependencies
- [ ] .env exists with placeholders
- [ ] settings.py has CONFIG dict
- [ ] sources.csv has 16 URLs
- [ ] disclaimer.md exists

---

## Phase 2: Data Ingestion Pipeline

### Objective
Build the complete data ingestion pipeline: URL loading, chunking, embedding, and vector storage in ChromaDB.

### Files to Create
- `src/ingestion/__init__.py`
- `src/ingestion/loader.py`
- `src/ingestion/chunker.py`
- `src/ingestion/embedder.py`
- `src/ingestion/vector_store.py`
- `src/ingestion/pipeline.py`

### Cursor Prompts

#### 2a. URL Loader
```
Create the URL loader module for the RAG bot ingestion pipeline.

File: src/ingestion/loader.py

Create a class URLLoader with the following:

1. Method load(url: str) -> tuple[str, dict]:
   - Detect if URL is PDF (check extension or Content-Type header)
   - For HTML: use requests to fetch, then BeautifulSoup to parse
     - Extract main content text (remove nav, footer, script, style tags)
     - Extract text from tables if present
   - For PDF: download to temp file, use pdfplumber to extract text
     - Extract text from all pages
     - Preserve table structure where possible
   - Return (raw_text, metadata_dict)
   - metadata_dict should contain: source_url, doc_type, scheme_name

2. Method detect_doc_type(url: str) -> str:
   - Return one of: "scheme_page", "factsheet", "kim", "sid", "ter_report", "statement_guide", "education", "riskometer"
   - Use URL patterns to determine type

3. Method detect_scheme_name(url: str) -> str:
   - Return scheme name if URL is scheme-specific, else "general"
   - Match patterns like "hdfc-flexi-cap", "hdfc-small-cap", "hdfc-elss"

4. Error handling:
   - requests.exceptions.RequestException for fetch failures
   - Log errors with logging module
   - Return ("", {}) on failure

5. Add a main() function that:
   - Reads URLs from data/sources.csv
   - Loads each URL
   - Prints summary (success/failure per URL)

Import requirements: requests, bs4, pdfplumber, logging, csv, tempfile, os
```

#### 2b. Chunker
```
Create the chunker module for the RAG bot ingestion pipeline.

File: src/ingestion/chunker.py

Create a class Chunker with the following:

1. __init__(self, chunk_size: int = 800, chunk_overlap: int = 160):
   - Store chunk_size and chunk_overlap
   - Initialize RecursiveCharacterTextSplitter from langchain.text_splitter
   - Use separators: ["\n\n", "\n", ". ", " ", ""]

2. Method split(self, text: str, metadata: dict) -> list[dict]:
   - Use the text splitter to split text into chunks
   - For each chunk, create a dict with:
     - chunk_id: generate UUID
     - text: the chunk text
     - metadata: copy of input metadata + chunk_index, char_start, char_end
   - Return list of chunk dicts

3. Method split_batch(self, texts_with_metadata: list[tuple[str, dict]]) -> list[dict]:
   - Process multiple texts at once
   - Return combined list of chunks

4. Add a main() function that:
   - Creates a Chunker instance
   - Tests with sample text
   - Prints number of chunks created

Import requirements: langchain.text_splitter.RecursiveCharacterTextSplitter, uuid
```

#### 2c. Embedding Engine
```
Create the embedding engine module for the RAG bot ingestion pipeline.

File: src/ingestion/embedder.py

Create a class Embedder with the following:

1. __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
   - Load the sentence transformer model: SentenceTransformer(model_name)
   - Store model reference
   - Set batch_size = 32

2. Method embed(self, text: str) -> list[float]:
   - Embed a single text string
   - Return list of 384 floats (the embedding vector)
   - Use model.encode(text, normalize_embeddings=True)

3. Method embed_batch(self, texts: list[str]) -> list[list[float]]:
   - Embed multiple texts in batch
   - Use model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
   - Return list of embedding vectors

4. Method embed_chunks(self, chunks: list[dict]) -> list[dict]:
   - Extract text from each chunk
   - Call embed_batch on all texts
   - Add "embedding" key to each chunk dict
   - Return chunks with embeddings

5. Add a main() function that:
   - Creates an Embedder instance
   - Tests with sample texts
   - Prints embedding dimensions

Import requirements: sentence_transformers.SentenceTransformer
```

#### 2d. Vector Store
```
Create the vector store module for the RAG bot ingestion pipeline.

File: src/ingestion/vector_store.py

Create a class VectorStore with the following:

1. __init__(self, persist_dir: str = "./data/chroma_db", collection_name: str = "mutual_fund_faq"):
   - Create ChromaDB client: chromadb.PersistentClient(path=persist_dir)
   - Get or create collection with name=collection_name
   - Store collection reference

2. Method add(self, chunks: list[dict], embeddings: list[list[float]]):
   - Extract ids, documents, metadatas, embeddings from chunks
   - collection.add(ids=..., embeddings=..., documents=..., metadatas=...)
   - Each chunk dict has: chunk_id, text, metadata, embedding

3. Method add_batch(self, chunks_with_embeddings: list[dict], batch_size: int = 100):
   - Add in batches to avoid memory issues
   - Call self.add() for each batch

4. Method count(self) -> int:
   - Return collection.count()

5. Method search(self, query_embedding: list[float], n_results: int = 5) -> list[dict]:
   - collection.query(query_embeddings=[query_embedding], n_results=n_results)
   - Return list of dicts with: chunk_id, text, source_url, score
   - Extract from ChromaDB response format

6. Method clear(self):
   - Delete and recreate collection (for re-ingestion)

7. Add a main() function that:
   - Creates a VectorStore instance
   - Prints collection count

Import requirements: chromadb
```

#### 2e. Ingestion Pipeline Orchestrator
```
Create the ingestion pipeline orchestrator for the RAG bot.

File: src/ingestion/pipeline.py

Create a class IngestionPipeline with the following:

1. __init__(self, config: dict):
   - Create URLLoader instance
   - Create Chunker with config chunk_size and chunk_overlap
   - Create Embedder with config embedding_model
   - Create VectorStore with config persist_dir and collection_name

2. Method run(self, urls: list[str] = None) -> dict:
   - If urls is None, read from data/sources.csv
   - For each URL:
     a. Load raw text and metadata
     b. Chunk the text
     c. Embed the chunks
     d. Store in vector DB
   - Track: urls_processed, chunks_created, errors
   - Return summary dict

3. Method run_from_csv(self, csv_path: str = "data/sources.csv") -> dict:
   - Read URLs from CSV
   - Call self.run(urls)

4. Add a main() function that:
   - Load config from src.config.settings
   - Create IngestionPipeline
   - Run full ingestion
   - Print summary

Import requirements: all ingestion modules, config.settings
```

### Verification
```bash
# Test individual modules
python -c "from src.ingestion.loader import URLLoader; l = URLLoader(); text, meta = l.load('https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/direct'); print(f'Loaded {len(text)} chars, type: {meta.get(\"doc_type\")}')"

python -c "from src.ingestion.chunker import Chunker; c = Chunker(); chunks = c.split('This is a test. ' * 100, {'source_url': 'http://test.com', 'doc_type': 'test'}); print(f'Created {len(chunks)} chunks')"

python -c "from src.ingestion.embedder import Embedder; e = Embedder(); emb = e.embed('test'); print(f'Embedding dim: {len(emb)}')"

python -c "from src.ingestion.vector_store import VectorStore; vs = VectorStore(); print(f'Collection count: {vs.count()}')"

# Run full ingestion
python -m src.ingestion.pipeline
```

### Exit Criteria
- [ ] URLLoader class created with load() method
- [ ] HTML parsing works (BeautifulSoup)
- [ ] PDF parsing works (pdfplumber)
- [ ] Doc type detection works
- [ ] Scheme name detection works
- [ ] Chunker class created with split() method
- [ ] RecursiveCharacterTextSplitter configured correctly
- [ ] Chunks have UUID, text, and metadata
- [ ] Embedder class created
- [ ] Model loads correctly (all-MiniLM-L6-v2)
- [ ] embed() returns 384-dim vector
- [ ] VectorStore class created
- [ ] ChromaDB persistent client configured
- [ ] add() method stores chunks with embeddings
- [ ] search() returns ranked results with scores
- [ ] IngestionPipeline class created
- [ ] run() method orchestrates all steps
- [ ] run_from_csv() reads sources.csv
- [ ] Errors are caught and logged per URL
- [ ] Full ingestion runs end-to-end

---

## Phase 3: Data Retrieval Pipeline

### Objective
Build the complete data retrieval pipeline: query processing, vector search, context building, and LLM generation.

### Files to Create
- `src/retrieval/__init__.py`
- `src/retrieval/query_processor.py`
- `src/retrieval/searcher.py`
- `src/retrieval/context_builder.py`
- `src/retrieval/generator.py`
- `src/retrieval/pipeline.py`

### Cursor Prompts

#### 3a. Query Processor
```
Create the query processor module for the RAG bot retrieval pipeline.

File: src/retrieval/query_processor.py

Create a class QueryProcessor with the following:

1. __init__(self):
   - Define advice keywords list:
     ["should i buy", "should i sell", "best fund", "recommend", "which fund for me",
      "portfolio advice", "investment advice", "what should i invest", "is it good to buy",
      "should i invest", "which is better", "top fund", "good fund to invest"]
   - Define abbreviation mappings:
     {"elss": "equity linked savings scheme", "sip": "systematic investment plan",
      "ter": "total expense ratio", "kim": "key information memorandum",
      "sid": "scheme information document", "amc": "asset management company",
      "nav": "net asset value"}

2. Method detect_intent(self, query: str) -> str:
   - Return "advice" if query contains any advice keyword
   - Return "factual" otherwise

3. Method normalize(self, query: str) -> str:
   - Lowercase
   - Strip extra whitespace
   - Expand abbreviations using mappings
   - Return normalized query

4. Method process(self, query: str) -> dict:
   - Detect intent
   - Normalize query
   - Return {"original": query, "normalized": normalized, "is_advice": bool, "intent": str}

5. Add a main() function that:
   - Tests with sample queries
   - Prints intent detection results

Import requirements: re (for pattern matching)
```

#### 3b. Vector Searcher
```
Create the vector searcher module for the RAG bot retrieval pipeline.

File: src/retrieval/searcher.py

Create a class Searcher with the following:

1. __init__(self, persist_dir: str, collection_name: str, embedding_model: str):
   - Create ChromaDB client
   - Get collection
   - Create Embedder instance (reuse from src.ingestion.embedder)

2. Method search(self, query: str, n_results: int = 5, threshold: float = 0.5) -> list[dict]:
   - Embed the query using embedder
   - Query ChromaDB collection
   - Filter results by similarity threshold
   - Return list of dicts with: chunk_id, text, source_url, score, metadata
   - Sort by score descending

3. Method search_with_filters(self, query: str, filters: dict = None, n_results: int = 5) -> list[dict]:
   - Same as search but with metadata filters
   - filters example: {"scheme_name": "HDFC Flexi Cap"}

4. Add a main() function that:
   - Tests search with sample query
   - Prints top results with scores

Import requirements: chromadb, src.ingestion.embedder.Embedder
```

#### 3c. Context Builder
```
Create the context builder module for the RAG bot retrieval pipeline.

File: src/retrieval/context_builder.py

Create a class ContextBuilder with the following:

1. __init__(self, max_chunks: int = 5):
   - Store max_chunks
   - Define system prompt template

2. Method build(self, query: str, search_results: list[dict]) -> str:
   - Construct system prompt:
     "You are a facts-only mutual fund FAQ assistant. Answer using ONLY the provided context.
      Include one source link. Keep answers to 3 sentences or fewer.
      If the question asks for investment advice, politely decline and provide an educational link.
      Always add 'Last updated from sources: [URL]' at the end of your answer."
   - Build context section from search_results:
     For each result, add:
     [Chunk text]
     Source: [source_url]
   - Build user query section
   - Combine into full prompt string
   - Return formatted prompt

3. Method build_refusal_prompt(self) -> str:
   - Return a prompt for refusal responses

4. Add a main() function that:
   - Tests with sample search results
   - Prints the constructed prompt

Import requirements: none (string formatting only)
```

#### 3d. LLM Generator
```
Create the LLM generator module for the RAG bot retrieval pipeline.

File: src/retrieval/generator.py

Create a class Generator with the following:

1. __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.1, max_tokens: int = 150):
   - Store model, temperature, max_tokens
   - Initialize OpenAI client: openai.OpenAI() (reads API key from env)

2. Method generate(self, prompt: str) -> dict:
   - Call OpenAI chat completions API
   - Use system message from prompt
   - Extract answer from response
   - Extract source URL from the context in the prompt
   - Return {"answer": str, "source_url": str}

3. Method generate_refusal(self) -> dict:
   - Return refusal response:
     answer: "I can only provide factual information, not investment advice. For educational resources, visit SEBI's investor education page."
     source_url: "https://www.sebi.gov.in/sebi_data/commondocs/siep_h.html"

4. Method extract_source_url(self, prompt: str) -> str:
   - Parse the prompt to find the first source URL
   - Use regex to find "Source: <URL>" pattern
   - Return the URL or empty string

5. Error handling:
   - openai.APIError: log and return fallback message
   - openai.RateLimitError: retry with backoff

6. Add a main() function that:
   - Tests generation with sample prompt
   - Prints the response

Import requirements: openai, os, re, logging, time
```

#### 3e. Retrieval Pipeline Orchestrator
```
Create the retrieval pipeline orchestrator for the RAG bot.

File: src/retrieval/pipeline.py

Create a class RetrievalPipeline with the following:

1. __init__(self, config: dict):
   - Create QueryProcessor
   - Create Searcher with config values
   - Create ContextBuilder with config top_k
   - Create Generator with config llm_model, temperature, max_tokens

2. Method query(self, question: str) -> dict:
   - Process query (intent detection + normalization)
   - If advice question: return refusal response
   - If factual question:
     a. Search for relevant chunks
     b. If no results: return "I don't have information on that topic"
     c. Build context prompt
     d. Generate answer
     e. Return {"answer": str, "source_url": str, "is_refusal": false, "confidence": float}

3. Method _refusal_response(self) -> dict:
   - Return refusal dict with SEBI education link

4. Method _no_results_response(self) -> dict:
   - Return "I don't have information on that topic" with empty source_url

5. Add a main() function that:
   - Load config
   - Create pipeline
   - Test with sample queries
   - Print responses

Import requirements: all retrieval modules, config.settings
```

### Verification
```bash
# Test individual modules
python -c "from src.retrieval.query_processor import QueryProcessor; qp = QueryProcessor(); print(qp.process('Should I buy HDFC Flexi Cap?')); print(qp.process('What is the expense ratio?'))"

python -c "from src.retrieval.searcher import Searcher; s = Searcher('./data/chroma_db', 'mutual_fund_faq', 'sentence-transformers/all-MiniLM-L6-v2'); results = s.search('expense ratio'); print(f'Found {len(results)} results'); print(results[0]['text'][:100] if results else 'No results')"

python -c "from src.retrieval.context_builder import ContextBuilder; cb = ContextBuilder(); results = [{'text': 'Test chunk', 'source_url': 'http://test.com', 'score': 0.9}]; print(cb.build('test query', results))"

python -c "from src.retrieval.generator import Generator; g = Generator(); result = g.generate('System: You are a helpful assistant. Context: The expense ratio is 0.5%. Source: http://test.com. Query: What is the expense ratio?'); print(result)"

# Test full retrieval pipeline
python -c "from src.retrieval.pipeline import RetrievalPipeline; from src.config.settings import CONFIG; rp = RetrievalPipeline(CONFIG); result = rp.query('What is the ELSS lock-in period?'); print(result)"
```

### Exit Criteria
- [ ] QueryProcessor class created
- [ ] Advice keyword detection works
- [ ] Abbreviation expansion works
- [ ] Searcher class created
- [ ] search() returns ranked results
- [ ] Threshold filtering works
- [ ] Results include source_url for citations
- [ ] ContextBuilder class created
- [ ] build() constructs proper prompt
- [ ] System prompt includes all rules
- [ ] Generator class created
- [ ] generate() calls OpenAI API
- [ ] generate_refusal() returns proper refusal
- [ ] Error handling for API failures
- [ ] RetrievalPipeline class created
- [ ] query() method orchestrates all steps
- [ ] Advice questions return refusal
- [ ] No-results case handled
- [ ] Full retrieval pipeline runs end-to-end

---

## Phase 4: UI Layer

### Objective
Build the Streamlit UI with welcome message, example questions, disclaimer, and chat interface.

### Files to Create
- `src/ui/__init__.py`
- `src/ui/app.py`

### Cursor Prompt
```
Create the Streamlit UI for the RAG bot.

File: src/ui/app.py

Create a Streamlit app with the following:

1. Page configuration:
   - Title: "MF FAQ Assistant"
   - Icon: chart_with_upwards_trend

2. Load config from src.config.settings

3. Initialize RetrievalPipeline (cache with @st.cache_resource)

4. UI Layout:
   a. Header: App title
   b. Welcome message from config
   c. Disclaimer banner (st.warning): "Facts-only. No investment advice."
   d. Example questions as clickable buttons (3 columns)
   e. Chat input box
   f. Response display area

5. Chat functionality:
   - When user submits question:
     a. Show user message
     b. Show loading spinner
     c. Call pipeline.query()
     d. Display answer
     e. Display source link (st.link_button or st.markdown)
     f. Display "Last updated from sources:" note
   - If refusal: show refusal message with educational link

6. Sidebar:
   - About section
   - Source count
   - Known limitations

7. Footer:
   - Disclaimer text from docs/disclaimer.md

Import requirements: streamlit, src.retrieval.pipeline.RetrievalPipeline, src.config.settings
```

### Verification
```bash
streamlit run src/ui/app.py
```

### Exit Criteria
- [ ] Streamlit app runs without errors
- [ ] Welcome message displays
- [ ] Disclaimer banner shows
- [ ] Example questions are clickable
- [ ] Chat input works
- [ ] Responses show answer + source link
- [ ] Refusal responses work correctly
- [ ] Sidebar shows app info

---

## Phase 5: Testing & Integration

### Objective
Run end-to-end tests, fix issues, and polish the user experience.

### Files to Create
- `tests/test_ingestion.py`
- `tests/test_retrieval.py`
- `tests/test_e2e.py`
- `README.md`
- `docs/sample_qa.md`

### Cursor Prompt
```
Create tests and documentation for the RAG bot.

1. Create tests/test_ingestion.py:
   - Test URLLoader with a sample URL
   - Test Chunker with sample text
   - Test Embedder dimensions
   - Test VectorStore add and search
   - Test full IngestionPipeline

2. Create tests/test_retrieval.py:
   - Test QueryProcessor intent detection
   - Test Searcher with sample query
   - Test ContextBuilder prompt format
   - Test Generator response format
   - Test full RetrievalPipeline

3. Create tests/test_e2e.py:
   - Test full flow: ingest, query, response
   - Test advice question refusal
   - Test no-results case

4. Create README.md with:
   - Project overview
   - Setup instructions (pip install -r requirements.txt)
   - Environment variables setup
   - How to run ingestion
   - How to run the app
   - Project structure
   - Known limitations

5. Create docs/sample_qa.md with:
   - 10 sample questions and expected answers
   - Source links for each
   - Refusal examples

Import requirements: pytest, all src modules
```

### Verification
```bash
pytest tests/ -v
streamlit run src/ui/app.py
```

### Exit Criteria
- [ ] All tests pass
- [ ] README.md is complete
- [ ] sample_qa.md has 10 Q&A pairs
- [ ] App runs without errors
- [ ] Ingestion pipeline works end-to-end
- [ ] Retrieval pipeline works end-to-end
- [ ] UI displays correctly

---

## Phase 6: Deliverables Finalization

### Objective
Prepare all deliverables specified in the PRD.

### Files to Create/Update
- `data/sources.csv` (final version with all URLs)
- `docs/sample_qa.md` (10 Q&A pairs with answers and links)
- `docs/disclaimer.md` (final disclaimer)
- `README.md` (complete with all sections)
- `demo.ipynb` (Jupyter notebook demo)

### Cursor Prompt
```
Finalize all deliverables for the RAG bot project.

1. Update data/sources.csv:
   - Ensure all 16 URLs are present
   - Add columns: id, type, url, scheme_name, status (active/inactive)

2. Create docs/sample_qa.md with 10 Q&A pairs:
   - "What is the expense ratio of HDFC Flexi Cap Fund?"
   - "What is the ELSS lock-in period?"
   - "What is the minimum SIP amount?"
   - "What is the exit load for HDFC Small Cap Fund?"
   - "How do I download my capital gains statement?"
   - "What is the riskometer of HDFC Flexi Cap Fund?"
   - "What is the benchmark for HDFC Flexi Cap Fund?"
   - "Should I buy HDFC Flexi Cap Fund?" (refusal)
   - "Which mutual fund is best for me?" (refusal)
   - "How do I request an account statement?"
   For each: provide the answer and source link

3. Create demo.ipynb:
   - Markdown cells explaining each step
   - Code cells showing: ingestion, query, response
   - Output cells with results

4. Update README.md:
   - Add "Quick Start" section
   - Add "Demo" section
   - Add "Deliverables" section
   - Add "Architecture" section with diagram reference

5. Create a final verification script verify.py:
   - Check all files exist
   - Check all URLs in sources.csv are valid
   - Check ChromaDB has chunks
   - Print summary
```

### Verification
```bash
python verify.py
ls -la README.md docs/sample_qa.md docs/disclaimer.md data/sources.csv demo.ipynb
```

### Exit Criteria
- [ ] sources.csv finalized with all URLs
- [ ] sample_qa.md has 10 Q&A pairs with answers and links
- [ ] disclaimer.md is final
- [ ] README.md is complete
- [ ] demo.ipynb works
- [ ] verify.py passes all checks
- [ ] All PRD deliverables are ready

---

## Summary: Phase Dependencies

Phase 1: Project Setup depends on nothing

Phase 2: Data Ingestion Pipeline depends on Phase 1

Phase 3: Data Retrieval Pipeline depends on Phase 2

Phase 4: UI Layer depends on Phase 3

Phase 5: Testing and Integration depends on Phases 2, 3, 4

Phase 6: Deliverables depends on Phase 5

---

## Quick Reference

| Phase | Name | Sub-modules | Est. Time |
|---|---|---|---|
| 1 | Project Setup | — | 5 min |
| 2 | Data Ingestion Pipeline | Loader, Chunker, Embedder, Vector Store, Pipeline | 60 min |
| 3 | Data Retrieval Pipeline | Query Processor, Searcher, Context Builder, Generator, Pipeline | 60 min |
| 4 | UI Layer | Streamlit App | 20 min |
| 5 | Testing and Integration | Tests, README, Sample Q&A | 30 min |
| 6 | Deliverables | Sources, Docs, Demo, Verify | 20 min |
| **Total** | | | **~3 hours** |

---

*End of Implementation Guide*
