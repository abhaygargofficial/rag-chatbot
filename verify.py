"""Final verification script for the RAG bot project."""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def check_file(path, description):
    """Check if a file exists."""
    exists = os.path.exists(path)
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {description}: {path}")
    return exists


def check_sources_csv():
    """Check sources.csv has all 16 URLs."""
    print("\nChecking sources.csv...")
    csv_path = "data/sources.csv"
    if not os.path.exists(csv_path):
        print(f"  [MISSING] {csv_path}")
        return False

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"  [OK] Found {len(rows)} URLs in sources.csv")
    return len(rows) >= 16


def check_chroma_db():
    """Check ChromaDB has chunks."""
    print("\nChecking ChromaDB...")
    try:
        from src.ingestion.vector_store import VectorStore

        store = VectorStore()
        count = store.count()
        if count > 0:
            print(f"  [OK] ChromaDB has {count} chunks")
            return True
        else:
            print(f"  [WARN] ChromaDB is empty (run ingestion first)")
            return False
    except Exception as e:
        print(f"  [ERROR] ChromaDB check failed: {e}")
        return False


def check_env():
    """Check .env file exists and has Groq key."""
    print("\nChecking .env...")
    env_path = ".env"
    if not os.path.exists(env_path):
        print(f"  [MISSING] {env_path}")
        return False

    with open(env_path, "r") as f:
        content = f.read()

    if "GROQ_API_KEY" in content:
        print(f"  [OK] GROQ_API_KEY found in .env")
        if "your-groq-api-key-here" in content:
            print(f"  [WARN] GROQ_API_KEY is still a placeholder - update it!")
            return False
        return True
    else:
        print(f"  [MISSING] GROQ_API_KEY not found in .env")
        return False


def main():
    """Run all verification checks."""
    print("=" * 50)
    print("RAG BOT - FINAL VERIFICATION")
    print("=" * 50)

    all_passed = True

    # Check project files
    print("\nChecking project files...")
    files = [
        ("PRD.md", "Product Requirements"),
        ("ARCHITECTURE.md", "Architecture Document"),
        ("IMPLEMENTATION.md", "Implementation Guide"),
        ("README.md", "README"),
        ("requirements.txt", "Requirements"),
        (".env", "Environment Config"),
        ("data/sources.csv", "Source URLs"),
        ("docs/disclaimer.md", "Disclaimer"),
        ("docs/sample_qa.md", "Sample Q&A"),
        ("src/config/settings.py", "Settings"),
        ("src/ingestion/loader.py", "URL Loader"),
        ("src/ingestion/chunker.py", "Chunker"),
        ("src/ingestion/embedder.py", "Embedder"),
        ("src/ingestion/vector_store.py", "Vector Store"),
        ("src/ingestion/pipeline.py", "Ingestion Pipeline"),
        ("src/retrieval/query_processor.py", "Query Processor"),
        ("src/retrieval/searcher.py", "Searcher"),
        ("src/retrieval/context_builder.py", "Context Builder"),
        ("src/retrieval/generator.py", "Generator"),
        ("src/retrieval/pipeline.py", "Retrieval Pipeline"),
        ("src/ui/app.py", "Streamlit App"),
        ("tests/test_ingestion.py", "Ingestion Tests"),
        ("tests/test_retrieval.py", "Retrieval Tests"),
        ("tests/test_e2e.py", "E2E Tests"),
    ]

    for path, desc in files:
        if not check_file(path, desc):
            all_passed = False

    # Check sources.csv
    if not check_sources_csv():
        all_passed = False

    # Check ChromaDB
    check_chroma_db()

    # Check .env
    check_env()

    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("VERIFICATION PASSED - All deliverables ready!")
    else:
        print("VERIFICATION FAILED - Some files missing")
    print("=" * 50)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
