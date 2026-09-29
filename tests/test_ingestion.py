"""Tests for the ingestion pipeline modules."""

import os
import sys
import unittest

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ingestion.loader import URLLoader
from src.ingestion.chunker import Chunker
from src.ingestion.embedder import Embedder
from src.ingestion.vector_store import VectorStore


class TestURLLoader(unittest.TestCase):
    """Test cases for URLLoader."""

    def setUp(self):
        self.loader = URLLoader()

    def test_detect_doc_type_scheme_page(self):
        url = "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/direct"
        self.assertEqual(self.loader.detect_doc_type(url), "scheme_page")

    def test_detect_doc_type_factsheet(self):
        url = "https://www.hdfcfund.com/mutual-funds/factsheets"
        self.assertEqual(self.loader.detect_doc_type(url), "factsheet")

    def test_detect_doc_type_kim(self):
        url = "https://www.hdfcfund.com/investor-services/fund-documents/kim"
        self.assertEqual(self.loader.detect_doc_type(url), "kim")

    def test_detect_doc_type_sid(self):
        url = "https://www.hdfcfund.com/investor-services/fund-documents/sid"
        self.assertEqual(self.loader.detect_doc_type(url), "sid")

    def test_detect_doc_type_ter_report(self):
        url = "https://www.hdfcfund.com/statutory-disclosure/total-expense-ratio-of-mutual-fund-schemes/reports"
        self.assertEqual(self.loader.detect_doc_type(url), "ter_report")

    def test_detect_doc_type_education(self):
        url = "https://www.sebi.gov.in/sebiweb/other/mutualfunds.jsp"
        self.assertEqual(self.loader.detect_doc_type(url), "education")

    def test_detect_scheme_name_flexi_cap(self):
        url = "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/direct"
        self.assertEqual(self.loader.detect_scheme_name(url), "HDFC Flexi Cap Fund")

    def test_detect_scheme_name_small_cap(self):
        url = "https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct"
        self.assertEqual(self.loader.detect_scheme_name(url), "HDFC Small Cap Fund")

    def test_detect_scheme_name_elss(self):
        url = "https://www.hdfcfund.com/explore/mutual-funds/hdfc-elss-tax-saver-fund/direct"
        self.assertEqual(
            self.loader.detect_scheme_name(url), "HDFC ELSS Tax Saver Fund"
        )

    def test_detect_scheme_name_general(self):
        url = "https://www.hdfcfund.com/mutual-funds/factsheets"
        self.assertEqual(self.loader.detect_scheme_name(url), "general")

    def test_load_html_page(self):
        """Test loading a real HTML page (requires internet)."""
        url = "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/direct"
        text, meta = self.loader.load(url)
        self.assertIsInstance(text, str)
        self.assertIsInstance(meta, dict)
        self.assertIn("source_url", meta)
        self.assertIn("doc_type", meta)
        self.assertIn("scheme_name", meta)


class TestChunker(unittest.TestCase):
    """Test cases for Chunker."""

    def setUp(self):
        self.chunker = Chunker(chunk_size=100, chunk_overlap=20)

    def test_split_creates_chunks(self):
        text = "This is a test sentence. " * 50
        metadata = {"source_url": "http://test.com", "doc_type": "test"}
        chunks = self.chunker.split(text, metadata)
        self.assertGreater(len(chunks), 0)

    def test_chunks_have_required_fields(self):
        text = "This is a test sentence. " * 50
        metadata = {"source_url": "http://test.com", "doc_type": "test"}
        chunks = self.chunker.split(text, metadata)

        for chunk in chunks:
            self.assertIn("chunk_id", chunk)
            self.assertIn("text", chunk)
            self.assertIn("metadata", chunk)
            self.assertIn("chunk_index", chunk["metadata"])
            self.assertIn("source_url", chunk["metadata"])

    def test_split_batch(self):
        texts = [
            ("First text " * 50, {"source_url": "http://test1.com"}),
            ("Second text " * 50, {"source_url": "http://test2.com"}),
        ]
        chunks = self.chunker.split_batch(texts)
        self.assertGreater(len(chunks), 0)


class TestEmbedder(unittest.TestCase):
    """Test cases for Embedder."""

    def setUp(self):
        self.embedder = Embedder()

    def test_embed_returns_384_dim(self):
        embedding = self.embedder.embed("test text")
        self.assertEqual(len(embedding), 384)

    def test_embed_batch(self):
        texts = ["test one", "test two", "test three"]
        embeddings = self.embedder.embed_batch(texts)
        self.assertEqual(len(embeddings), 3)
        for emb in embeddings:
            self.assertEqual(len(emb), 384)

    def test_embed_chunks(self):
        chunks = [
            {"chunk_id": "1", "text": "test one", "metadata": {}},
            {"chunk_id": "2", "text": "test two", "metadata": {}},
        ]
        result = self.embedder.embed_chunks(chunks)
        self.assertEqual(len(result), 2)
        for chunk in result:
            self.assertIn("embedding", chunk)
            self.assertEqual(len(chunk["embedding"]), 384)


class TestVectorStore(unittest.TestCase):
    """Test cases for VectorStore."""

    def setUp(self):
        self.store = VectorStore()

    def test_count(self):
        count = self.store.count()
        self.assertIsInstance(count, int)

    def test_add_and_search(self):
        # Create test chunks
        chunks = [
            {
                "chunk_id": "test-1",
                "text": "HDFC Flexi Cap Fund expense ratio",
                "metadata": {"source_url": "http://test.com", "doc_type": "test"},
            }
        ]
        embeddings = [[0.1] * 384]

        self.store.add(chunks, embeddings)
        self.assertGreater(self.store.count(), 0)

        # Search
        results = self.store.search([0.1] * 384, n_results=1)
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
