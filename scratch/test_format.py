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

t0 = time.time()
res = c.post('/api/chat', json={
    'message': 'सोयाबीनवर पाने खाणाऱ्या अळीचे नियंत्रण कसे करावे?',
    'language': 'mr'
})
t1 = time.time()

d = res.get_json()
print(f"Time: {t1 - t0:.2f}s | Status: {d.get('status')} | Source: {d.get('source')}")
print("\n--- FORMATTED RESPONSE ---")
print(d.get('response'))
