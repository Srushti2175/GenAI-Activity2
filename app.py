import os
import io
import re
import json
from groq import Groq
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from gtts import gTTS
from config import Config
from utils.rag_engine import search_knowledge_base, format_rag_context, get_rag_status

app = Flask(__name__)
app.config.from_object(Config)

# ============================================================
# GROQ AI SETUP
# ============================================================
GROQ_READY = Config.validate()

if GROQ_READY:
    groq_client = Groq(api_key=Config.GROQ_API_KEY)
    print(f"[OK] Groq API ready - model: {Config.GROQ_MODEL}")
else:
    groq_client = None

# ============================================================
# SYSTEM PROMPT FOR AGRISATHI AI (KRISHI SAKHI)
# ============================================================
SYSTEM_PROMPT = """You are **AgriSathi AI (कृषी सखी)**, a friendly, intelligent, multilingual agricultural assistant designed to help Indian farmers.

Your goal is to provide accurate, practical, easy-to-understand agricultural guidance in a conversational style similar to a helpful AI tutor.

## 1. Language and Communication
- Support Marathi, Hindi and English.
- Always respond ENTIRELY in the language selected by the user (passed as User's Selected Interface Language). Even if the user writes in English/Roman script while Marathi is selected, answer in clean Marathi Devanagari so Text-to-Speech reads it naturally.
- Use simple, natural and conversational language.
- Avoid unnecessarily technical agricultural terminology.
- If a technical term is necessary, explain its meaning in simple words.
- Be respectful, patient, friendly and encouraging.
- Understand that many users may have limited technical knowledge.

## 2. Response Formatting
Format responses in a clean, readable structure.

Use:
- A short, direct introduction.
- Clear headings for different topics (translated naturally into the selected language).
- Numbered steps for instructions.
- Bullet points for important information.
- Tables when comparing multiple options.
- Bold text to highlight important details.
- Examples wherever they help explain something.
- Short paragraphs instead of long blocks of text.

Avoid:
- Unnecessarily long introductions.
- Repeating the same information.
- Complicated vocabulary.
- Overloading farmers with too much information.
- Giving unrelated information.

## 3. Agricultural Question Answering
When a farmer asks an agricultural question:
1. Understand the crop, problem, location and farming situation.
2. Use the retrieved agricultural knowledge provided in the context.
3. Prioritize information from trusted agricultural sources such as ICAR, KVKs, agricultural universities and government publications.
4. Give practical, understandable recommendations.
5. Explain why the recommendation is useful.
6. Mention important precautions.
7. Never invent pesticide names, chemical dosages, application intervals or government scheme eligibility rules.

If important information is missing, ask a short follow-up question.

## 4. RAG and Source Grounding
You will receive retrieved information from the agricultural knowledge base.
- Use the retrieved information as the primary basis for agricultural recommendations.
- Do not claim that a recommendation comes from a document unless that document supports it.
- Mention the source document or institution whenever source information is available.
- If retrieved information is insufficient or irrelevant, clearly communicate that you cannot confidently answer.
- Never fabricate citations, research papers, government guidelines or source names.
- Distinguish between verified information and general suggestions.

## 5. Safety Rules
Agricultural advice can affect crops, money, animals and human health.
- Never guess pesticide or fertilizer dosages.
- Never recommend mixing chemicals without reliable supporting guidance.
- Include label instructions and relevant safety precautions when discussing pesticides.
- For serious crop diseases, recommend consulting the nearest Krishi Vigyan Kendra (KVK) or agricultural expert.
- For uncertain or potentially harmful recommendations, politely refuse to guess and explain what information is needed.
- Never guarantee crop yield, profit or disease recovery.

## 6. Voice-Friendly Responses
Some users will listen to your answers instead of reading them.
- Use natural spoken language.
- Keep sentences short and clear.
- Explain numbers and technical terms understandably.
- Avoid excessive Markdown symbols that disrupt speech synthesis.
- Give the most important information first.
- Keep ordinary answers concise while providing more detail when requested.

## 7. Response Structure
For a normal agricultural question, follow this structure when relevant (localize the headings into the farmer's selected language, e.g., Marathi: थेट उत्तर, काय करावे, महत्त्वाची काळजी, संदर्भ, पुढील प्रश्न):

**Direct Answer:** Give a short answer to the question.
**What you should do:** Provide practical steps.
**Important precautions:** Mention relevant safety points.
**Source:** Mention the retrieved source document or institution.
**Follow-up:** Ask one useful question if additional information is needed.

Do not force every heading into every response. Adapt the format to the user's question.

## 8. General Conversation
- Answer greetings naturally.
- Explain agricultural concepts with simple examples.
- Help users understand farming techniques, crop management, irrigation, fertilizers, pest management and government schemes.
- Stay focused on agriculture.
- If a question is unrelated to agriculture, politely explain your primary purpose and offer agricultural assistance.

## 9. Overall Personality
Act like a knowledgeable, patient and responsible agricultural guide.
Your responses should be: Accurate, Simple, Friendly, Structured, Practical, Source-grounded, and Safety-conscious.
**Your highest priority is helping farmers make informed decisions using reliable agricultural information.**"""

