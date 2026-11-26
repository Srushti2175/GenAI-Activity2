import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

client = app.test_client()

print("=" * 60)
print("KRISHI SAKHI - END-TO-END RAG VALIDATION")
print("=" * 60)

# 1. Check knowledge endpoint
print("\n[TEST 1] Testing /api/knowledge...")
r1 = client.get('/api/knowledge')
data1 = r1.get_json()
print("  Status code:", r1.status_code)
print("  Total documents:", data1.get("total_documents"))
print("  Total chunks:", data1.get("total_chunks"))
print("  RAG status:", data1.get("rag_engine", {}).get("status"))
print("  FAISS vectors:", data1.get("rag_engine", {}).get("total_vectors"))

# 2. Check search endpoint
print("\n[TEST 2] Testing /api/search?q=जीवामृत&k=2...")
r2 = client.get('/api/search?q=जीवामृत&k=2')
data2 = r2.get_json()
print("  Status code:", r2.status_code)
print(f"  Found {data2.get('count')} results:")
for doc in data2.get("results", []):
    print(f"    - {doc['file_name']} (p.{doc['page']}) | score: {doc['score']} | {doc['match_type']}")

# 3. Check /api/chat with RAG context
print("\n[TEST 3] Testing /api/chat with RAG query...")
with client.session_transaction() as sess:
    sess['user'] = {
        'name': 'Ramesh Patil (रमेश पाटील)',
        'location': 'Sangli, Maharashtra',
        'crops': 'Soybean, Cotton',
        'language': 'mr'
    }

r3 = client.post('/api/chat', json={
    'message': 'सेंद्रिय शेतीमध्ये जीवामृत कसे तयार करावे आणि काय प्रमाण वापरावे?',
    'language': 'mr'
})
data3 = r3.get_json()
print("  Status code:", r3.status_code)
print("  Chat status:", data3.get("status"))
print("  Source engine:", data3.get("source"))
print("  RAG active:", data3.get("rag_active"))
print("  Sources count:", len(data3.get("source_documents", [])))
for doc in data3.get("source_documents", []):
    print(f"    * {doc['file_name']} (Page {doc['page']}) [Score: {doc['score']}]")

print("\n--- AI Response Generated with RAG ---")
print(data3.get("response", ""))
print("\n" + "=" * 60)
