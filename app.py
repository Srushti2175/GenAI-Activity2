import os
import io
import re
import json
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from gtts import gTTS
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# ============================================================
# GEMINI AI SETUP
# ============================================================
GEMINI_READY = Config.validate()

if GEMINI_READY:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(
        model_name=Config.GEMINI_MODEL,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=1024,
        ),
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT",       "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH",      "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT","threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT","threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
    )
    print(f"[OK] Gemini API ready - model: {Config.GEMINI_MODEL}")
else:
    gemini_model = None

# ============================================================
# SYSTEM PROMPT FOR KRISHI SAKHI AI
# ============================================================
SYSTEM_PROMPT = """You are **Krishi Sakhi (कृषी सखी / कृषि सखी)**, a trusted, expert, and compassionate AI assistant designed exclusively to help Indian farmers.

Your specializations include:
- 🌾 Crop pest and disease diagnosis with specific medicine names, dosages, and application schedules.
- 🌦️ Agricultural weather interpretation and farm safety advisories.
- 🧪 Fertilizer management (NPK ratios, urea, DAP, micronutrients) with crop-wise recommendations.
- 🏛️ Indian government welfare schemes: PM-KISAN, Pradhan Mantri Fasal Bima Yojana (PMFBY), Namo Shetkari Mahasanman Nidhi, soil health cards, Kisan Credit Card (KCC), and state-level subsidies.
- 📈 Market price guidance and seasonal selling advisory.
- 🌱 Organic farming, intercropping, and water-saving irrigation techniques.

**STRICT LANGUAGE RULES (CRITICAL):**
- The farmer's selected language will be passed to you.
- You MUST generate your response ENTIRELY in that SELECTED LANGUAGE.
- If the selected language is Marathi (मराठी), write your entire answer in clean, spoken, natural Marathi (मराठी देवनागरी लिपी). Even if the user asked in English or Roman script (e.g. "soyabean kid upay"), your response MUST be in Marathi so that the farmer can listen to it via loud Marathi Text-to-Speech!
- If the selected language is Hindi (हिंदी), write your entire response in Hindi (हिंदी).
- If the selected language is English, write in English.

**Voice & Response Style:**
- The farmer will listen to your answer out loud! Use warm, respectful spoken tone (उदा. "राम-राम शेतकरी बंधू", "नमस्कार").
- Use simple, practical language that uneducated rural farmers can immediately grasp.
- Always use short, clear bullet points or numbered steps for actionable advice.
- Include specific medicine/fertilizer names, quantities (grams/ml per 10 liters of water), and exact timings (morning/evening).
- Keep responses concise and focused — avoid unnecessary jargon or lengthy disclaimers.
- Do NOT answer questions unrelated to agriculture, farming, or farmer welfare schemes. Politely redirect instead.

You represent the trust and care of a knowledgeable local agricultural extension officer who speaks the farmer's own language."""

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
# HELPER: BUILD LANGUAGE-AWARE GEMINI PROMPT
# ============================================================
def build_prompt(user_query: str, language: str, farmer: dict) -> str:
    lang_map = {"mr": "Marathi (मराठी)", "hi": "Hindi (हिंदी)", "en": "English"}
    lang_label = lang_map.get(language, "Marathi (मराठी)")

    farmer_context = (
        f"Farmer Name: {farmer.get('name', 'शेतकरी')}\n"
        f"Location: {farmer.get('location', 'Maharashtra, India')}\n"
        f"Primary Crops: {farmer.get('crops', 'Mixed crops')}\n"
        f"User's Selected Interface Language: {lang_label}"
    )

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"--- Farmer Context ---\n{farmer_context}\n\n"
        f"--- Farmer's Question ---\n{user_query}\n\n"
        f"[MANDATORY LANGUAGE INSTRUCTION]: The farmer has selected {lang_label}. "
        f"Your response will be READ OUT LOUD in {lang_label} voice using Text-To-Speech. "
        f"You MUST write the ENTIRE answer in {lang_label}."
    )