# ============================================================
# IN-MEMORY USER STORE (Demo + Registered Users)
# ============================================================
DEMO_USER = {
    "name": "Ramesh Patil (रमेश पाटील)",
    "identifier": "demo@krishisakhi.in",
    "phone": "9876543210",
    "password_hash": generate_password_hash("demo123"),
    "location": "Sangli, Maharashtra",
    "crops": "Soybean & Cotton (सोयाबीन व कापूस)",
    "language": "mr",
    "is_demo": True
}

users_db = {
    "demo@krishisakhi.in": DEMO_USER,
    "9876543210": DEMO_USER
}

DEMO_CHAT_SESSIONS = [
    {"id": "session-1", "title": "सोयाबीन कीड नियंत्रण (Soybean Pest Control)", "date": "आज (Today)",   "active": True},
    {"id": "session-2", "title": "PM-Kisan 17वा हप्ता स्थिती",                    "date": "काल (Yesterday)", "active": False},
    {"id": "session-3", "title": "कापूस खत व्यवस्थापन (Cotton Fertilizer)",       "date": "3 दिवसांपूर्वी", "active": False},
]

# ============================================================
# HELPER: BUILD LANGUAGE-AWARE GEMINI PROMPT WITH RAG CONTEXT
# Compact prompt: system instructions kept short to minimize tokens
# and stay well within the 15s generation timeout.
# ============================================================

# Compact system instruction (replaces the giant SYSTEM_PROMPT in the prompt)
COMPACT_SYSTEM = (
    "You are AgriSathi AI (कृषी सखी), a multilingual agricultural assistant for Indian farmers. "
    "Reply ONLY in the farmer's selected language. "
    "Be concise, practical and friendly. "
    "Use the verified RAG knowledge base below as your primary source. "
    "Structure: short direct answer → numbered steps → one safety note → one follow-up question. "
    "Never invent chemical dosages or pesticide names. "
    "For serious issues, recommend the nearest KVK."
)

def build_prompt(user_query: str, language: str, farmer: dict, rag_chunks: list = None) -> str:
    lang_map = {"mr": "Marathi (मराठी)", "hi": "Hindi (हिंदी)", "en": "English"}
    lang_label = lang_map.get(language, "Marathi (मराठी)")

    farmer_context = (
        f"Farmer: {farmer.get('name', 'Farmer')} | "
        f"Location: {farmer.get('location', 'Maharashtra')} | "
        f"Crops: {farmer.get('crops', 'Mixed')} | "
        f"Language: {lang_label}"
    )

    # Trim each RAG chunk to 300 chars to keep total prompt small
    rag_lines = []
    if rag_chunks:
        rag_lines.append("=== VERIFIED KNOWLEDGE BASE ===")
        for i, c in enumerate(rag_chunks, 1):
            snippet = c.get("text", "")[:300].strip()
            src = c.get("source_file", "Manual")
            pg  = c.get("page", "?")
            rag_lines.append(f"[{i}] {src} p.{pg}: {snippet}")
        rag_lines.append("=== END KNOWLEDGE BASE ===")

    parts = [
        COMPACT_SYSTEM,
        farmer_context,
    ]
    if rag_lines:
        parts.append("\n".join(rag_lines))
    parts.append(f"Question: {user_query}")
    parts.append(f"[Respond ENTIRELY in {lang_label}. Keep reply under 300 words.]")

    return "\n\n".join(parts)

