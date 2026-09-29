"""Embedding Engine module for generating vector embeddings."""

from typing import List

from sentence_transformers import SentenceTransformer


class Embedder:
    """Generates dense vector embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the Embedder.

        Args:
            model_name: The sentence-transformers model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.batch_size = 32

    def embed(self, text: str) -> List[float]:
        """
        Embed a single text string.

        Args:
            text: Text to embed

        Returns:
            List of 384 floats (the embedding vector)
        """
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return embeddings.tolist()

    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        Embed a list of chunk dicts.

        Args:
            chunks: List of chunk dicts with 'text' key

        Returns:
            Chunks with 'embedding' key added
        """
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embed_batch(texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding

        return chunks

    def main(self):
        """Test the embedder with sample texts."""
        sample_texts = [
            "What is the expense ratio of HDFC Flexi Cap Fund?",
            "ELSS funds have a 3-year lock-in period.",
            "Minimum SIP amount varies by scheme.",
        ]
        embedder = Embedder()
        embeddings = embedder.embed_batch(sample_texts)
        print(f"Embedded {len(embeddings)} texts")
        print(f"Embedding dimensions: {len(embeddings[0])}")


if __name__ == "__main__":
    embedder = Embedder()
    embedder.main()
