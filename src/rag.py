"""
Task 6: RAG Pipeline
====================
Loads company documents, chunks them, builds a FAISS vector store
using HuggingFace sentence-transformers embeddings, and provides
a retrieval function used by department agents.

Embedding model : sentence-transformers/all-MiniLM-L6-v2 (free, offline after first download)
Vector store    : FAISS (in-memory, no server needed)
"""

import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# ── Path to knowledge base documents ──────────────────────────────────────────
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")

DOCUMENTS = {
    "company_policy":   "company_policy.txt",
    "pricing_guide":    "pricing_guide.txt",
    "technical_manual": "technical_manual.txt",
    "faq":              "faq.txt",
}

# Sources that get fine-grained Q&A-boundary chunking instead of
# generic character-based splitting (prevents unrelated FAQ entries
# from bleeding into the same chunk).
QA_STYLE_SOURCES = {"faq"}

# Default similarity score cutoff for retrieve_context().
# FAISS similarity_search_with_score returns L2 distance here (since
# embeddings are normalize_embeddings=True). Lower score = more similar.
# Tune this against your own docs/queries before trusting it blindly —
# print raw scores for a handful of test queries and see where the
# "actually relevant" vs "just nearby" boundary falls.
DEFAULT_SCORE_THRESHOLD = 0.5


def _load_qa_chunks(filepath: str, source: str) -> list[Document]:
    """
    Split a FAQ-style file into one Document per Q&A pair, instead of
    relying on generic character-count chunking. This keeps "How do I
    reset my password?" and "How do I update my profile?" as separate
    retrievable units even though they sit right next to each other
    in the source file.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    raw_blocks = [b.strip() for b in content.split("\n\n") if b.strip()]
    qa_chunks = []
    for block in raw_blocks:
        if block.startswith("Q:"):
            qa_chunks.append(Document(page_content=block, metadata={"source": source}))
        elif qa_chunks:
            # Non-"Q:" block (e.g. a section header) — attach to nothing,
            # but don't silently drop it either; keep as its own small chunk
            # so section headers like "ACCOUNT QUESTIONS" aren't lost.
            qa_chunks.append(Document(page_content=block, metadata={"source": source}))
        else:
            qa_chunks.append(Document(page_content=block, metadata={"source": source}))

    return qa_chunks


def load_documents() -> list[Document]:
    """
    Read all knowledge-base text files and wrap them as LangChain Documents.

    FAQ-style sources are returned as one Document per Q&A pair (already
    chunked). Other sources are returned as a single whole-file Document,
    to be chunked later by the character splitter in build_vector_store().
    """
    docs = []
    for source, filename in DOCUMENTS.items():
        filepath = os.path.join(DOCS_DIR, filename)

        if source in QA_STYLE_SOURCES:
            qa_docs = _load_qa_chunks(filepath, source)
            docs.extend(qa_docs)
            print(f"[RAG] Loaded '{source}' as {len(qa_docs)} Q&A chunks.")
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            docs.append(Document(page_content=content, metadata={"source": source}))
            print(f"[RAG] Loaded '{source}' as 1 whole-file document.")

    print(f"[RAG] Loaded {len(docs)} total knowledge-base documents/chunks.")
    return docs


def build_vector_store(docs: list[Document]) -> FAISS:
    """
    Chunk documents and build a FAISS vector store using
    HuggingFace sentence-transformers embeddings.

    Documents already pre-chunked (FAQ Q&A pairs) are passed through
    untouched. Larger whole-file documents (policy, pricing, manual)
    are split further by the character-based splitter.

    Model: all-MiniLM-L6-v2 (~80 MB, downloaded once and cached locally).
    No API key required.
    """
    # 1. Separate already-chunked docs (FAQ) from whole-file docs
    pre_chunked = [d for d in docs if d.metadata.get("source") in QA_STYLE_SOURCES]
    to_split = [d for d in docs if d.metadata.get("source") not in QA_STYLE_SOURCES]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "],
    )
    split_chunks = splitter.split_documents(to_split) if to_split else []

    chunks = pre_chunked + split_chunks
    print(
        f"[RAG] {len(pre_chunked)} pre-chunked (FAQ) docs + "
        f"{len(split_chunks)} character-split chunks = {len(chunks)} total chunks."
    )

    # 2. Load HuggingFace embedding model (cached after first run)
    print("[RAG] Loading HuggingFace embedding model (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # 3. Build FAISS index
    vector_store = FAISS.from_documents(chunks, embeddings)
    print("[RAG] FAISS vector store built successfully.")
    return vector_store


def retrieve_context(
    vector_store: FAISS,
    query: str,
    k: int = 4,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
) -> str:
    """
    Retrieve the top-k most relevant document chunks for a given query
    using semantic similarity (FAISS L2 distance over normalized
    MiniLM embeddings), then filter out chunks that aren't actually
    close enough to be relevant.

    Args:
        vector_store    : The FAISS index.
        query           : The customer's question.
        k               : Max number of chunks to consider.
        score_threshold : Max distance to keep a chunk (lower = more similar).
                          Chunks scoring above this are dropped. If every
                          candidate is dropped, the single best match is
                          kept anyway so callers never get an empty result
                          when *something* was retrieved.

    Returns:
        A single string with all relevant retrieved chunks joined by separators.
    """
    results = vector_store.similarity_search_with_score(query, k=k)
    if not results:
        return "No relevant information found in the knowledge base."

    filtered = [(doc, score) for doc, score in results if score <= score_threshold]
    if not filtered:
        # Nothing cleared the bar — fall back to the single closest match
        # rather than returning nothing at all.
        filtered = [results[0]]

    context_parts = []
    for doc, score in filtered:
        context_parts.append(
            f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        )

    context = "\n\n---\n\n".join(context_parts)
    print(
        f"[RAG] Retrieved {len(filtered)}/{len(results)} chunks "
        f"above threshold ({score_threshold}) for query: {query!r}"
    )
    for doc, score in results:
        kept = "kept" if score <= score_threshold or (doc, score) == filtered[0] else "dropped"
        print(f"       [{kept}] score={score:.4f} source={doc.metadata.get('source')}")

    return context


# ── Singleton vector store (built once, reused across all nodes) ──────────────
_vector_store: FAISS | None = None


def get_vector_store() -> FAISS:
    """Return (or build) the singleton FAISS vector store."""
    global _vector_store
    if _vector_store is None:
        docs = load_documents()
        _vector_store = build_vector_store(docs)
    return _vector_store