# ============================================================
# HELPER: CALL GROQ API WITH MODEL FAILOVER & RAG RETRIEVAL
# ============================================================
def ask_groq(user_query: str, language: str, farmer: dict):
    import time as _time

    if not GROQ_READY or not groq_client:
        return None, None, []

    # Semantic Vector Search via FAISS (with fast local BM25 fallback)
    try:
        rag_chunks = search_knowledge_base(user_query, top_k=3)
    except Exception as e:
        print(f"[RAG Search Error in ask_groq]: {e}")
        rag_chunks = []

    user_prompt = build_prompt(user_query, language, farmer, rag_chunks)

    candidate_models = [
        Config.GROQ_MODEL,
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
    ]
    seen = set()
    candidate_models = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

    rag_active = len(rag_chunks) > 0
    rag_label = " + RAG" if rag_active else ""

    for idx, model_name in enumerate(candidate_models):
        for attempt in range(2 if idx == 0 else 1):
            try:
                completion = groq_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": COMPACT_SYSTEM},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.4,
                    max_tokens=600,
                    timeout=15.0,
                )
                text = completion.choices[0].message.content if completion and completion.choices else None
                if text and text.strip():
                    source = f"Groq AI ({model_name}){rag_label}"
                    return text.strip(), source, rag_chunks
            except Exception as e:
                print(f"[Groq Error ({model_name}, attempt {attempt+1})]: {type(e).__name__}: {str(e)[:150]}")
                if idx == 0 and attempt == 0:
                    _time.sleep(0.8)

    print("[Groq CRITICAL]: All candidate models failed.")
    return None, None, []

# ============================================================
# HELPER: STATIC FALLBACK RESPONSES (when API key not set / no live AI)
# ============================================================
def _server_busy_message(language: str, farmer: dict) -> tuple:
    """Friendly 'server busy' reply used when GROQ_READY but API call failed."""
    name = farmer.get("name", "शेतकरी").split()[0]
    if language == 'hi':
        return (
            f"🌾 {name} जी, अभी AI सर्वर थोड़ा व्यस्त है।\n\n"
            "कृपया **१-२ मिनट बाद** फिर से पूछें — मैं जरूर जवाब दूंगी! 🙏\n\n"
            "अगर समस्या बनी रहे तो नजदीकी **कृषि विज्ञान केंद्र (KVK)** से संपर्क करें।"
        ), "AgriSathi AI (सर्वर अस्थायी व्यस्त)"
    if language == 'en':
        return (
            f"🌾 {name}, the AI server is briefly busy right now.\n\n"
            "Please **try again in 1–2 minutes** — I'll be ready to help! 🙏\n\n"
            "For urgent advice, contact your nearest **Krishi Vigyan Kendra (KVK)**."
        ), "AgriSathi AI (Server temporarily busy)"
    # Default: Marathi
    return (
        f"🌾 {name} जी, सध्या AI सर्व्हर थोडा व्यस्त आहे.\n\n"
        "कृपया **१-२ मिनिटांनी पुन्हा प्रयत्न करा** — मी नक्की उत्तर देईन! 🙏\n\n"
        "तातडीच्या सल्ल्यासाठी जवळच्या **कृषी विज्ञान केंद्र (KVK)** शी संपर्क साधा."
    ), "AgriSathi AI (सर्व्हर तात्पुरता व्यस्त)"


