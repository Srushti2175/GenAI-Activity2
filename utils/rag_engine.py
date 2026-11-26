"""
Krishi Sakhi - RAG (Retrieval-Augmented Generation) Engine
Performs semantic vector search using FAISS (Cosine Similarity)
and retrieves relevant agricultural knowledge chunks for Gemini AI prompt injection.
Includes automatic fallback to BM25 keyword search if embedding API is unreachable.
"""

import os
import sys
import json
import re
import math
import numpy as np
import faiss
import google.generativeai as genai

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import Config
KB_DIR = os.path.join(BASE_DIR, "data", "knowledge_base")
FAISS_INDEX_FILE = os.path.join(KB_DIR, "faiss_index.bin")
METADATA_FILE = os.path.join(KB_DIR, "index_metadata.json")
BM25_FILE = os.path.join(KB_DIR, "bm25_index.json")

EMBEDDING_MODEL = "models/gemini-embedding-001"

# Module-level cache for ultra-fast in-memory search
_faiss_index = None
_metadata = None
_chunks = None
_bm25_data = None
_chunk_tokens_list = None
_query_cache = {}


def _tokenize(text: str):
    """Unicode-aware word tokenizer preserving full Devanagari words."""
    return re.findall(r'[\u0900-\u097F\w]+', text.lower())


def _load_resources():
    """Load FAISS index, metadata, and pre-tokenize chunks into memory (runs once)."""
    global _faiss_index, _metadata, _chunks, _bm25_data, _chunk_tokens_list

    if _faiss_index is not None and _chunks is not None:
        return True

    # 1. Load FAISS index
    if os.path.exists(FAISS_INDEX_FILE):
        try:
            _faiss_index = faiss.read_index(FAISS_INDEX_FILE)
        except Exception as e:
            print(f"[RAG Error]: Could not load FAISS index: {e}")
            _faiss_index = None

    # 2. Load Metadata & Chunks
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                _metadata = json.load(f)
                _chunks = _metadata.get("chunks", [])
                _chunk_tokens_list = [_tokenize(c["text"]) for c in _chunks]
        except Exception as e:
            print(f"[RAG Error]: Could not load index metadata: {e}")
            _chunks = None

    # 3. Load BM25 Fallback Index
    if os.path.exists(BM25_FILE):
        try:
            with open(BM25_FILE, "r", encoding="utf-8") as f:
                _bm25_data = json.load(f)
        except Exception as e:
            print(f"[RAG Error]: Could not load BM25 index: {e}")
            _bm25_data = None

    return (_faiss_index is not None and _chunks is not None)


def search_bm25(query: str, top_k: int = 3):
    """Ultra-fast local BM25 keyword search (< 2ms using pre-tokenized chunks)."""
    _load_resources()
    if not _chunks or not _chunk_tokens_list:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    N = len(_chunks)
    scores = np.zeros(N)
    avgdl = _bm25_data.get("avgdl", 100.0) if _bm25_data else 100.0
    k1 = 1.5
    b = 0.75

    for token in set(query_tokens):
        # Compute DF across pre-tokenized chunks
        df = sum(1 for c_tokens in _chunk_tokens_list if token in c_tokens)
        if df == 0:
            continue
        idf = math.log(1 + (N - df + 0.5) / (df + 0.5))

        for idx, c_tokens in enumerate(_chunk_tokens_list):
            tf = c_tokens.count(token)
            if tf > 0:
                doc_len = len(c_tokens)
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / avgdl))
                scores[idx] += idf * (numerator / denominator)

    top_indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            c = dict(_chunks[idx])
            c["score"] = float(round(scores[idx], 3))
            c["match_type"] = "bm25_keyword"
            results.append(c)

    return results


