"""Tests for the retrieval pipeline modules."""

import os
import sys
import unittest

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.retrieval.query_processor import QueryProcessor
from src.retrieval.searcher import Searcher
from src.retrieval.context_builder import ContextBuilder
from src.retrieval.generator import Generator


class TestQueryProcessor(unittest.TestCase):
    """Test cases for QueryProcessor."""

    def setUp(self):
        self.processor = QueryProcessor()

    def test_detect_intent_advice(self):
        result = self.processor.detect_intent("Should I buy HDFC Flexi Cap?")
        self.assertEqual(result, "advice")

    def test_detect_intent_factual(self):
        result = self.processor.detect_intent("What is the expense ratio?")
        self.assertEqual(result, "factual")

    def test_normalize_lowercase(self):
        result = self.processor.normalize("What is the Expense Ratio?")
        self.assertEqual(result, "what is the expense ratio?")

    def test_normalize_expands_abbreviations(self):
        result = self.processor.normalize("What is ELSS?")
        self.assertIn("equity linked savings scheme", result)

    def test_process_returns_correct_format(self):
        result = self.processor.process("Should I buy?")
        self.assertIn("original", result)
        self.assertIn("normalized", result)
        self.assertIn("is_advice", result)
        self.assertIn("intent", result)
        self.assertTrue(result["is_advice"])


class TestSearcher(unittest.TestCase):
    """Test cases for Searcher."""

    def setUp(self):
        self.searcher = Searcher(
            persist_dir="./data/chroma_db",
            collection_name="mutual_fund_faq",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        )

    def test_search_returns_results(self):
        results = self.searcher.search("expense ratio", n_results=3)
        self.assertIsInstance(results, list)

    def test_search_results_have_required_fields(self):
        results = self.searcher.search("expense ratio", n_results=3)
        for result in results:
            self.assertIn("chunk_id", result)
            self.assertIn("text", result)
            self.assertIn("source_url", result)
            self.assertIn("score", result)

    def test_search_with_filters(self):
        results = self.searcher.search_with_filters(
            "expense ratio", filters={"doc_type": "ter_report"}, n_results=3
        )
        self.assertIsInstance(results, list)


class TestContextBuilder(unittest.TestCase):
    """Test cases for ContextBuilder."""

    def setUp(self):
        self.builder = ContextBuilder(max_chunks=3)

    def test_build_returns_string(self):
        results = [
            {"text": "Test chunk", "source_url": "http://test.com", "score": 0.9}
        ]
        prompt = self.builder.build("test query", results)
        self.assertIsInstance(prompt, str)

    def test_build_includes_system_prompt(self):
        results = [
            {"text": "Test chunk", "source_url": "http://test.com", "score": 0.9}
        ]
        prompt = self.builder.build("test query", results)
        self.assertIn("facts-only", prompt)

    def test_build_includes_context(self):
        results = [
            {"text": "Test chunk content", "source_url": "http://test.com", "score": 0.9}
        ]
        prompt = self.builder.build("test query", results)
        self.assertIn("Test chunk content", prompt)
        self.assertIn("http://test.com", prompt)

    def test_build_refusal_prompt(self):
        prompt = self.builder.build_refusal_prompt()
        self.assertIsInstance(prompt, str)
        self.assertIn("investment advice", prompt)


class TestGenerator(unittest.TestCase):
    """Test cases for Generator."""

    def setUp(self):
        self.generator = Generator()

    def test_generate_refusal(self):
        result = self.generator.generate_refusal()
        self.assertIn("answer", result)
        self.assertIn("source_url", result)
        self.assertIn("factual information", result["answer"])

    def test_extract_source_url(self):
        prompt = "Context: test\nSource: https://example.com/page\n\nQuery: test"
        url = self.generator.extract_source_url(prompt)
        self.assertEqual(url, "https://example.com/page")

    def test_extract_source_url_not_found(self):
        prompt = "No source here"
        url = self.generator.extract_source_url(prompt)
        self.assertEqual(url, "")


if __name__ == "__main__":
    unittest.main()
