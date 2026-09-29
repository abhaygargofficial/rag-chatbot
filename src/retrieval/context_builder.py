"""Context Builder module for constructing prompts from retrieved chunks."""


class ContextBuilder:
    """Builds prompts from retrieved chunks for LLM generation."""

    def __init__(self, max_chunks: int = 5):
        """
        Initialize the ContextBuilder.

        Args:
            max_chunks: Maximum number of chunks to include in context
        """
        self.max_chunks = max_chunks
        self.system_prompt = (
            "You are a facts-only mutual fund FAQ assistant. "
            "Answer using ONLY the provided context. "
            "Include one source link. "
            "Keep answers to 3 sentences or fewer. "
            "If the question asks for investment advice, politely decline and provide an educational link. "
            "Always add 'Last updated from sources: [URL]' at the end of your answer."
        )

    def build(self, query: str, search_results: list) -> str:
        """
        Build a complete prompt from query and search results.

        Args:
            query: The user's query
            search_results: List of search result dicts

        Returns:
            Formatted prompt string
        """
        # Build context section
        context_parts = []
        for i, result in enumerate(search_results[: self.max_chunks]):
            context_parts.append(
                f"[Context {i+1}]\n{result['text']}\nSource: {result['source_url']}"
            )

        context_section = "\n\n".join(context_parts)

        # Build full prompt
        prompt = f"{self.system_prompt}\n\n{context_section}\n\nUser Query: {query}\n\nAnswer:"

        return prompt

    def build_refusal_prompt(self) -> str:
        """
        Build a prompt for refusal responses.

        Returns:
            Refusal prompt string
        """
        return (
            "The user is asking for investment advice. "
            "Respond with a polite refusal and provide an educational link to "
            "SEBI's investor education page: https://www.sebi.gov.in/sebi_data/commondocs/siep_h.html"
        )

    def main(self):
        """Test the context builder with sample results."""
        builder = ContextBuilder()
        results = [
            {
                "text": "The expense ratio of HDFC Flexi Cap Fund Direct is 0.71%.",
                "source_url": "https://www.hdfcfund.com/statutory-disclosure/total-expense-ratio-of-mutual-fund-schemes/reports",
                "score": 0.95,
            },
            {
                "text": "HDFC Flexi Cap Fund is a diversified equity fund.",
                "source_url": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/direct",
                "score": 0.87,
            },
        ]
        prompt = builder.build("What is the expense ratio?", results)
        print(prompt)


if __name__ == "__main__":
    builder = ContextBuilder()
    builder.main()