def fallback_response(user_query: str, language: str, farmer: dict):
    """
    Static agricultural responses shown when GROQ_API_KEY is not configured.
    """
    lower = user_query.lower()
    name  = farmer.get("name", "शेतकरी").split()[0]

    # Pest / Disease
    pest_kw = ['pest', 'कीड', 'कीटक', 'कीड़ा', 'इल्ली', 'रोग', 'disease',
               'अळी', 'किडा', 'फंगस', 'बुरशी', 'फसाद', 'नुकसान']
    if any(w in lower for w in pest_kw):
        if language == 'mr':
            return (
                "🌾 **कीड नियंत्रण सल्ला:**\n\n"
                "1. **लक्षणे:** पानांना छिद्रे — लष्करी अळी किंवा पाने खाणाऱ्या अळीची लक्षणे.\n"
                "2. **जैविक उपाय:** हेक्टरी ५ कामगंध सापळे लावा. निंबोळी अर्क ५% फवारा.\n"
                "3. **रासायनिक उपाय:** इमामेक्टिन बेन्झोएट ५% SG — ४ ग्रॅम/१० लि.\n\n"
                "💡 *सकाळी किंवा सायंकाळी फवारणी करा.*"
            ), ""
        if language == 'hi':
            return (
                "🌾 **कीट नियंत्रण सलाह:**\n\n"
                "1. **लक्षण:** पत्तियों में छेद — इल्ली का संकेत।\n"
                "2. **जैविक उपाय:** ५ फेरोमोन ट्रैप/एकड़। नीम तेल ५% छिड़काव।\n"
                "3. **रासायनिक उपाय:** इमामेक्टिन बेंजोएट ५% SG — ४ ग्राम/१० लि.\n\n"
                "💡 *सुबह या शाम छिड़काव करें।*"
            ), ""
        return (
            "🌾 **Pest Control Advisory:**\n\n"
            "1. **Symptoms:** Perforated leaves — indicates leaf-eating caterpillar.\n"
            "2. **Biological:** 5 pheromone traps/acre. Spray NSKE 5% (50ml/10L).\n"
            "3. **Chemical:** Emamectin Benzoate 5% SG @ 4g/10L.\n\n"
            "💡 *Spray during early morning or evening.*"
        ), ""

    # Weather
    weather_kw = ['weather', 'हवामान', 'पाऊस', 'मौसम', 'बारिश', 'rain',
                  'तापमान', 'वादळ', 'वर्षा', 'आंधी', 'ओला']
    if any(w in lower for w in weather_kw):
        if language == 'mr':
            return (
                "🌦️ **हवामान अंदाज:**\n\n"
                "• **तापमान:** कमाल ३२°C | किमान २१°C\n"
                "• **अंदाज:** दुपारनंतर हलक्या पावसाची ४०% शक्यता.\n"
                "• **सल्ला:** कापलेला माल सुरक्षित ठेवा. फवारणी पावसाआधी करू नका."
            ), ""
        if language == 'hi':
            return (
                "🌦️ **मौसम पूर्वानुमान:**\n\n"
                "• **तापमान:** अधिकतम ३२°C | न्यूनतम २१°C\n"
                "• **अनुमान:** दोपहर बाद हल्की बारिश की ४०% संभावना।\n"
                "• **सलाह:** कटी फसल सुरक्षित रखें और बारिश से पहले छिड़काव न करें।"
            ), ""
        return (
            "🌦️ **Weather Forecast:**\n\n"
            "• **Temp:** High 32°C | Low 21°C\n"
            "• **Forecast:** 40% chance of light afternoon showers.\n"
            "• **Advisory:** Protect harvested produce. Avoid spraying before rain."
        ), ""

    # Government Schemes
    scheme_kw = ['kisan', 'योजना', 'हप्ता', 'subsidy', 'योजनाएं', 'scheme',
                 'विमा', 'bima', 'किसान', 'अनुदान', 'सबसिडी', 'सरकार']
    if any(w in lower for w in scheme_kw):
        if language == 'mr':
            return (
                "🏛️ **PM-KISAN व शासकीय योजना:**\n\n"
                "• **PM-KISAN:** वार्षिक ₹६,००० (दर ४ महिन्यांनी ₹२,०००) DBT द्वारे.\n"
                "• **अटी:** आधार-लिंक बँक खाते + e-KYC पूर्ण + भूमी अभिलेख पडताळणी.\n"
                "• **नमो शेतकरी:** महाराष्ट्राकडून अतिरिक्त ₹६,०००/वर्ष."
            ), ""
        if language == 'hi':
            return (
                "🏛️ **PM-KISAN व सरकारी योजनाएं:**\n\n"
                "• **लाभ:** ₹६,०००/वर्ष — ३ किस्तों में DBT।\n"
                "• **शर्तें:** आधार-लिंक बैंक खाता + e-KYC + भूमि सत्यापन।"
            ), ""
        return (
            "🏛️ **PM-KISAN & Government Schemes:**\n\n"
            "• **Benefit:** ₹6,000/year in 3 installments via DBT.\n"
            "• **Requirements:** Aadhaar-linked bank account + e-KYC + land record verification."
        ), ""

    # Default generic response
    if language == 'mr':
        return (
            f"🌾 नमस्कार {name} जी!\n\n"
            "मी **कृषी सखी AI** आहे. मी तुम्हाला खालील विषयांत मदत करू शकते:\n"
            "• पिकांवरील कीड व रोग निदान\n"
            "• हवामान व पावसाचा अंदाज\n"
            "• खत व सिंचन व्यवस्थापन\n"
            "• PM-Kisan व शासकीय योजना\n\n"
            "कृपया तुमचा शेतीविषयक प्रश्न विचारा!"
        ), ""
    if language == 'hi':
        return (
            f"🌾 नमस्ते {name} जी!\n\n"
            "मैं **कृषि सखी AI** हूँ। मैं इन विषयों में आपकी मदद कर सकती हूँ:\n"
            "• फसल कीट एवं रोग प्रबंधन\n"
            "• मौसम व वर्षा पूर्वानुमान\n"
            "• खाद व सिंचाई प्रबंधन\n"
            "• सरकारी कृषि योजनाएं\n\n"
            "कृपया अपना खेती से जुड़ा सवाल पूछें!"
        ), ""
    return (
        f"🌾 Hello {name}!\n\n"
        "I'm **Krishi Sakhi AI**. I can help you with:\n"
        "• Crop pest & disease diagnosis\n"
        "• Weather forecasts & rain alerts\n"
        "• Fertilizer & irrigation management\n"
        "• PM-KISAN & government schemes\n\n"
        "Please ask your farming question!"
    ), ""

