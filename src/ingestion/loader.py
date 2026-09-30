"""URL Loader module for fetching and parsing HTML pages and PDFs."""

import csv
import logging
import os
import tempfile
from typing import Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class URLLoader:
    """Loads and parses content from URLs (HTML pages and PDFs)."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def load(self, url: str) -> Tuple[str, dict]:
        """
        Load content from a URL.

        Args:
            url: The URL to load

        Returns:
            Tuple of (raw_text, metadata_dict)
        """
        try:
            doc_type = self.detect_doc_type(url)
            scheme_name = self.detect_scheme_name(url)

            if self._is_pdf(url):
                text = self._load_pdf(url)
            elif self._is_excel(url):
                if "ter" in url.lower() or "expense" in url.lower():
                    ter_chunks = self._load_ter_excel(url)
                    text = "\n\n".join(c["text"] for c in ter_chunks)
                else:
                    text = self._load_excel(url)
            else:
                text = self._load_html(url)

            metadata = {
                "source_url": url,
                "doc_type": doc_type,
                "scheme_name": scheme_name,
            }

            logger.info(f"Loaded {len(text)} chars from {url} (type: {doc_type})")
            return text, metadata

        except Exception as e:
            logger.error(f"Failed to load {url}: {e}")
            return "", {}

    def detect_doc_type(self, url: str) -> str:
        """Detect document type from URL patterns."""
        url_lower = url.lower()
        if "factsheet" in url_lower:
            return "factsheet"
        elif "kim" in url_lower:
            return "kim"
        elif "sid" in url_lower:
            return "sid"
        elif "total-expense-ratio" in url_lower or "ter" in url_lower:
            return "ter_report"
        elif url_lower.endswith((".xls", ".xlsx", ".xlsm")):
            return "ter_report"
        elif "statement" in url_lower or "capital-gain" in url_lower:
            return "statement_guide"
        elif "risk-o-meter" in url_lower or "riskometer" in url_lower:
            return "riskometer"
        elif "sebi" in url_lower or "amfi" in url_lower or "investor" in url_lower:
            return "education"
        elif "hdfcfund.com" in url_lower:
            return "scheme_page"
        return "general"

    def detect_scheme_name(self, url: str) -> str:
        """Detect scheme name from URL."""
        url_lower = url.lower()
        if "flexi-cap" in url_lower:
            return "HDFC Flexi Cap Fund"
        elif "small-cap" in url_lower:
            return "HDFC Small Cap Fund"
        elif "elss" in url_lower or "tax-saver" in url_lower:
            return "HDFC ELSS Tax Saver Fund"
        return "general"

    def _is_pdf(self, url: str) -> bool:
        """Check if URL points to a PDF."""
        return url.lower().endswith(".pdf")

    def _is_excel(self, url: str) -> bool:
        """Check if URL points to an Excel file."""
        return url.lower().endswith((".xls", ".xlsx", ".xlsm", ".csv"))

    def _load_html(self, url: str) -> str:
        """Fetch and parse HTML page."""
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script, style, nav, footer elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Try to find main content
        main_content = soup.find("main") or soup.find("body")
        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)

    def _load_pdf(self, url: str) -> str:
        """Download and parse PDF file."""
        import pdfplumber

        response = self.session.get(url, timeout=60)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        try:
            text_parts = []
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                    # Also extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            row_text = " | ".join(
                                cell for cell in row if cell
                            )
                            if row_text.strip():
                                text_parts.append(row_text)

            return "\n".join(text_parts)
        finally:
            os.unlink(tmp_path)

    def _load_excel(self, url: str) -> str:
        """Download and parse Excel file into natural-language chunks."""
        import pandas as pd

        response = self.session.get(url, timeout=60)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".xls", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        try:
            text_parts = []
            df = pd.read_excel(tmp_path, sheet_name=None)
            for sheet_name, sheet_df in df.items():
                text_parts.append(f"Sheet: {sheet_name}")
                for _, row in sheet_df.iterrows():
                    row_text = " | ".join(
                        str(cell) for cell in row if pd.notna(cell)
                    )
                    if row_text.strip():
                        text_parts.append(row_text)
            return "\n".join(text_parts)
        finally:
            os.unlink(tmp_path)

    def _load_ter_excel(self, url: str) -> list:
        """Download and parse TER Excel file into natural-language chunks.

        The Excel has a single sheet with a two-row header:
        - Row 0: Group labels (Regular Plan, Direct Plan)
        - Row 1: Actual column headers
        - Row 2+: Data

        Regular Plan columns: 3-7, Direct Plan columns: 8-12.

        Returns list of dicts with 'text' and 'metadata' keys.
        """
        import pandas as pd

        response = self.session.get(url, timeout=60)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".xls", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        try:
            chunks = []

            # Read with header=2 (skip group labels row, use actual headers)
            df = pd.read_excel(tmp_path, sheet_name=0, header=2)

            # Map columns by position (since headers may have duplicates)
            cols = list(df.columns)
            col_map = {
                "scheme_name": cols[0],
                "scheme_code": cols[1],
                "date": cols[2],
                "base_regular": cols[3],
                "total_regular": cols[7],
                "base_direct": cols[8],
                "total_direct": cols[12],
            }

            # Process each row
            for _, row in df.iterrows():
                try:
                    scheme_name = str(row[col_map["scheme_name"]]).strip()
                    if not scheme_name or scheme_name == "nan":
                        continue

                    scheme_code = str(row[col_map["scheme_code"]]).strip()
                    date_val = str(row[col_map["date"]]).strip()

                    # Create chunks for both Direct and Regular plans
                    for plan_type, base_key, total_key in [
                        ("Regular", "base_regular", "total_regular"),
                        ("Direct", "base_direct", "total_direct"),
                    ]:
                        base_ter = row[col_map[base_key]]
                        total_ter = row[col_map[total_key]]

                        if pd.isna(base_ter) or pd.isna(total_ter):
                            continue

                        try:
                            base_ter = float(base_ter)
                            total_ter = float(total_ter)
                        except (ValueError, TypeError):
                            continue

                        chunk_text = f"{scheme_name} ({plan_type} Plan) expense ratio (TER)"
                        if date_val and date_val != "nan":
                            chunk_text += f" as of {date_val}"
                        chunk_text += f": Base TER {base_ter}%, Total TER {total_ter}%"
                        if scheme_code and scheme_code != "nan":
                            chunk_text += f". Scheme code: {scheme_code}."

                        chunks.append({
                            "text": chunk_text,
                            "metadata": {
                                "source_url": url,
                                "doc_type": "ter_report",
                                "scheme_name": scheme_name,
                                "plan_type": plan_type,
                                "date": date_val,
                            }
                        })
                except Exception as e:
                    logger.warning(f"Error parsing TER row: {e}")
                    continue

            # Keep only the latest date per scheme+plan combination
            latest_chunks = {}
            for chunk in chunks:
                key = (chunk["metadata"]["scheme_name"], chunk["metadata"]["plan_type"])
                existing = latest_chunks.get(key)
                if existing is None or chunk["metadata"]["date"] > existing["metadata"]["date"]:
                    latest_chunks[key] = chunk

            return list(latest_chunks.values())
        finally:
            os.unlink(tmp_path)

    def main(self):
        """Load all URLs from sources.csv and print summary."""
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "sources.csv"
        )
        csv_path = os.path.normpath(csv_path)

        if not os.path.exists(csv_path):
            logger.error(f"sources.csv not found at {csv_path}")
            return

        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            urls = [row["url"] for row in reader]

        success = 0
        failure = 0

        for url in urls:
            text, meta = self.load(url)
            if text:
                success += 1
                print(f"[OK] {url} -> {len(text)} chars ({meta.get('doc_type')})")
            else:
                failure += 1
                print(f"[FAIL] {url}")

        print(f"\nSummary: {success} succeeded, {failure} failed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loader = URLLoader()
    loader.main()
