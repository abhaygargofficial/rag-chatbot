"""Streamlit UI for Indmoney - INDmoney-style blue/white theme."""

import html
import os
import sys
from urllib.parse import urlparse

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.config.settings import CONFIG
from src.retrieval.pipeline import RetrievalPipeline


LOGO_URL = "https://ast.indmoneycdn.com/cdn/images/fe/ind-money-logo.svg"

FALLBACK_QUESTIONS = [
    "What is the expense ratio of HDFC Flexi Cap Fund?",
    "What is the exit load on HDFC Mid-Cap Opportunities Fund?",
    "What is the lock-in period for HDFC ELSS Tax Saver?",
    "Who manages HDFC Balanced Advantage Fund?",
]

st.set_page_config(
    page_title="Indmoney | HDFC MF Assistant",
    page_icon=":chart_with_upwards_trend:",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    :root {
        --blue: #1E5EFF;
        --blue-deep: #0829A6;
        --blue-night: #061A6B;
        --blue-tint: #EEF3FF;
        --blue-line: #D5E0FF;
        --ink: #0B1B3F;
        --text: #3A4A6B;
        --muted: #7A88A8;
        --line: #E7ECF6;
        --white: #FFFFFF;
        --soft: #F6F8FE;
    }

    /* ---------- Force light, kill Streamlit chrome ---------- */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: var(--white) !important;
        color: var(--ink) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    .stApp p, .stApp span, .stApp div, .stApp button, .stApp textarea { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
    #MainMenu, footer, .stDeployButton { display: none !important; }

    [data-testid="stMainBlockContainer"], .block-container {
        max-width: 880px !important;
        padding: 0 24px 140px !important;
    }

    /* ---------- Top bar ---------- */
    .st-key-topbar {
        position: sticky; top: 0; z-index: 50;
        background: rgba(255,255,255,0.88);
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        border-bottom: 1px solid var(--line);
        padding: 14px 0 12px; margin: 0 -24px 0; padding-left: 24px; padding-right: 24px;
    }
    .brand { display: flex; align-items: center; gap: 12px; height: 40px; }
    .brand img { height: 26px; width: auto; display: block; }
    .brand-divider { width: 1px; height: 20px; background: var(--line); }
    .brand-sub { font-size: 13px; font-weight: 600; color: var(--muted); }

    .st-key-kb_button { display: flex; justify-content: flex-end; }
    .st-key-kb_button button {
        background: var(--white) !important; color: var(--blue) !important;
        border: 1px solid var(--blue-line) !important; border-radius: 999px !important;
        font-weight: 600 !important; font-size: 13px !important; padding: 6px 16px !important;
        min-height: 36px !important;
    }
    .st-key-kb_button button p { color: var(--blue) !important; font-size: 13px !important; font-weight: 600 !important; }
    .st-key-kb_button button:hover { background: var(--blue-tint) !important; border-color: var(--blue) !important; }

    /* ---------- Hero ---------- */
    .hero {
        position: relative; overflow: hidden;
        background: radial-gradient(120% 140% at 100% 0%, #3D7BFF 0%, var(--blue) 35%, var(--blue-deep) 75%, var(--blue-night) 100%);
        border-radius: 24px; padding: 44px 40px 36px; margin: 28px 0 32px; color: var(--white);
        box-shadow: 0 20px 50px -24px rgba(8,41,166,0.55);
    }
    .hero::after {
        content: ""; position: absolute; inset: 0; pointer-events: none;
        background-image:
            linear-gradient(rgba(255,255,255,0.07) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.07) 1px, transparent 1px);
        background-size: 32px 32px;
        mask-image: linear-gradient(120deg, transparent 30%, #000 100%);
        -webkit-mask-image: linear-gradient(120deg, transparent 30%, #000 100%);
    }
    .hero-chart { position: absolute; right: -10px; bottom: -6px; width: 300px; opacity: 0.9; pointer-events: none; }
    .hero-inner { position: relative; z-index: 1; max-width: 520px; }
    .hero h1 {
        font-size: clamp(28px, 4.4vw, 40px) !important; font-weight: 800 !important;
        line-height: 1.12 !important; letter-spacing: -0.8px; margin: 0 0 14px !important;
        color: var(--white) !important; padding: 0 !important;
    }
    .hero p.lead { font-size: 15px; line-height: 1.6; margin: 0 0 24px; color: #CFDBFF !important; }
    .hero-sources { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
    .hero-sources span.label { font-size: 12px; color: #AFC3FF !important; margin-right: 4px; }
    .chip {
        font-size: 12px; font-weight: 600; color: var(--white) !important;
        background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.22);
        border-radius: 999px; padding: 5px 11px;
    }
    .hero-foot {
        margin-top: 22px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.16);
        font-size: 12.5px; color: #CFDBFF !important; display: flex; align-items: center; gap: 8px;
    }
    .hero-foot svg { flex-shrink: 0; }

    /* ---------- Example questions ---------- */
    .section-head { display: flex; align-items: baseline; justify-content: space-between; margin: 0 0 14px; }
    .section-title { font-size: 17px; font-weight: 700; color: var(--ink); }
    .section-hint { font-size: 13px; color: var(--muted); }

    .st-key-examples [data-testid="stHorizontalBlock"] { gap: 12px; }
    .st-key-examples [data-testid="stButton"] { margin-bottom: 4px; }
    .st-key-examples button {
        width: 100% !important; min-height: 88px !important; height: auto !important;
        background: var(--white) !important; border: 1px solid var(--line) !important;
        border-radius: 16px !important; padding: 16px 18px 16px 58px !important;
        text-align: left !important; position: relative;
        box-shadow: 0 1px 2px rgba(11,27,63,0.04);
        transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease;
    }
    .st-key-examples button::before {
        content: ""; position: absolute; left: 18px; top: 50%; transform: translateY(-50%);
        width: 28px; height: 28px; border-radius: 9px; background-color: var(--blue-tint);
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231E5EFF' stroke-width='2.4' stroke-linecap='round'%3E%3Cpath d='M6 18v-4'/%3E%3Cpath d='M12 18V9'/%3E%3Cpath d='M18 18V5'/%3E%3C/svg%3E");
        background-repeat: no-repeat; background-position: center; background-size: 15px;
    }
    .st-key-examples button > div { justify-content: flex-start !important; width: 100%; }
    .st-key-examples button p {
        text-align: left !important; font-size: 14px !important; font-weight: 500 !important;
        color: var(--text) !important; line-height: 1.45 !important; margin: 0 !important;
    }
    .st-key-examples button:hover {
        border-color: var(--blue) !important;
        box-shadow: 0 8px 24px -12px rgba(30,94,255,0.45) !important;
        transform: translateY(-1px);
    }
    .st-key-examples button:hover p { color: var(--ink) !important; }
    .st-key-examples button:focus-visible { outline: 2px solid var(--blue) !important; outline-offset: 2px; }

    /* ---------- Chat ---------- */
    .chat-top { height: 20px; }
    .user-row { display: flex; justify-content: flex-end; margin: 22px 0 12px; }
    .user-bubble {
        background: var(--blue); color: var(--white) !important;
        padding: 12px 18px; border-radius: 18px 18px 4px 18px; max-width: 75%;
        font-size: 14.5px; line-height: 1.5; overflow-wrap: anywhere;
        box-shadow: 0 6px 18px -10px rgba(30,94,255,0.7);
    }
    .bot-row { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 8px; }
    .bot-avatar {
        width: 34px; height: 34px; border-radius: 11px; flex-shrink: 0;
        background: linear-gradient(135deg, var(--blue) 0%, var(--blue-deep) 100%);
        display: flex; align-items: center; justify-content: center;
    }
    .bot-card {
        flex: 1; min-width: 0; background: var(--white); border: 1px solid var(--line);
        border-radius: 4px 18px 18px 18px; padding: 16px 20px;
        box-shadow: 0 1px 2px rgba(11,27,63,0.04);
    }
    .bot-name { font-size: 12.5px; font-weight: 700; color: var(--blue) !important; margin-bottom: 6px; }
    .bot-answer { font-size: 14.5px; line-height: 1.7; color: var(--text) !important; overflow-wrap: anywhere; }
    .source {
        display: flex; align-items: center; justify-content: space-between; gap: 12px;
        margin-top: 14px; padding: 10px 12px; background: var(--soft);
        border: 1px solid var(--line); border-radius: 12px;
    }
    .source-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
    .source-domain { font-size: 12.5px; color: var(--muted) !important; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .source a {
        font-size: 13px; font-weight: 700; color: var(--blue) !important;
        text-decoration: none !important; white-space: nowrap;
    }
    .source a:hover { text-decoration: underline !important; }

    /* Spinner */
    [data-testid="stSpinner"] p, [data-testid="stSpinner"] div { color: var(--muted) !important; font-size: 13px !important; }

    /* ---------- Chat input (bottom bar) ---------- */
    [data-testid="stBottom"], [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] { background: var(--white) !important; }
    [data-testid="stBottomBlockContainer"] { max-width: 880px !important; padding: 12px 24px 22px !important; }
    [data-testid="stBottom"] { border-top: 1px solid var(--line); }
    [data-testid="stChatInput"] {
        background: var(--white) !important; border: 1.5px solid var(--blue-line) !important;
        border-radius: 16px !important; box-shadow: 0 8px 28px -14px rgba(30,94,255,0.35) !important;
    }
    [data-testid="stChatInput"] > div { background: var(--white) !important; }
    [data-testid="stChatInput"]:focus-within { border-color: var(--blue) !important; }
    [data-testid="stChatInput"] textarea {
        background: var(--white) !important; color: var(--ink) !important;
        font-size: 14.5px !important; caret-color: var(--blue);
    }
    [data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; }
    [data-testid="stChatInputSubmitButton"] {
        background: var(--blue) !important; border-radius: 11px !important; color: var(--white) !important;
    }
    [data-testid="stChatInputSubmitButton"]:disabled { background: var(--blue-line) !important; }
    [data-testid="stChatInputSubmitButton"] svg { color: var(--white) !important; fill: var(--white) !important; }

    /* ---------- Knowledge base dialog ---------- */
    div[role="dialog"] { background: var(--white) !important; border-radius: 20px !important; }
    div[role="dialog"] h2, div[role="dialog"] [data-testid="stHeading"] * { color: var(--ink) !important; font-weight: 800 !important; }
    .kb-stat {
        display: flex; align-items: center; gap: 14px; padding: 14px 16px; margin-bottom: 18px;
        background: var(--blue-tint); border-radius: 14px;
    }
    .kb-stat b { font-size: 26px; font-weight: 800; color: var(--blue) !important; line-height: 1; }
    .kb-stat span { font-size: 13.5px; color: var(--text) !important; line-height: 1.4; }
    .kb-block { margin-bottom: 18px; }
    .kb-title { font-size: 14px; font-weight: 700; color: var(--ink) !important; margin-bottom: 8px; }
    .kb-block p, .kb-block li { font-size: 14px; color: var(--text) !important; line-height: 1.6; }
    .kb-block ul { margin: 0; padding-left: 18px; }
    .kb-block li::marker { color: var(--blue); }
    .kb-chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .kb-chip {
        font-size: 13px; font-weight: 600; color: var(--blue-deep) !important;
        background: var(--white); border: 1px solid var(--blue-line); border-radius: 999px; padding: 5px 12px;
    }

    @media (prefers-reduced-motion: reduce) {
        .st-key-examples button { transition: none !important; }
        .st-key-examples button:hover { transform: none; }
    }
    @media (max-width: 640px) {
        [data-testid="stMainBlockContainer"], .block-container { padding: 0 14px 140px !important; }
        .st-key-topbar { margin: 0 -14px; padding-left: 14px; padding-right: 14px; }
        .brand-divider, .brand-sub { display: none; }
        .hero { padding: 30px 22px 26px; border-radius: 20px; }
        .hero-chart { width: 200px; opacity: 0.5; }
        .user-bubble { max-width: 88%; }
        .bot-avatar { display: none; }
        .bot-card { border-radius: 18px; padding: 14px 16px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_pipeline() -> RetrievalPipeline:
    pipeline = RetrievalPipeline(CONFIG)

    # Check if the collection is empty (e.g., on deployed environment)
    # and run ingestion if needed
    try:
        count = pipeline.searcher.collection.count()
        if count == 0:
            st.info("Knowledge base is empty. Running initial ingestion...")
            from src.ingestion.pipeline import IngestionPipeline

            ingestion = IngestionPipeline(CONFIG)
            ingestion.run_from_csv()
            st.success("Ingestion complete!")
    except Exception as e:
        st.error(f"Error checking/initializing knowledge base: {e}")

    return pipeline


def _safe(text) -> str:
    return html.escape(str(text or "")).replace("\n", "<br>")


BARS_SVG = (
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#FFFFFF" '
    'stroke-width="2.4" stroke-linecap="round"><path d="M6 18v-4"/><path d="M12 18V9"/>'
    '<path d="M18 18V5"/></svg>'
)

LINK_SVG = (
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#7A88A8" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/>'
    '<path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/></svg>'
)


def render_user(text: str):
    st.markdown(
        f'<div class="user-row"><div class="user-bubble">{_safe(text)}</div></div>',
        unsafe_allow_html=True,
    )


def render_bot(answer, source_url):
    source_html = ""
    if source_url:
        url = html.escape(str(source_url), quote=True)
        domain = html.escape(urlparse(str(source_url)).netloc.replace("www.", "") or str(source_url))
        source_html = (
            '<div class="source">'
            f'<div class="source-left">{LINK_SVG}<span class="source-domain">{domain}</span></div>'
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">View official page</a>'
            "</div>"
        )
    st.markdown(
        f'<div class="bot-row"><div class="bot-avatar">{BARS_SVG}</div><div class="bot-card"><div class="bot-name">Indmoney AI</div><div class="bot-answer">{_safe(answer)}</div>{source_html}</div></div>',
        unsafe_allow_html=True,
    )


@st.dialog("Knowledge base")
def show_knowledge_base():
    st.markdown(
        """
        <div class="kb-stat">
            <b>16</b>
            <span>official pages ingested and searchable</span>
        </div>
        <div class="kb-block">
            <div class="kb-title">About</div>
            <p>Answers factual questions about HDFC Mutual Fund schemes using only official public sources.</p>
        </div>
        <div class="kb-block">
            <div class="kb-title">Sources</div>
            <div class="kb-chips">
                <span class="kb-chip">HDFC Mutual Fund</span>
                <span class="kb-chip">SEBI</span>
                <span class="kb-chip">AMFI</span>
            </div>
        </div>
        <div class="kb-block">
            <div class="kb-title">Known limitations</div>
            <ul>
                <li>Facts only, no investment advice</li>
                <li>Limited to HDFC schemes</li>
                <li>No performance or return data</li>
                <li>English only</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar():
    with st.container(key="topbar"):
        left, right = st.columns([4, 1.4], vertical_alignment="center")
        with left:
            st.markdown(
                f'<div class="brand"><img src="{LOGO_URL}" alt="INDmoney">'
                '<span class="brand-divider"></span>'
                '<span class="brand-sub">Mutual Fund Assistant</span></div>',
                unsafe_allow_html=True,
            )
        with right:
            if st.button("Knowledge base", key="kb_button"):
                show_knowledge_base()


def render_landing():
    st.markdown(
        """
        <div class="hero">
            <svg class="hero-chart" viewBox="0 0 300 140" fill="none">
                <path d="M0 120 C40 112 60 96 90 100 S140 70 170 76 S220 40 250 34 S285 18 300 12 L300 140 L0 140 Z" fill="rgba(255,255,255,0.08)"/>
                <path d="M0 120 C40 112 60 96 90 100 S140 70 170 76 S220 40 250 34 S285 18 300 12" stroke="rgba(255,255,255,0.55)" stroke-width="2.5" stroke-linecap="round"/>
                <circle cx="250" cy="34" r="5" fill="#FFFFFF"/>
                <circle cx="250" cy="34" r="11" fill="rgba(255,255,255,0.2)"/>
            </svg>
            <div class="hero-inner">
                <h1>Know your HDFC fund before you invest in it.</h1>
                <p class="lead">Ask about expense ratios, exit loads, lock-in periods, benchmarks and fund managers. Every answer links back to the official page it came from.</p>
                <div class="hero-sources">
                    <span class="label">Answers from</span>
                    <span class="chip">HDFC Mutual Fund</span>
                    <span class="chip">SEBI</span>
                    <span class="chip">AMFI</span>
                </div>
                <div class="hero-foot">
                    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#CFDBFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    Facts only. This assistant does not give investment advice.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    questions = CONFIG.get("example_questions") or FALLBACK_QUESTIONS
    st.markdown(
        '<div class="section-head"><span class="section-title">Try asking</span>'
        '<span class="section-hint">Tap a question to start</span></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="examples"):
        cols = st.columns(2)
        for i, q in enumerate(questions):
            with cols[i % 2]:
                if st.button(q, key=f"example_{i}", use_container_width=True):
                    st.session_state["pending_question"] = q
                    st.rerun()


def main():
    pipeline = get_pipeline()

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    render_topbar()

    question = st.chat_input("Ask anything about HDFC mutual funds...")
    pending = st.session_state.pop("pending_question", None)
    new_q = pending or question

    if not st.session_state["messages"] and not new_q:
        render_landing()
        return

    st.markdown('<div class="chat-top"></div>', unsafe_allow_html=True)

    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            render_user(msg["content"])
        else:
            render_bot(msg["content"], msg.get("source_url"))

    if new_q:
        st.session_state["messages"].append({"role": "user", "content": new_q})
        render_user(new_q)

        with st.spinner("Searching official sources..."):
            result = pipeline.query(new_q)

        answer = result.get("answer", "")
        source_url = result.get("source_url")
        st.session_state["messages"].append(
            {"role": "assistant", "content": answer, "source_url": source_url}
        )
        render_bot(answer, source_url)


if __name__ == "__main__":
    main()