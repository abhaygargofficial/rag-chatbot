"""Ingestion Pipeline orchestrator for the RAG bot."""

import csv
import json
import logging
import os
import uuid
from typing import Optional

from src.config.settings import CONFIG
from .chunker import Chunker
from .embedder import Embedder
from .loader import URLLoader
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates the full data ingestion pipeline."""

    def __init__(self, config: dict):
        """
        Initialize the Ingestion Pipeline.

        Args:
            config: Configuration dict with chunk_size, chunk_overlap,
                   embedding_model, persist_dir, collection_name
        """
        self.config = config
        self.loader = URLLoader()
        self.chunker = Chunker(
            chunk_size=config.get("chunk_size", 800),
            chunk_overlap=config.get("chunk_overlap", 160),
        )
        self.embedder = Embedder(
            model_name=config.get(
                "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
            )
        )
        self.vector_store = VectorStore(
            persist_dir=config.get("persist_dir", "./data/chroma_db"),
            collection_name=config.get("collection_name", "mutual_fund_faq"),
        )

    def run(self, urls: Optional[list] = None) -> dict:
        """
        Execute the full ingestion pipeline.

        Args:
            urls: List of URLs to ingest. If None, reads from data/raw/manifest.json.

        Returns:
            Summary dict with urls_processed, chunks_created, errors
        """
        if urls is None:
            urls = self._read_urls_from_manifest()

        results = {
            "status": "success",
            "urls_processed": 0,
            "chunks_created": 0,
            "errors": [],
        }

        for url in urls:
            try:
                # Step 1: Load from raw snapshot
                raw_text, metadata = self._load_from_raw(url)
                if not raw_text:
                    results["errors"].append(
                        {"url": url, "error": "No content loaded"}
                    )
                    continue

                # Step 2: Chunk (skip chunking for TER Excel - already chunked)
                if metadata.get("doc_type") == "ter_report" and metadata.get("is_excel", False):
                    # TER Excel files are already parsed into natural-language chunks
                    ter_chunks = self._load_ter_from_raw(url)
                    chunks = []
                    for tc in ter_chunks:
                        chunks.append({
                            "chunk_id": str(uuid.uuid4()),
                            "text": tc["text"],
                            "metadata": {**tc["metadata"], "chunk_index": 0},
                        })
                else:
                    chunks = self.chunker.split(raw_text, metadata)

                # Step 3: Embed
                chunks_with_embeddings = self.embedder.embed_chunks(chunks)

                # Step 4: Store
                self.vector_store.add_batch(chunks_with_embeddings)

                results["urls_processed"] += 1
                results["chunks_created"] += len(chunks)

                logger.info(
                    f"Ingested {url}: {len(chunks)} chunks"
                )

            except Exception as e:
                logger.error(f"Error ingesting {url}: {e}")
                results["errors"].append({"url": url, "error": str(e)})

        if results["errors"]:
            results["status"] = "partial_success"

        return results

    def run_from_csv(self, csv_path: str = "data/sources.csv") -> dict:
        """
        Read URLs from CSV and run ingestion.

        Args:
            csv_path: Path to sources CSV file

        Returns:
            Summary dict
        """
        urls = self._read_urls_from_csv(csv_path)
        return self.run(urls)

    def _read_urls_from_manifest(self) -> list:
        """Read URLs from data/raw/manifest.json."""
        manifest_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "raw", "manifest.json"
        )
        manifest_path = os.path.normpath(manifest_path)

        if not os.path.exists(manifest_path):
            logger.warning(f"Manifest not found at {manifest_path}, falling back to sources.csv")
            return self._read_urls_from_csv()

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        return [entry["source_url"] for entry in manifest]

    def _load_from_raw(self, url: str) -> tuple:
        """Load raw content from data/raw/ using the manifest."""
        manifest_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "raw", "manifest.json"
        )
        manifest_path = os.path.normpath(manifest_path)

        if not os.path.exists(manifest_path):
            return "", {}

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        # Find the entry for this URL
        entry = None
        for e in manifest:
            if e["source_url"] == url:
                entry = e
                break

        if entry is None:
            return "", {}

        filepath = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "raw", entry["filename"]
        )
        filepath = os.path.normpath(filepath)

        if not os.path.exists(filepath):
            return "", {}

        # Read the file
        with open(filepath, "rb") as f:
            content = f.read()

        # Determine file type and extract text
        filename = entry["filename"]
        is_excel = filename.endswith((".xls", ".xlsx", ".xlsm"))
        is_pdf = filename.endswith(".pdf")

        if is_excel:
            # For Excel files, we need to parse them specially
            # Return a marker so the pipeline knows to use _load_ter_from_raw
            return "EXCEL_PLACEHOLDER", {
                "source_url": url,
                "doc_type": entry.get("doc_type", "ter_report"),
                "scheme_name": entry.get("scheme_name", ""),
                "is_excel": True,
                "filepath": filepath,
            }
        elif is_pdf:
            # For PDFs, extract text
            return self._extract_pdf_text(filepath, url, entry)
        else:
            # For HTML, parse it
            return self._extract_html_text(content, url, entry)

    def _extract_html_text(self, content: bytes, url: str, entry: dict) -> tuple:
        """Extract text from HTML content."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")

        # Remove script, style, nav, footer elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Try to find main content
        main_content = soup.find("main") or soup.find("body")
        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)

        metadata = {
            "source_url": url,
            "doc_type": entry.get("doc_type", "unknown"),
            "scheme_name": entry.get("scheme_name", ""),
        }

        return text, metadata

    def _extract_pdf_text(self, filepath: str, url: str, entry: dict) -> tuple:
        """Extract text from PDF file."""
        import pdfplumber

        text_parts = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        text = "\n".join(text_parts)

        metadata = {
            "source_url": url,
            "doc_type": entry.get("doc_type", "unknown"),
            "scheme_name": entry.get("scheme_name", ""),
        }

        return text, metadata

    def _load_ter_from_raw(self, url: str) -> list:
        """Load TER Excel from raw file and parse into natural-language chunks."""
        import pandas as pd

        manifest_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "raw", "manifest.json"
        )
        manifest_path = os.path.normpath(manifest_path)

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        entry = None
        for e in manifest:
            if e["source_url"] == url:
                entry = e
                break

        if entry is None:
            return []

        filepath = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "raw", entry["filename"]
        )
        filepath = os.path.normpath(filepath)

        if not os.path.exists(filepath):
            return []

        # Parse the Excel file
        df = pd.read_excel(filepath, sheet_name=0, header=2)

        chunks = []
        cols = list(df.columns)
        col_map = {
            "scheme_name": cols[0],
            "scheme_code": cols[1],
            "date": cols[2],
            "base_regular": cols[3],
            "total_regular": cols[7],
            "base_direct": cols[8],
            "total_direct": cols[12],
        }

        for _, row in df.iterrows():
            try:
                scheme_name = str(row[col_map["scheme_name"]]).strip()
                if not scheme_name or scheme_name == "nan":
                    continue

                scheme_code = str(row[col_map["scheme_code"]]).strip()
                date_val = str(row[col_map["date"]]).strip()

                for plan_type, base_key, total_key in [
                    ("Regular", "base_regular", "total_regular"),
                    ("Direct", "base_direct", "total_direct"),
                ]:
                    base_ter = row[col_map[base_key]]
                    total_ter = row[col_map[total_key]]

                    if pd.isna(base_ter) or pd.isna(total_ter):
                        continue

                    try:
                        base_ter = float(base_ter)
                        total_ter = float(total_ter)
                    except (ValueError, TypeError):
                        continue

                    chunk_text = f"{scheme_name} ({plan_type} Plan) expense ratio (TER)"
                    if date_val and date_val != "nan":
                        chunk_text += f" as of {date_val}"
                    chunk_text += f": Base TER {base_ter}%, Total TER {total_ter}%"
                    if scheme_code and scheme_code != "nan":
                        chunk_text += f". Scheme code: {scheme_code}."

                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "source_url": url,
                            "doc_type": "ter_report",
                            "scheme_name": scheme_name,
                            "plan_type": plan_type,
                            "date": date_val,
                        }
                    })
            except Exception as e:
                logger.warning(f"Error parsing TER row: {e}")
                continue

        # Keep only the latest date per scheme+plan combination
        latest_chunks = {}
        for chunk in chunks:
            key = (chunk["metadata"]["scheme_name"], chunk["metadata"]["plan_type"])
            existing = latest_chunks.get(key)
            if existing is None or chunk["metadata"]["date"] > existing["metadata"]["date"]:
                latest_chunks[key] = chunk

        return list(latest_chunks.values())

    def _read_urls_from_csv(
        self, csv_path: str = "data/sources.csv"
    ) -> list:
        """Read URLs from the sources CSV file."""
        # Try relative to project root
        if not os.path.exists(csv_path):
            csv_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "data", "sources.csv"
            )
            csv_path = os.path.normpath(csv_path)

        urls = []
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                urls.append(row["url"])

        return urls


def main():
    """Run the full ingestion pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    pipeline = IngestionPipeline(CONFIG)
    results = pipeline.run_from_csv()

    print("\n" + "=" * 50)
    print("INGESTION SUMMARY")
    print("=" * 50)
    print(f"Status: {results['status']}")
    print(f"URLs processed: {results['urls_processed']}")
    print(f"Chunks created: {results['chunks_created']}")
    print(f"Errors: {len(results['errors'])}")

    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  - {error['url']}: {error['error']}")


if __name__ == "__main__":
    main()
