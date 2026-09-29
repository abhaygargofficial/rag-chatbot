"""Query Processor module for intent detection and normalization."""

import re


class QueryProcessor:
    """Processes user queries with intent detection and normalization."""

    def __init__(self):
        """Initialize the QueryProcessor with advice keywords and abbreviations."""
        self.advice_keywords = [
            "should i buy",
            "should i sell",
            "best fund",
            "recommend",
            "which fund for me",
            "portfolio advice",
            "investment advice",
            "what should i invest",
            "is it good to buy",
            "should i invest",
            "which is better",
            "top fund",
            "good fund to invest",
        ]
        self.abbreviation_mappings = {
            "elss": "equity linked savings scheme",
            "sip": "systematic investment plan",
            "ter": "total expense ratio",
            "kim": "key information memorandum",
            "sid": "scheme information document",
            "amc": "asset management company",
            "nav": "net asset value",
        }

    def detect_intent(self, query: str) -> str:
        """
        Detect if the query is asking for advice or factual information.

        Args:
            query: The user's query

        Returns:
            "advice" if query contains advice keywords, "factual" otherwise
        """
        query_lower = query.lower()
        for keyword in self.advice_keywords:
            if keyword in query_lower:
                return "advice"
        return "factual"

    def normalize(self, query: str) -> str:
        """
        Normalize the query by lowercasing and expanding abbreviations.

        Args:
            query: The user's query

        Returns:
            Normalized query string
        """
        # Lowercase
        normalized = query.lower().strip()

        # Expand abbreviations
        for abbr, full_form in self.abbreviation_mappings.items():
            # Use word boundary to avoid partial matches
            pattern = r"\b" + re.escape(abbr) + r"\b"
            normalized = re.sub(pattern, full_form, normalized)

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def process(self, query: str) -> dict:
        """
        Process the query: detect intent and normalize.

        Args:
            query: The user's query

        Returns:
            Dict with original, normalized, is_advice, and intent
        """
        intent = self.detect_intent(query)
        normalized = self.normalize(query)

        return {
            "original": query,
            "normalized": normalized,
            "is_advice": intent == "advice",
            "intent": intent,
        }

    def main(self):
        """Test the query processor with sample queries."""
        processor = QueryProcessor()

        test_queries = [
            "Should I buy HDFC Flexi Cap?",
            "What is the expense ratio?",
            "Which fund is best for me?",
            "What is the ELSS lock-in period?",
        ]

        for query in test_queries:
            result = processor.process(query)
            print(f"Query: {query}")
            print(f"  Intent: {result['intent']}")
            print(f"  Normalized: {result['normalized']}")
            print()


if __name__ == "__main__":
    processor = QueryProcessor()
    processor.main()
