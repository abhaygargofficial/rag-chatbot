"""Vector Store module for ChromaDB persistence and search."""

import logging
from typing import List, Optional

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages ChromaDB collection for storing and searching vectors."""

    def __init__(
        self,
        persist_dir: str = "./data/chroma_db",
        collection_name: str = "mutual_fund_faq",
    ):
        """
        Initialize the Vector Store.

        Args:
            persist_dir: Directory for ChromaDB persistence
            collection_name: Name of the collection
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, chunks: List[dict], embeddings: List[List[float]]):
        """
        Add chunks with embeddings to the store.

        Args:
            chunks: List of chunk dicts
            embeddings: List of embedding vectors
        """
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(ids)} chunks to {self.collection_name}")

    def add_batch(
        self, chunks_with_embeddings: List[dict], batch_size: int = 100
    ):
        """
        Add chunks in batches to avoid memory issues.

        Args:
            chunks_with_embeddings: List of chunk dicts with 'embedding' key
            batch_size: Number of chunks per batch
        """
        for i in range(0, len(chunks_with_embeddings), batch_size):
            batch = chunks_with_embeddings[i : i + batch_size]
            embeddings = [chunk["embedding"] for chunk in batch]
            self.add(batch, embeddings)

    def count(self) -> int:
        """Return the number of chunks in the collection."""
        return self.collection.count()

    def search(
        self, query_embedding: List[float], n_results: int = 5
    ) -> List[dict]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query vector
            n_results: Number of results to return

        Returns:
            List of dicts with chunk_id, text, source_url, score
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # Convert distance to similarity score (1 - distance for cosine)
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

        return output

    def clear(self):
        """Delete and recreate the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Cleared collection {self.collection_name}")

    def main(self):
        """Test the vector store."""
        store = VectorStore()
        print(f"Collection count: {store.count()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    store = VectorStore()
    store.main()
