"""End-to-end tests for the RAG bot."""

import os
import sys
import unittest

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config.settings import CONFIG
from src.retrieval.pipeline import RetrievalPipeline


class TestEndToEnd(unittest.TestCase):
    """End-to-end tests for the full RAG pipeline."""

    @classmethod
    def setUpClass(cls):
        """Set up the retrieval pipeline once for all tests."""
        cls.pipeline = RetrievalPipeline(CONFIG)

    def test_factual_query_returns_answer(self):
        """Test that a factual query returns an answer with source."""
        result = self.pipeline.query("What is the ELSS lock-in period?")

        self.assertIn("answer", result)
        self.assertIn("source_url", result)
        self.assertIn("is_refusal", result)
        self.assertIn("confidence", result)
        self.assertFalse(result["is_refusal"])

    def test_advice_query_returns_refusal(self):
        """Test that an advice query returns a refusal."""
        result = self.pipeline.query("Should I buy HDFC Flexi Cap Fund?")

        self.assertTrue(result["is_refusal"])
        self.assertIn("factual information", result["answer"])
        self.assertIn("sebi.gov.in", result["source_url"])

    def test_no_results_returns_message(self):
        """Test that a query with no results returns appropriate message."""
        result = self.pipeline.query("What is the weather today?")

        self.assertFalse(result["is_refusal"])
        # Either returns "no information" or a low-confidence answer
        self.assertTrue(
            "don't have information" in result["answer"]
            or result["confidence"] < 0.5
        )

    def test_query_with_expense_ratio(self):
        """Test expense ratio query returns relevant results."""
        result = self.pipeline.query("What is the expense ratio of HDFC Flexi Cap?")

        self.assertFalse(result["is_refusal"])
        self.assertGreater(result["confidence"], 0.3)

    def test_query_with_minimum_sip(self):
        """Test minimum SIP query returns relevant results."""
        result = self.pipeline.query("What is the minimum SIP amount?")

        self.assertFalse(result["is_refusal"])
        self.assertIsInstance(result["answer"], str)


if __name__ == "__main__":
    unittest.main()
