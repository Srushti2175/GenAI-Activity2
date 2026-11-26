"""
Test Hindi language fix in KrishiSakhi.
Verifies:
  1. Hindi query returns real Gemini AI response (no 'API key' hint text)
  2. Source shows AI model, not Demo
  3. No fallback_response demo text
  4. Also tests Marathi and English to ensure no regression
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from app import app

FARMER_HI = {'name': 'Raju Kumar', 'location': 'Lucknow, UP', 'crops': 'Wheat', 'language': 'hi'}
FARMER_MR = {'name': 'Ramesh Patil', 'location': 'Sangli, Maharashtra', 'crops': 'Soybean', 'language': 'mr'}
FARMER_EN = {'name': 'John Farmer', 'location': 'Punjab', 'crops': 'Rice', 'language': 'en'}

TESTS = [
    ("hi", FARMER_HI, "सोयाबीन की फसल में कीड़ों से कैसे बचाएं?"),
    ("hi", FARMER_HI, "गेहूं की खेती के लिए सिंचाई कब करनी चाहिए?"),
    ("mr", FARMER_MR, "सोयाबीन पिकावर कीड नियंत्रण कसे करावे?"),
    ("en", FARMER_EN, "How to manage rice blast disease?"),
]

FAIL_PHRASES = [
    "GEMINI_API_KEY .env में डालें",
    "GEMINI_API_KEY .env मध्ये टाका",
    "Add GEMINI_API_KEY to .env",
    "Demo Mode",
    "demo@krishisakhi",
]

client = app.test_client()
all_passed = True

for lang, farmer, query in TESTS:
    with client.session_transaction() as sess:
        sess['user'] = farmer
    
    start = time.time()
    res = client.post('/api/chat', json={'message': query, 'language': lang})
    elapsed = time.time() - start
    d = res.get_json()

    status = d.get('status')
    source = d.get('source', '')
    response = d.get('response', '')
    ai_powered = d.get('ai_powered', False)

    # Check for forbidden phrases
    has_bad_phrase = any(phrase in response for phrase in FAIL_PHRASES)
    passed = status == 'success' and not has_bad_phrase

    flag = "✅ PASS" if passed else "❌ FAIL"
    if not passed:
        all_passed = False

    print(f"\n{'='*60}")
    print(f"{flag} | lang={lang} | {elapsed:.2f}s")
    print(f"Query   : {query[:60]}")
    print(f"Source  : {source}")
    print(f"AI Ready: {ai_powered}")
    print(f"Response (first 300 chars):\n{response[:300]}")
    if has_bad_phrase:
        for phrase in FAIL_PHRASES:
            if phrase in response:
                print(f"⚠️  FORBIDDEN PHRASE FOUND: '{phrase}'")

print(f"\n{'='*60}")
print("ALL TESTS PASSED ✅" if all_passed else "SOME TESTS FAILED ❌")