# ============================================================
# HELPER: CALL GEMINI API WITH ULTRA-FAST REUSE
# ============================================================
def ask_gemini(user_query: str, language: str, farmer: dict):
    global gemini_model
    if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY == 'your_gemini_api_key_here':
        return None, None

    prompt = build_prompt(user_query, language, farmer)

    # 1. Fast path: reuse already loaded model in milliseconds
    if gemini_model:
        try:
            response = gemini_model.generate_content(prompt)
            if response and response.text:
                model_name = getattr(gemini_model, 'model_name', Config.GEMINI_MODEL)
                source = f"Google Gemini AI ({model_name}) | Krishi Sakhi"
                return response.text.strip(), source
        except Exception as e:
            print(f"[Gemini Fast Path Error]: {e}")

    # 2. Fallback path: initialize fastest candidate model
    candidate_models = [Config.GEMINI_MODEL, 'gemini-2.5-flash', 'gemini-flash-latest']
    seen = set()
    candidate_models = [m for m in candidate_models if not (m in seen or seen.add(m))]

    for model_name in candidate_models:
        try:
            m = genai.GenerativeModel(
                model_name=model_name,
                generation_config=genai.GenerationConfig(
                    temperature=0.6,
                    top_p=0.9,
                    max_output_tokens=600,
                )
            )
            response = m.generate_content(prompt)
            if response and response.text:
                gemini_model = m
                source = f"Google Gemini AI ({model_name}) | Krishi Sakhi"
                return response.text.strip(), source
        except Exception as e:
            print(f"[Gemini Error with {model_name}]: {e}")
            continue

    return None, None

