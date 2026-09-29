"""Streamlit UI for the MF FAQ Assistant RAG Bot."""

import os
import sys

import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.config.settings import CONFIG
from src.retrieval.pipeline import RetrievalPipeline


@st.cache_resource
def get_pipeline() -> RetrievalPipeline:
    """Initialize and cache the RetrievalPipeline."""
    return RetrievalPipeline(CONFIG)


def main():
    """Main Streamlit app."""
    # Page configuration
    st.set_page_config(
        page_title=CONFIG.get("app_title", "MF FAQ Assistant"),
        page_icon=":chart_with_upwards_trend:",
        layout="centered",
    )

    # Initialize pipeline
    pipeline = get_pipeline()

    # Header
    st.title(CONFIG.get("app_title", "MF FAQ Assistant"))

    # Welcome message
    st.markdown(f"### {CONFIG.get('welcome_message', 'Ask me factual questions.')}")

    # Disclaimer banner
    st.warning("**Facts-only. No investment advice.**")

    # Example questions
    st.markdown("### Try these example questions:")
    example_questions = CONFIG.get("example_questions", [])

    cols = st.columns(3)
    for i, question in enumerate(example_questions):
        with cols[i % 3]:
            if st.button(question, key=f"example_{i}"):
                st.session_state["selected_question"] = question

    # Chat input
    question = st.text_input(
        "Ask a question about HDFC mutual fund schemes:",
        value=st.session_state.get("selected_question", ""),
        key="question_input",
    )

    # Clear selected question from session state
    if "selected_question" in st.session_state:
        del st.session_state["selected_question"]

    # Process question
    if question:
        # Show user message
        st.markdown(f"**You:** {question}")

        # Show loading spinner
        with st.spinner("Searching for answer..."):
            result = pipeline.query(question)

        # Display response
        st.markdown("---")

        if result["is_refusal"]:
            # Refusal response
            st.error(result["answer"])
            if result["source_url"]:
                st.markdown(
                    f"[Educational Resource]({result['source_url']})"
                )
        else:
            # Normal answer
            st.markdown(f"**Answer:** {result['answer']}")

            if result["source_url"]:
                st.markdown("---")
                st.markdown("**Source:**")
                st.markdown(f"[View Source]({result['source_url']})")
                st.markdown(
                    f"*Last updated from sources: {result['source_url']}*"
                )

    # Sidebar
    with st.sidebar:
        st.markdown("### About")
        st.markdown(
            "This assistant provides **factual information** about HDFC mutual fund "
            "schemes using only official public sources (AMC, SEBI, AMFI)."
        )

        st.markdown("---")
        st.markdown("### Sources")
        st.markdown(f"- {16} official pages ingested")
        st.markdown("- HDFC Mutual Fund")
        st.markdown("- SEBI")
        st.markdown("- AMFI")

        st.markdown("---")
        st.markdown("### Known Limitations")
        st.markdown("- Facts-only, no investment advice")
        st.markdown("- Limited to HDFC schemes")
        st.markdown("- No performance/return data")
        st.markdown("- English only")

    # Footer
    st.markdown("---")
    disclaimer_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "disclaimer.md"
    )
    if os.path.exists(disclaimer_path):
        with open(disclaimer_path, "r") as f:
            disclaimer_text = f.read()
        st.markdown(f"*{disclaimer_text}*")
    else:
        st.markdown(
            "*Facts-only. No investment advice. This assistant provides factual "
            "information from official public sources only.*"
        )


if __name__ == "__main__":
    main()
