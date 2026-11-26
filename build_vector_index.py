"""
Krishi Sakhi - Vector Index Builder
Generates dense embeddings for all knowledge base chunks using Gemini Embeddings
and builds a FAISS vector index (data/knowledge_base/faiss_index.bin).
Also builds a fast local BM25/keyword index as fallback.
"""

import os
import sys
import json
import time
import math
import numpy as np
import faiss
import google.generativeai as genai
from dotenv import load_dotenv

# Ensure project root in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

KB_DIR = os.path.join(BASE_DIR, "data", "knowledge_base")
CHUNKS_FILE = os.path.join(KB_DIR, "processed_chunks.json")
FAISS_INDEX_FILE = os.path.join(KB_DIR, "faiss_index.bin")
EMBEDDINGS_FILE = os.path.join(KB_DIR, "chunk_embeddings.npy")
METADATA_FILE = os.path.join(KB_DIR, "index_metadata.json")
BM25_FILE = os.path.join(KB_DIR, "bm25_index.json")

EMBEDDING_MODEL = "models/gemini-embedding-001"
BATCH_SIZE = 30


def tokenize(text: str):
    """Simple whitespace + punctuation tokenizer for local fallback search."""
    import re
    return re.findall(r'\b\w+\b', text.lower())


def build_bm25_index(chunks):
    """Build a lightweight BM25 index for zero-latency local keyword fallback."""
    print("\nBuilding lightweight local BM25 fallback index...")
    doc_freqs = {}
    doc_lengths = []
    tokenized_docs = []

    for c in chunks:
        tokens = tokenize(c["text"])
        tokenized_docs.append(tokens)
        doc_lengths.append(len(tokens))
        unique_tokens = set(tokens)
        for t in unique_tokens:
            doc_freqs[t] = doc_freqs.get(t, 0) + 1

    N = len(chunks)
    avgdl = sum(doc_lengths) / N if N > 0 else 1.0

    bm25_data = {
        "N": N,
        "avgdl": avgdl,
        "doc_lengths": doc_lengths,
        "doc_freqs": doc_freqs,
        "chunk_ids": [c["id"] for c in chunks]
    }

    with open(BM25_FILE, "w", encoding="utf-8") as f:
        json.dump(bm25_data, f, ensure_ascii=False)
    print(f"[OK] Saved BM25 index ({len(doc_freqs)} terms) to: {BM25_FILE}")


def build_faiss_index():
    print("=" * 60)
    print("[KRISHI SAKHI] - STEP 5: BUILDING FAISS VECTOR INDEX")
    print("=" * 60)

    if not os.path.exists(CHUNKS_FILE):
        print(f"Error: {CHUNKS_FILE} not found. Run ingest_knowledge.py first.")
        return False

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Total Chunks to Index: {len(chunks)}")
    if not chunks:
        print("No chunks to index.")
        return False

    # 1. Build local BM25 index
    build_bm25_index(chunks)

    # 2. Configure Gemini API for embeddings
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("[WARNING] GEMINI_API_KEY not set. Cannot generate dense neural embeddings.")
        print("Using BM25 index as primary.")
        return False

    genai.configure(api_key=api_key)
    print(f"\nGenerating embeddings using: {EMBEDDING_MODEL}")
    print(f"Batch size: {BATCH_SIZE} chunks per API call")

    all_embeddings = []
    total_chunks = len(chunks)

    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = math.ceil(total_chunks / BATCH_SIZE)

        success = False
        retries = 3
        while not success and retries > 0:
            print(f"  -> Embedding batch {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ", flush=True)
            try:
                resp = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=texts,
                    task_type="retrieval_document"
                )
                embeddings = resp["embedding"]
                all_embeddings.extend(embeddings)
                print("[OK]")
                success = True
            except Exception as e:
                print(f"[Rate Limit / Error: {e}]")
                retries -= 1
                if retries > 0:
                    print("     Pausing 22 seconds for Free Tier rate limit reset...")
                    time.sleep(22)
                else:
                    print("     Falling back to zero vectors for this batch.")
                    dim = 3072
                    all_embeddings.extend([[0.0] * dim for _ in batch])
        # Smooth pause between batches to stay under 100 items/min
        time.sleep(12)

    if len(all_embeddings) != len(chunks):
        print(f"Warning: Embeddings count ({len(all_embeddings)}) != Chunks count ({len(chunks)})")

    # 3. Convert to float32 numpy array and normalize for Cosine Similarity
    embeddings_np = np.array(all_embeddings, dtype=np.float32)
    dim = embeddings_np.shape[1]
    print(f"\nTotal Embeddings Matrix: {embeddings_np.shape} (Dimension: {dim})")

    # Normalize vectors so that Inner Product == Cosine Similarity
    faiss.normalize_L2(embeddings_np)

    # 4. Create FAISS Index (IndexFlatIP for exact cosine similarity)
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings_np)
    print(f"FAISS Index Created: {index.ntotal} vectors indexed.")

    # 5. Save artifacts
    faiss.write_index(index, FAISS_INDEX_FILE)
    print(f"[OK] Saved FAISS index to: {FAISS_INDEX_FILE}")

    np.save(EMBEDDINGS_FILE, embeddings_np)
    print(f"[OK] Saved embeddings matrix to: {EMBEDDINGS_FILE}")

    # Save index metadata (mapping index row -> chunk details)
    metadata = {
        "embedding_model": EMBEDDING_MODEL,
        "dimension": dim,
        "total_vectors": index.ntotal,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "chunks": chunks
    }
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved index metadata to: {METADATA_FILE}")

    print("\n" + "=" * 60)
    print("STEP 5 VECTOR INDEXING COMPLETE!")
    print(f"• Indexed Chunks : {index.ntotal}")
    print(f"• Vector Dim     : {dim}")
    print(f"• Search Engine  : FAISS Flat Inner Product (Exact Cosine)")
    print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    build_faiss_index()
