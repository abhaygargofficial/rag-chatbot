"""Configuration settings for the RAG Bot."""

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

    # LLM (Groq)
    "llm_model": "llama-3.1-8b-instant",
    "temperature": 0.1,
    "max_tokens": 150,

    # UI
    "app_title": "MF FAQ Assistant",
    "welcome_message": "Ask me factual questions about HDFC mutual fund schemes.",
    "example_questions": [
        "What is the expense ratio of HDFC Flexi Cap Fund?",
        "What is the ELSS lock-in period?",
        "How do I download my capital gains statement?",
    ],
}
