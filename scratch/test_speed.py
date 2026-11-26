import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import app

c = app.test_client()
with c.session_transaction() as sess:
    sess['user'] = {
        'name': 'Ramesh Patil',
        'location': 'Sangli, Maharashtra',
        'crops': 'Soybean, Cotton',
        'language': 'mr'
    }

q1 = 'सेंद्रिय शेतीमध्ये जीवामृत कसे तयार करावे?'
t0 = time.time()
res1 = c.post('/api/chat', json={'message': q1, 'language': 'mr'})
t1 = time.time()
d1 = res1.get_json()
print(f"Query 1 (Cold): {(t1 - t0):.2f}s | Source: {d1.get('source')} | Docs: {len(d1.get('source_documents', []))}")
print("Response 1:", d1.get('response', '')[:160].replace('\n', ' '))

q2 = 'सोयाबीनवरील अळीसाठी कोणते औषध वापरावे?'
t2 = time.time()
res2 = c.post('/api/chat', json={'message': q2, 'language': 'mr'})
t3 = time.time()
d2 = res2.get_json()
print(f"\nQuery 2 (Warm): {(t3 - t2):.2f}s | Source: {d2.get('source')} | Docs: {len(d2.get('source_documents', []))}")
print("Response 2:", d2.get('response', '')[:160].replace('\n', ' '))

t4 = time.time()
res3 = c.post('/api/chat', json={'message': q1, 'language': 'mr'})
t5 = time.time()
d3 = res3.get_json()
print(f"\nQuery 3 (Cached RAG): {(t5 - t4):.2f}s | Source: {d3.get('source')} | Docs: {len(d3.get('source_documents', []))}")