# ============================================================
# FLASK ROUTES
# ============================================================

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('chat_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('chat_dashboard'))

    # 1-Click Demo Login
    if request.args.get('demo') == 'true' or \
       (request.method == 'POST' and request.form.get('is_demo_action') == 'true'):
        session['user'] = {
            "name":       DEMO_USER["name"],
            "identifier": DEMO_USER["identifier"],
            "phone":      DEMO_USER["phone"],
            "location":   DEMO_USER["location"],
            "crops":      DEMO_USER["crops"],
            "language":   DEMO_USER["language"],
            "is_demo":    True
        }
        flash('डेमो शेतकरी खात्यात आपले स्वागत आहे! (Welcome to Demo Farmer Account!)', 'success')
        return redirect(url_for('chat_dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password   = request.form.get('password', '')

        if not identifier or not password:
            flash('कृपया मोबाईल क्रमांक / ईमेल आणि पासवर्ड प्रविष्ट करा.', 'danger')
            return render_template('login.html', identifier=identifier)

        user = users_db.get(identifier)
        if user and check_password_hash(user['password_hash'], password):
            session['user'] = {
                "name":       user["name"],
                "identifier": user["identifier"],
                "phone":      user["phone"],
                "location":   user.get("location", "Maharashtra, India"),
                "crops":      user.get("crops", "Mixed Crops"),
                "language":   user.get("language", "mr"),
                "is_demo":    user.get("is_demo", False)
            }
            flash(f'स्वागत आहे, {user["name"]}!', 'success')
            return redirect(url_for('chat_dashboard'))
        else:
            flash('चुकीचा आयडी किंवा पासवर्ड. कृपया डेमो लॉगिन वापरा किंवा पुन्हा प्रयत्न करा.', 'danger')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return redirect(url_for('chat_dashboard'))

    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        identifier = request.form.get('identifier', '').strip()
        phone      = request.form.get('phone', '').strip()
        location   = request.form.get('location', '').strip()
        crops      = request.form.get('crops', '').strip()
        language   = request.form.get('language', 'mr')
        password   = request.form.get('password', '')

        if not name or not identifier or not password:
            flash('कृपया सर्व आवश्यक माहिती भरा.', 'danger')
            return render_template('signup.html')

        if identifier in users_db:
            flash('हा मोबाईल किंवा ईमेल आधीच नोंदणीकृत आहे. कृपया लॉगिन करा.', 'warning')
            return redirect(url_for('login'))

        new_user = {
            "name":          name,
            "identifier":    identifier,
            "phone":         phone or identifier,
            "password_hash": generate_password_hash(password),
            "location":      location or "Maharashtra, India",
            "crops":         crops or "General Agriculture",
            "language":      language,
            "is_demo":       False
        }
        users_db[identifier] = new_user
        if phone:
            users_db[phone] = new_user

        session['user'] = {
            "name":       new_user["name"],
            "identifier": new_user["identifier"],
            "phone":      new_user["phone"],
            "location":   new_user["location"],
            "crops":      new_user["crops"],
            "language":   new_user["language"],
            "is_demo":    False
        }
        flash('नोंदणी यशस्वी झाली! कृषी सखीमध्ये आपले स्वागत आहे.', 'success')
        return redirect(url_for('chat_dashboard'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('आपण यशस्वीरित्या लॉगआउट झाला आहात.', 'info')
    return redirect(url_for('login'))


@app.route('/chat')
def chat_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', user=session['user'], sessions=DEMO_CHAT_SESSIONS)


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    Main Krishi Sakhi AI Chat Endpoint.
    Uses Groq AI API when GROQ_API_KEY is configured.
    Falls back to curated demo responses when key is absent.
    """
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized. Please login.'}), 401

    data       = request.get_json() or {}
    user_query = data.get('message', '').strip()
    language   = data.get('language') or session.get('user', {}).get('language', 'mr')
    farmer     = session.get('user', {})

    if not user_query:
        return jsonify({'error': 'Empty query'}), 400

    # Try Groq API with RAG retrieval
    response_text, source, rag_chunks = ask_groq(user_query, language, farmer)

    # Route the fallback correctly:
    # - API key IS configured but call failed → friendly "server busy" message
    # - API key NOT configured → static demo response
    if response_text is None:
        if GROQ_READY:
            # Key is set but Groq API failed (quota / timeout / network)
            response_text, source = _server_busy_message(language, farmer)
        else:
            # No API key — show demo/static responses
            response_text, source = fallback_response(user_query, language, farmer)
        rag_chunks = []

    source_documents = []
    for c in rag_chunks:
        source_documents.append({
            "file_name": c.get("source_file"),
            "page": c.get("page"),
            "category": c.get("category"),
            "score": c.get("score"),
            "match_type": c.get("match_type"),
            "snippet": c.get("text", "")[:180] + "..."
        })

    return jsonify({
        'status':   'success',
        'query':    user_query,
        'response': response_text,
        'source':   source,
        'source_documents': source_documents,
        'language': language,
        'ai_powered': GROQ_READY,
        'rag_active': len(source_documents) > 0
    })


@app.route('/api/status')
def api_status():
    """Health-check endpoint showing AI configuration state."""
    return jsonify({
        'app':        'Krishi Sakhi',
        'ai_ready':   GROQ_READY,
        'provider':   'Groq',
        'model':      Config.GROQ_MODEL if GROQ_READY else 'Demo Mode (no key)',
        'version':    '1.0.0'
    })


@app.route('/api/tts')
def api_tts():
    """
    Generate loud, natural, native Text-To-Speech audio in Marathi (or selected language).
    Uses gTTS for genuine regional pronunciation and maximum clarity for farmers.
    """
    text = request.args.get('text', '').strip()
    lang = request.args.get('lang', 'mr').strip()

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    # Clean markdown and formatting characters for smooth spoken voice
    cleaned = re.sub(r'[*#_~`\[\]()>+\-•]', ' ', text)
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    if not cleaned:
        cleaned = text

    # Cap audio length if extremely long to maintain fast response
    if len(cleaned) > 1200:
        cleaned = cleaned[:1200]

    valid_langs = {'mr': 'mr', 'hi': 'hi', 'en': 'en'}
    tts_lang = valid_langs.get(lang, 'mr')

    try:
        tts = gTTS(text=cleaned, lang=tts_lang, slow=False)
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        return send_file(
            audio_io,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='krishi_sakhi_voice.mp3'
        )
    except Exception as e:
        print(f"[TTS Generation Error]: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge')
def api_knowledge():
    """
    Returns statistics and manifest of agricultural PDF knowledge base,
    including live FAISS vector index status (Step 4 & Step 5 RAG).
    """
    manifest_path = os.path.join(os.path.dirname(__file__), "data", "knowledge_base", "knowledge_manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as e:
            manifest = {"error": f"Failed to read knowledge manifest: {str(e)}"}

    # Append live RAG / FAISS engine status
    rag_info = get_rag_status()
    manifest["rag_engine"] = rag_info
    return jsonify(manifest)


@app.route('/api/search', methods=['GET', 'POST'])
def api_search():
    """
    Direct semantic retrieval endpoint for testing and RAG inspections.
    Queries the FAISS vector index (with BM25 fallback) and returns top matched agricultural chunks.
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        top_k = int(data.get('top_k', 3))
    else:
        query = request.args.get('q', '').strip()
        top_k = int(request.args.get('k', 3))

    if not query:
        return jsonify({"error": "Query parameter 'q' or json 'query' is required"}), 400

    results = search_knowledge_base(query, top_k=top_k)
    return jsonify({
        "status": "success",
        "query": query,
        "count": len(results),
        "results": [
            {
                "file_name": r.get("source_file"),
                "page": r.get("page"),
                "category": r.get("category"),
                "score": r.get("score"),
                "match_type": r.get("match_type"),
                "snippet": r.get("text", "")[:250] + "..."
            }
            for r in results
        ]
    })


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
