"""Ingestion Pipeline orchestrator for the RAG bot."""

import csv
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
            urls: List of URLs to ingest. If None, reads from sources.csv.

        Returns:
            Summary dict with urls_processed, chunks_created, errors
        """
        if urls is None:
            urls = self._read_urls_from_csv()

        results = {
            "status": "success",
            "urls_processed": 0,
            "chunks_created": 0,
            "errors": [],
        }

        for url in urls:
            try:
                # Step 1: Load
                raw_text, metadata = self.loader.load(url)
                if not raw_text:
                    results["errors"].append(
                        {"url": url, "error": "No content loaded"}
                    )
                    continue

                # Step 2: Chunk (skip chunking for TER Excel - already chunked)
                if "ter" in url.lower() and self.loader._is_excel(url):
                    # TER Excel files are already parsed into natural-language chunks
                    ter_chunks = self.loader._load_ter_excel(url)
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
