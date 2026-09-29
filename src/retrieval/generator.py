"""LLM Generator module for producing answers with citations using Groq."""

import logging
import os
import re
import time

from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Generator:
    """Generates answers using Groq's LLM with citations."""

    def __init__(
        self,
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 150,
    ):
        """
        Initialize the Generator.

        Args:
            model: Groq model name (defaults to env var GROQ_MODEL or llama-3.1-8b-instant)
            temperature: Sampling temperature (low for factual answers)
            max_tokens: Maximum tokens in response
        """
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None

    def _get_client(self):
        """Lazy initialization of Groq client."""
        if self.client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key or api_key == "your-groq-api-key-here":
                raise ValueError(
                    "GROQ_API_KEY not set. Please set it in .env file."
                )
            self.client = Groq(api_key=api_key)
        return self.client

    def generate(self, prompt: str) -> dict:
        """
        Generate an answer from the prompt.

        Args:
            prompt: The formatted prompt with context

        Returns:
            Dict with answer and source_url
        """
        try:
            client = self._get_client()

            # Split prompt into system message and user message
            parts = prompt.split("\n\nUser Query:")
            system_message = parts[0]
            user_message = (
                parts[1].replace("\n\nAnswer:", "").strip()
                if len(parts) > 1
                else prompt
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            answer = response.choices[0].message.content.strip()
            source_url = self.extract_source_url(prompt)

            return {"answer": answer, "source_url": source_url}

        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return {
                "answer": str(e),
                "source_url": "",
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "answer": "Sorry, an unexpected error occurred. Please try again.",
                "source_url": "",
            }

    def generate_refusal(self) -> dict:
        """
        Generate a refusal response for advice questions.

        Returns:
            Dict with refusal answer and educational link
        """
        return {
            "answer": (
                "I can only provide factual information, not investment advice. "
                "For educational resources, visit SEBI's investor education page."
            ),
            "source_url": "https://www.sebi.gov.in/sebi_data/commondocs/siep_h.html",
        }

    def extract_source_url(self, prompt: str) -> str:
        """
        Extract the first source URL from the prompt.

        Args:
            prompt: The formatted prompt

        Returns:
            Source URL or empty string
        """
        match = re.search(r"Source: (https?://[^\s]+)", prompt)
        return match.group(1) if match else ""

    def main(self):
        """Test the generator with a sample prompt."""
        generator = Generator()
        prompt = (
            "System: You are a helpful assistant.\n\n"
            "Context: The expense ratio is 0.5%.\n"
            "Source: http://test.com\n\n"
            "User Query: What is the expense ratio?\n\n"
            "Answer:"
        )
        result = generator.generate(prompt)
        print(f"Answer: {result['answer']}")
        print(f"Source: {result['source_url']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generator = Generator()
    generator.main()