# ============================================================
# HELPER: STATIC FALLBACK RESPONSES (when API key not set)
# ============================================================
def fallback_response(user_query: str, language: str, farmer: dict):
    lower = user_query.lower()
    name  = farmer.get("name", "शेतकरी").split()[0]

    # Pest / Disease
    if any(w in lower for w in ['pest', 'कीड', 'कीटक', 'कीड़ा', 'इल्ली', 'रोग', 'disease']):
        if language == 'mr':
            return (
                "🌾 **कीड नियंत्रण सल्ला (Demo Mode):**\n\n"
                "1. **लक्षणे:** पानांना छिद्रे — लष्करी अळी किंवा पाने खाणाऱ्या अळीची लक्षणे.\n"
                "2. **जैविक उपाय:** हेक्टरी ५ कामगंध सापळे लावा. निंबोळी अर्क ५% (५० मिली/१० लि.) फवारा.\n"
                "3. **रासायनिक उपाय:** **इमामेक्टिन बेन्झोएट ५% SG** ४ ग्रॅम/१० लि. किंवा "
                "**क्लोराँट्रानिलीप्रोल १८.५% SC** ३ मिली/१० लि. फवारणी करा.\n\n"
                "💡 *सकाळी किंवा सायंकाळी फवारणी करा.*\n\n"
                "*(GEMINI_API_KEY .env मध्ये टाका म्हणजे लाइव्ह AI उत्तरे मिळतील!)*"
            ), "ICAR-KVK कीड नियंत्रण मार्गदर्शिका (Demo)"

        if language == 'hi':
            return (
                "🌾 **कीट नियंत्रण सलाह (Demo Mode):**\n\n"
                "1. **लक्षण:** पत्तियों में छेद — इल्ली का संकेत.\n"
                "2. **जैविक उपाय:** ५ फेरोमोन ट्रैप/एकड़। नीम तेल ५% (५० मिली/१० लि.) छिड़काव.\n"
                "3. **रासायनिक उपाय:** **इमामेक्टिन बेंजोएट ५% SG** ४ ग्राम/१० लि.\n\n"
                "💡 *सुबह या शाम छिड़काव करें।*\n\n"
                "*(GEMINI_API_KEY .env में डालें — Live AI जवाब पाएं!)*"
            ), "ICAR कृषि विज्ञान केंद्र (Demo)"

        return (
            "🌾 **Pest Control Advisory (Demo Mode):**\n\n"
            "1. **Symptoms:** Perforated leaves — indicates leaf-eating caterpillar.\n"
            "2. **Biological:** 5 pheromone traps/acre. Spray NSKE 5% (50ml/10L water).\n"
            "3. **Chemical:** **Emamectin Benzoate 5% SG** @ 4g/10L water.\n\n"
            "💡 *Spray during early morning or evening.*\n\n"
            "*(Add GEMINI_API_KEY to .env for live AI responses!)*"
        ), "ICAR Agricultural Research Guide (Demo)"

    # Weather
    if any(w in lower for w in ['weather', 'हवामान', 'पाऊस', 'मौसम', 'बारिश', 'rain']):
        if language == 'mr':
            return (
                "🌦️ **हवामान अंदाज (Demo Mode):**\n\n"
                "• **तापमान:** कमाल ३२°C | किमान २१°C\n"
                "• **अंदाज:** दुपारनंतर हलक्या पावसाची ४०% शक्यता.\n"
                "• **सल्ला:** कापलेला माल सुरक्षित ठेवा. फवारणी पावसाआधी करू नका.\n\n"
                "*(GEMINI_API_KEY जोडा — थेट IMD आधारित AI उत्तर मिळेल!)*"
            ), "IMD कृषी हवामान सेवा (Demo)"
        if language == 'hi':
            return (
                "🌦️ **मौसम पूर्वानुमान (Demo Mode):**\n\n"
                "• **तापमान:** अधिकतम ३२°C | न्यूनतम २१°C\n"
                "• **अनुमान:** दोपहर बाद हल्की बारिश की ४०% संभावना.\n"
                "• **सलाह:** कटी फसल सुरक्षित रखें।\n\n"
                "*(GEMINI_API_KEY .env में डालें!)*"
            ), "IMD ग्रामीण कृषि मौसम सेवा (Demo)"
        return (
            "🌦️ **Weather Forecast (Demo Mode):**\n\n"
            "• **Temp:** High 32°C | Low 21°C\n"
            "• **Forecast:** 40% chance of light afternoon showers.\n"
            "• **Advisory:** Protect harvested produce. Avoid spraying before rain.\n\n"
            "*(Add GEMINI_API_KEY to .env for live responses!)*"
        ), "IMD Agro-Met Service (Demo)"

    # Government Schemes
    if any(w in lower for w in ['kisan', 'योजना', 'हप्ता', 'subsidy', 'योजनाएं', 'scheme', 'विमा', 'bima']):
        if language == 'mr':
            return (
                "🏛️ **PM-KISAN व शासकीय योजना (Demo Mode):**\n\n"
                "• **PM-KISAN:** वार्षिक ₹६,००० (दर ४ महिन्यांनी ₹२,०००) DBT द्वारे.\n"
                "• **अटी:** आधार-लिंक बँक खाते + e-KYC पूर्ण + भूमी अभिलेख पडताळणी.\n"
                "• **नमो शेतकरी:** महाराष्ट्राकडून अतिरिक्त ₹६,०००/वर्ष.\n\n"
                "*(GEMINI_API_KEY जोडा — सविस्तर AI सल्ला मिळेल!)*"
            ), "कृषी व शेतकरी कल्याण मंत्रालय (Demo)"
        if language == 'hi':
            return (
                "🏛️ **PM-KISAN योजना (Demo Mode):**\n\n"
                "• **लाभ:** ₹६,०००/वर्ष — ३ किस्तों में DBT.\n"
                "• **शर्तें:** आधार-लिंक बैंक खाता + e-KYC + भूमि सत्यापन.\n\n"
                "*(GEMINI_API_KEY .env में डालें!)*"
            ), "कृषि मंत्रालय, भारत सरकार (Demo)"
        return (
            "🏛️ **PM-KISAN & Government Schemes (Demo Mode):**\n\n"
            "• **Benefit:** ₹6,000/year in 3 installments of ₹2,000 via DBT.\n"
            "• **Requirements:** Aadhaar-linked bank account + e-KYC + land record verification.\n\n"
            "*(Add GEMINI_API_KEY to .env for live AI responses!)*"
        ), "Ministry of Agriculture, Govt of India (Demo)"

    # Default
    if language == 'mr':
        return (
            f"🌾 नमस्कार {name} जी!\n\n"
            "मी **कृषी सखी AI** आहे, परंतु सध्या मी **Demo Mode** मध्ये आहे.\n\n"
            "मी खालील विषयांत मदत करू शकते:\n"
            "• पिकांवरील कीड व रोग निदान\n"
            "• हवामान व पावसाचा अंदाज\n"
            "• खत व सिंचन व्यवस्थापन\n"
            "• PM-Kisan व शासकीय योजना\n\n"
            "**पूर्ण AI सक्रिय करण्यासाठी:** `.env` फाइलमध्ये `GEMINI_API_KEY` टाका.\n"
            "मोफत Key मिळवा: https://aistudio.google.com/app/apikey"
        ), "कृषी सखी AI (Demo Mode)"

    if language == 'hi':
        return (
            f"🌾 नमस्ते {name} जी!\n\n"
            "मैं **कृषि सखी AI** हूँ, लेकिन अभी **Demo Mode** में हूँ.\n\n"
            "मैं इन विषयों में मदद कर सकती हूँ:\n"
            "• फसल कीट एवं रोग प्रबंधन\n"
            "• मौसम व वर्षा पूर्वानुमान\n"
            "• खाद व सिंचाई प्रबंधन\n"
            "• सरकारी कृषि योजनाएं\n\n"
            "**Live AI के लिए:** `.env` में `GEMINI_API_KEY` डालें.\n"
            "मुफ्त Key: https://aistudio.google.com/app/apikey"
        ), "कृषि सखी AI (Demo Mode)"

    return (
        f"🌾 Hello {name}!\n\n"
        "I'm **Krishi Sakhi AI**, currently in **Demo Mode**.\n\n"
        "I can help you with:\n"
        "• Crop pest & disease diagnosis\n"
        "• Weather forecasts & rain alerts\n"
        "• Fertilizer & irrigation management\n"
        "• PM-KISAN & government schemes\n\n"
        "**To enable full AI:** Add `GEMINI_API_KEY` to your `.env` file.\n"
        "Get a free key at: https://aistudio.google.com/app/apikey"
    ), "Krishi Sakhi AI (Demo Mode)"

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
    Uses Google Gemini API when GEMINI_API_KEY is configured.
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

    # Try Gemini API first
    response_text, source = ask_gemini(user_query, language, farmer)

    # Fallback to demo responses if Gemini not configured or errored
    if response_text is None:
        response_text, source = fallback_response(user_query, language, farmer)

    return jsonify({
        'status':   'success',
        'query':    user_query,
        'response': response_text,
        'source':   source,
        'language': language,
        'ai_powered': GEMINI_READY
    })


@app.route('/api/status')
def api_status():
    """Health-check endpoint showing AI configuration state."""
    return jsonify({
        'app':        'Krishi Sakhi',
        'ai_ready':   GEMINI_READY,
        'model':      Config.GEMINI_MODEL if GEMINI_READY else 'Demo Mode (no key)',
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
    Returns statistics and manifest of agricultural PDF knowledge base.
    Used for monitoring ingested agricultural reference guides for RAG (Step 4 & 5).
    """
    manifest_path = os.path.join(os.path.dirname(__file__), "data", "knowledge_base", "knowledge_manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": f"Failed to read knowledge manifest: {str(e)}"}), 500
    return jsonify({
        "status": "empty",
        "message": "No knowledge base manifest found. Run 'python ingest_knowledge.py' first.",
        "total_documents": 0,
        "total_chunks": 0
    })


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
