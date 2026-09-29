"""Retrieval Pipeline orchestrator for the RAG bot."""

import logging

from src.config.settings import CONFIG
from .query_processor import QueryProcessor
from .searcher import Searcher
from .context_builder import ContextBuilder
from .generator import Generator

logger = logging.getLogger(__name__)


class RetrievalPipeline:
    """Orchestrates the full data retrieval pipeline."""

    def __init__(self, config: dict):
        """
        Initialize the Retrieval Pipeline.

        Args:
            config: Configuration dict with persist_dir, collection_name,
                   embedding_model, top_k, llm_model, temperature, max_tokens
        """
        self.config = config
        self.query_processor = QueryProcessor()
        self.searcher = Searcher(
            persist_dir=config.get("persist_dir", "./data/chroma_db"),
            collection_name=config.get("collection_name", "mutual_fund_faq"),
            embedding_model=config.get(
                "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
            ),
        )
        self.context_builder = ContextBuilder(
            max_chunks=config.get("top_k", 5)
        )
        self.generator = Generator(
            model=config.get("llm_model", "gpt-3.5-turbo"),
            temperature=config.get("temperature", 0.1),
            max_tokens=config.get("max_tokens", 150),
        )

    def query(self, question: str) -> dict:
        """
        Execute the full retrieval pipeline.

        Args:
            question: User's question

        Returns:
            Dict with answer, source_url, is_refusal, confidence
        """
        # Step 1: Process query
        processed = self.query_processor.process(question)

        # Step 2: Check intent
        if processed["is_advice"]:
            return self._refusal_response()

        # Step 3: Search
        results = self.searcher.search(
            processed["normalized"],
            n_results=self.config.get("top_k", 5),
            threshold=self.config.get("similarity_threshold", 0.5),
        )

        # Step 4: Handle no results
        if not results:
            return self._no_results_response()

        # Step 5: Build context
        prompt = self.context_builder.build(
            processed["normalized"], results
        )

        # Step 6: Generate
        response = self.generator.generate(prompt)

        return {
            "answer": response["answer"],
            "source_url": response["source_url"],
            "is_refusal": False,
            "confidence": results[0]["score"] if results else 0.0,
        }

    def _refusal_response(self) -> dict:
        """Return a refusal response for advice questions."""
        return {
            "answer": (
                "I can only provide factual information, not investment advice. "
                "For educational resources, visit SEBI's investor education page."
            ),
            "source_url": "https://www.sebi.gov.in/sebi_data/commondocs/siep_h.html",
            "is_refusal": True,
            "confidence": 1.0,
        }

    def _no_results_response(self) -> dict:
        """Return a response when no relevant chunks are found."""
        return {
            "answer": "I don't have information on that topic.",
            "source_url": "",
            "is_refusal": False,
            "confidence": 0.0,
        }


def main():
    """Run the full retrieval pipeline with test queries."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    pipeline = RetrievalPipeline(CONFIG)

    test_queries = [
        "What is the ELSS lock-in period?",
        "What is the expense ratio of HDFC Flexi Cap Fund?",
        "Should I buy HDFC Flexi Cap Fund?",
    ]

    for question in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {question}")
        print(f"{'='*50}")
        result = pipeline.query(question)
        print(f"Answer: {result['answer']}")
        print(f"Source: {result['source_url']}")
        print(f"Refusal: {result['is_refusal']}")
        print(f"Confidence: {result['confidence']:.3f}")


if __name__ == "__main__":
    main()
