"""Vector Searcher module for ChromaDB similarity search."""

import logging
from typing import Optional

import chromadb

from src.ingestion.embedder import Embedder

logger = logging.getLogger(__name__)


class Searcher:
    """Searches ChromaDB for relevant chunks based on query embedding."""

    def __init__(
        self,
        persist_dir: str,
        collection_name: str,
        embedding_model: str,
    ):
        """
        Initialize the Searcher.

        Args:
            persist_dir: ChromaDB persistence directory
            collection_name: Name of the collection
            embedding_model: Sentence-transformers model name
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedder = Embedder(model_name=embedding_model)

    def search(
        self,
        query: str,
        n_results: int = 5,
        threshold: float = 0.5,
    ) -> list:
        """
        Search for similar chunks.

        Args:
            query: The search query
            n_results: Number of results to return
            threshold: Minimum similarity score

        Returns:
            List of dicts with chunk_id, text, source_url, score, metadata
        """
        # Embed the query
        query_embedding = self.embedder.embed(query)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # Convert distance to similarity score
                distance = results["distances"][0][i]
                score = 1 - distance

                # Filter by threshold
                if score < threshold:
                    continue

                output.append(
                    {
                        "chunk_id": chunk_id,
                        "text": results["documents"][0][i],
                        "source_url": results["metadatas"][0][i].get(
                            "source_url", ""
                        ),
                        "score": score,
                        "metadata": results["metadatas"][0][i],
                    }
                )

        # Sort by score descending
        output.sort(key=lambda x: x["score"], reverse=True)

        return output

    def search_with_filters(
        self,
        query: str,
        filters: Optional[dict] = None,
        n_results: int = 5,
    ) -> list:
        """
        Search with metadata filters.

        Args:
            query: The search query
            filters: Metadata filters (e.g., {"scheme_name": "HDFC Flexi Cap"})
            n_results: Number of results to return

        Returns:
            List of dicts with chunk_id, text, source_url, score, metadata
        """
        query_embedding = self.embedder.embed(query)

        # Build where clause from filters
        where_clause = None
        if filters:
            where_clause = filters

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                score = 1 - distance

                output.append(
                    {
                        "chunk_id": chunk_id,
                        "text": results["documents"][0][i],
                        "source_url": results["metadatas"][0][i].get(
                            "source_url", ""
                        ),
                        "score": score,
                        "metadata": results["metadatas"][0][i],
                    }
                )

        output.sort(key=lambda x: x["score"], reverse=True)
        return output

    def main(self):
        """Test the searcher with a sample query."""
        searcher = Searcher(
            persist_dir="./data/chroma_db",
            collection_name="mutual_fund_faq",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        )
        results = searcher.search("expense ratio")
        print(f"Found {len(results)} results")
        for i, result in enumerate(results):
            print(f"  {i+1}. Score: {result['score']:.3f} | {result['text'][:80]}...")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    searcher = Searcher(
        persist_dir="./data/chroma_db",
        collection_name="mutual_fund_faq",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    )
    searcher.main()