def search_knowledge_base(query: str, top_k: int = 3, min_score: float = 0.30):
    """
    Search agricultural knowledge base using cached FAISS semantic dense retrieval
    with instant BM25 fallback and 2.5s network timeout protection.
    """
    cache_key = (query.strip().lower(), top_k)
    if cache_key in _query_cache:
        return _query_cache[cache_key]

    _load_resources()

    if _faiss_index is None or not _chunks:
        res = search_bm25(query, top_k=top_k)
        _query_cache[cache_key] = res
        return res

    api_key = Config.GEMINI_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        res = search_bm25(query, top_k=top_k)
        _query_cache[cache_key] = res
        return res

    try:
        genai.configure(api_key=api_key)
        resp = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
            task_type="retrieval_query",
            request_options={"timeout": 2.5}
        )
        query_embedding = np.array([resp["embedding"]], dtype=np.float32)

        # Normalize query vector for cosine similarity
        faiss.normalize_L2(query_embedding)

        # FAISS search: Inner Product on normalized vectors = Cosine Similarity
        scores, indices = _faiss_index.search(query_embedding, top_k)

        results = []
        for rank in range(top_k):
            idx = indices[0][rank]
            score = float(scores[0][rank])
            if idx >= 0 and idx < len(_chunks) and score >= min_score:
                chunk_match = dict(_chunks[idx])
                chunk_match["score"] = round(score, 3)
                chunk_match["match_type"] = "faiss_semantic"
                results.append(chunk_match)

        # If semantic search returned low scores or empty, supplement with BM25
        if not results:
            results = search_bm25(query, top_k=top_k)

        # Cache result (limit cache size to 200 entries)
        if len(_query_cache) > 200:
            _query_cache.clear()
        _query_cache[cache_key] = results
        return results

    except Exception as e:
        print(f"[RAG Retrieval Fallback]: {e}")
        res = search_bm25(query, top_k=top_k)
        return res


def format_rag_context(chunks: list) -> str:
    """Format retrieved knowledge chunks into clean context for Gemini system prompt."""
    if not chunks:
        return ""

    lines = [
        "--- VERIFIED AGRICULTURAL KNOWLEDGE BASE (RAG CONTEXT) ---",
        "The following verified knowledge snippets were retrieved from official agriculture training manuals and guides.",
        "You MUST prioritize these verified facts in your response and cite the document/page number when applicable.\n"
    ]

    for i, c in enumerate(chunks, 1):
        source = c.get("source_file", "Agricultural Manual")
        page = c.get("page", 1)
        category = c.get("category", "agriculture")
        score = c.get("score", 0.0)
        lines.append(f"[[SOURCE {i}]]: File: {source} | Page: {page} | Category: {category} (Relevance: {score})")
        lines.append(f"Content:\n{c.get('text', '').strip()}\n")

    lines.append("--- END OF KNOWLEDGE BASE CONTEXT ---")
    return "\n".join(lines)


def get_rag_status():
    """Return status of RAG index for API status / monitoring."""
    _load_resources()
    is_ready = _faiss_index is not None and _chunks is not None
    total_vectors = _faiss_index.ntotal if _faiss_index else 0
    dim = _faiss_index.d if _faiss_index else 0

    return {
        "status": "active" if is_ready else "not_initialized",
        "vector_search_engine": "FAISS Flat Inner Product (Exact Cosine)",
        "embedding_model": EMBEDDING_MODEL,
        "total_vectors": total_vectors,
        "dimension": dim,
        "total_chunks": len(_chunks) if _chunks else 0,
        "bm25_fallback_ready": _bm25_data is not None
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Testing RAG Engine...")
    status = get_rag_status()
    print("Status:", json.dumps(status, indent=2))

    test_queries = [
        "सेंद्रिय शेतीमध्ये जीवामृत कसे तयार करावे?",
        "सोयाबीनवरील पाने खाणाऱ्या अळीचे नियंत्रण कसे करावे?",
        "कपाशी पिकासाठी खतांची शिफारस काय आहे?",
        "PM-Kisan योजनेचा लाभ कसा मिळतो?"
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        res = search_knowledge_base(q, top_k=2)
        for r in res:
            print(f"  -> Score: {r['score']} | {r['source_file']} (p.{r['page']}) | Match: {r['match_type']}")
            print(f"     Preview: {r['text'][:120]}...")
