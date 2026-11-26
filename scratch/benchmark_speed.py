import time
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.rag_engine import search_bm25, search_knowledge_base

q = "सेंद्रिय शेतीमध्ये जीवामृत कसे तयार करावे?"

# Warmup
search_bm25(q, top_k=2)

t0 = time.time()
r_bm25 = search_bm25(q, top_k=3)
t1 = time.time()
print(f"BM25 Retrieval Time: {(t1 - t0) * 1000:.2f} ms")
for r in r_bm25:
    print(f"  BM25 match: {r['source_file']} p.{r['page']} (score: {r['score']})")

t2 = time.time()
r_faiss = search_knowledge_base(q, top_k=3)
t3 = time.time()
print(f"\nFAISS + Remote Embedding API Time: {(t3 - t2) * 1000:.2f} ms")
for r in r_faiss:
    print(f"  FAISS match: {r['source_file']} p.{r['page']} (score: {r['score']})")
