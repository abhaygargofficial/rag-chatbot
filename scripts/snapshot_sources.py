"""Fetch all source URLs and save raw content to data/raw/."""

import hashlib
import json
import logging
import os
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
SOURCES_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "sources.csv")


def fetch_url(url: str, session: requests.Session) -> tuple:
    """Fetch URL and return (content_bytes, content_type)."""
    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        return response.content, response.headers.get("Content-Type", "")
    except Exception as e:
        logger.error(f"  [FAIL] {url}: {e}")
        return None, ""


def get_extension(url: str, content_type: str) -> str:
    """Determine file extension from URL and content type."""
    url_lower = url.lower()
    if url_lower.endswith(".pdf") or "pdf" in content_type:
        return ".pdf"
    elif url_lower.endswith((".xls", ".xlsx", ".xlsm")) or "excel" in content_type or "spreadsheet" in content_type:
        return ".xls"
    elif url_lower.endswith(".csv") or "csv" in content_type:
        return ".csv"
    else:
        return ".html"


def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    # Read sources.csv
    import csv
    with open(SOURCES_CSV, "r") as f:
        reader = csv.DictReader(f)
        sources = list(reader)

    manifest = []
    fetch_date = datetime.now().isoformat()

    for i, source in enumerate(sources):
        url = source["url"]
        logger.info(f"[{i+1}/{len(sources)}] Fetching: {url}")

        content, content_type = fetch_url(url, session)
        if content is None:
            continue

        # Generate filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        ext = get_extension(url, content_type)
        filename = f"{url_hash}{ext}"
        filepath = os.path.join(RAW_DIR, filename)

        # Save raw content
        with open(filepath, "wb") as f:
            f.write(content)

        logger.info(f"  -> Saved {len(content)} bytes to {filename}")

        manifest.append({
            "filename": filename,
            "source_url": url,
            "doc_type": source.get("type", "unknown"),
            "scheme_name": source.get("scheme_name", ""),
            "fetch_date": fetch_date,
            "content_type": content_type,
            "size_bytes": len(content),
        })

    # Save manifest
    manifest_path = os.path.join(RAW_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"\nSnapshot complete: {len(manifest)} files saved to {RAW_DIR}")
    logger.info(f"Manifest saved to {manifest_path}")


if __name__ == "__main__":
    main()
