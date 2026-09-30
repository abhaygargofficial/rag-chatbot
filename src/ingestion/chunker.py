"""Chunker module for splitting text into overlapping chunks with metadata."""

import uuid
from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter


class Chunker:
    """Splits text into chunks with metadata for RAG ingestion."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 160):
        """
        Initialize the Chunker.

        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split(self, text: str, metadata: dict) -> List[dict]:
        """
        Split text into chunks with metadata.

        Args:
            text: Raw text to split
            metadata: Metadata dict with source_url, doc_type, scheme_name

        Returns:
            List of chunk dicts with chunk_id, text, and metadata
        """
        chunks = self.splitter.split_text(text)
        result = []

        for idx, chunk_text in enumerate(chunks):
            chunk = {
                "chunk_id": str(uuid.uuid4()),
                "text": chunk_text,
                "metadata": {
                    **metadata,
                    "chunk_index": idx,
                    "char_start": text.find(chunk_text),
                    "char_end": text.find(chunk_text) + len(chunk_text),
                },
            }
            result.append(chunk)

        return result

    def split_batch(self, texts_with_metadata: List[Tuple[str, dict]]) -> List[dict]:
        """
        Process multiple texts at once.

        Args:
            texts_with_metadata: List of (text, metadata) tuples

        Returns:
            Combined list of chunk dicts
        """
        all_chunks = []
        for text, metadata in texts_with_metadata:
            chunks = self.split(text, metadata)
            all_chunks.extend(chunks)
        return all_chunks

    def main(self):
        """Test the chunker with sample text."""
        sample_text = "This is a test sentence. " * 100
        metadata = {
            "source_url": "http://test.com",
            "doc_type": "test",
            "scheme_name": "test",
        }
        chunks = self.split(sample_text, metadata)
        print(f"Created {len(chunks)} chunks from {len(sample_text)} chars")
        for i, chunk in enumerate(chunks[:3]):
            print(f"  Chunk {i}: {len(chunk['text'])} chars")


if __name__ == "__main__":
    chunker = Chunker()
    chunker.main()
