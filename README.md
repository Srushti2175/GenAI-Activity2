# 🌾 Krishi Sakhi (कृषी सखी / कृषि सखी)

> **Multilingual AI Agricultural Assistant & Voice Chatbot for Indian Farmers**  
> Powered by **Groq AI** + **RAG (BM25 / FAISS)** | Supports **मराठी • हिंदी • English**

**Krishi Sakhi (AgriSathi AI)** is a web-based, voice-enabled AI assistant built with Flask to help Indian farmers get practical, accurate guidance on crop pest & disease management, fertilizers, irrigation, weather precautions, and government farmer welfare schemes in **Marathi**, **Hindi**, and **English**.

---

## ✨ Key Features

- **⚡ Fast Multilingual AI (`Groq`):** Powered by `openai/gpt-oss-120b` on Groq Cloud with automatic failover to `openai/gpt-oss-20b` and `qwen/qwen3.8-27b` (~1.4s–2s response time).
- **📚 Retrieval-Augmented Generation (RAG):** Grounds AI responses in verified agricultural manuals and guides (252 semantic chunks across 4 publications) using Devanagari-aware **BM25** keyword search and a **FAISS** vector index (`IndexFlatIP`).
- **🔤 Legacy Marathi Font Decoder:** Custom `SHREE-DEV-0727` (Shree-Lipi) to Unicode UTF-8 Devanagari converter (`utils/shreedev_converter.py`) for extracting clean Marathi text from legacy DTP agricultural PDFs.
- **🎙️ Voice Input (Speech-to-Text):** Real-time browser Web Speech API (`mr-IN`, `hi-IN`, `en-IN`) with live speech visualization and 650 ms silence auto-submit.
- **🔊 Voice Output (Dual-Tier Text-to-Speech):** Instant browser `speechSynthesis` sentence-by-sentence playback with Indian/Marathi/Hindi voice prioritization, backed by a Flask `/api/tts` (`gTTS`) MP3 fallback.
- **🌐 Full UI Localization:** Instant switching between **मराठी (Marathi)**, **हिंदी (Hindi)**, and **English** with localized quick-prompt chips.
- **🔐 Farmer Authentication:** Login, farmer registration (capturing Name, Phone, Location, Crops, and Preferred Language), and **1-Click Demo Login**.
- **🛡️ Safety-Conscious Prompting:** Structured, voice-friendly guidance that avoids fabricating chemical dosages or scheme rules and recommends Krishi Vigyan Kendra (KVK) consultation for serious crop diseases.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Flask 3.1, Werkzeug |
| **LLM Provider** | Groq Python SDK (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`) |
| **RAG & Search** | FAISS (`faiss-cpu`), NumPy, Devanagari-aware BM25 (`[\u0900-\u097F\w]+`) |
| **PDF Ingestion** | `pypdf`, custom Shree-Dev-0727 → Unicode Devanagari transliterator |
| **Voice (STT / TTS)** | Web Speech API (browser), `window.speechSynthesis`, `gTTS` (`/api/tts`) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Font Awesome, `marked` (Markdown) |

---

## 📂 Project Structure

```text
krishiSakhi/
├── app.py                              # Flask app, auth routes, Groq + RAG chat & TTS APIs
├── config.py                           # Environment & Groq/optional Gemini config
├── ingest_knowledge.py                 # CLI script to scan PDFs & generate semantic chunks
├── build_vector_index.py               # Builds FAISS index & local BM25 index
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Excludes .env, .venv, __pycache__, scratch/
├── README.md                           # Project documentation
│
├── utils/
│   ├── __init__.py
│   ├── pdf_processor.py                # PDF text extraction & sentence-aware chunking
│   ├── shreedev_converter.py           # Legacy Shree-Dev-0727 to Unicode Devanagari decoder
│   └── rag_engine.py                   # BM25 + FAISS retrieval & prompt context formatter
│
├── data/
│   └── knowledge_base/
│       ├── processed_chunks.json       # 252 semantic chunks with page & category metadata
│       ├── knowledge_manifest.json     # Document inventory & stats
│       ├── faiss_index.bin             # FAISS dense vector index (252 × 3072)
│       ├── chunk_embeddings.npy        # Normalized chunk embeddings
│       ├── bm25_index.json             # Local BM25 keyword search index
│       ├── fertilizers/                # Fertilizer dosage & NPK guides
│       ├── organic_farming/            # 73-page Organic Farming Manual (Marathi)
│       ├── pest_control/               # Soybean & cotton pest management guides
│       └── schemes/                    # PM-KISAN & government scheme guides
│
├── static/
│   ├── css/
│   │   ├── style.css                   # Base theme & typography
│   │   ├── auth.css                    # Login & signup styles
│   │   └── chat.css                    # Chat dashboard & voice UI styles
│   └── js/
│       ├── auth.js                     # Auth form validation & demo login helper
│       ├── chat.js                     # Chat client, STT/TTS voice engine, markdown rendering
│       └── translations.js             # UI dictionaries for Marathi, Hindi & English
│
└── templates/
    ├── base.html                       # Base layout with Noto Sans Devanagari fonts
    ├── login.html                      # Login page with 1-Click Demo Login
    ├── signup.html                     # Farmer registration page
    └── chat.html                       # Main chatbot & voice assistant dashboard
```

---

## 📚 Knowledge Base

| Document | Category | Pages | Chunks | Description |
|---|---|---:|---:|---|
| `Organic_farming_Training_manual_Marathi.pdf` | `organic_farming` | 73 | 241 | सेंद्रीय शेती प्रशिक्षण पुस्तिका (MOFF Pune) — organic fertilizers, Jeevamrut, Dashaparni Ark, seed treatment |
| `fertilizer_recommendations_guide.pdf` | `fertilizers` | 1 | 3 | NPK, Urea, DAP, and Potash dosage guidelines |
| `soybean_cotton_pest_guide.pdf` | `pest_control` | 1 | 4 | Soybean & cotton pest control (stem fly, leaf-eating caterpillar, bollworm) |
| `pm_kisan_and_govt_schemes_guide.pdf` | `schemes` | 1 | 4 | PM-KISAN, Namo Shetkari Mahasanman Nidhi, and PMFBY crop insurance |

- **Total:** 4 PDFs, 76 pages, **252 semantic chunks**

---

## ⚙️ Local Setup & Installation

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.12)
- **Google Chrome** or **Microsoft Edge** (recommended for Web Speech API voice input)
- A free **Groq API Key** from [console.groq.com/keys](https://console.groq.com/keys)

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/krishiSakhi.git
cd krishiSakhi
```

### 3. Create & Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables (`.env`)
Create a `.env` file in the project root (never commit this file to Git):

```env
SECRET_KEY=your-strong-random-flask-secret-key
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
DEFAULT_LANGUAGE=mr
```

*(Optional)* If you also want dense FAISS query embeddings via Google Gemini alongside Groq, add a valid Google AI Studio key (`AIza...`):
```env
GEMINI_API_KEY=AIza_your_optional_gemini_key
```
Without a Gemini embedding key, the RAG engine automatically uses fast local Devanagari-aware **BM25** retrieval (< 5 ms).

### 6. Run the Application
```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser and click **1-Click Demo Login** (or register a new farmer account).

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET`, `POST` | `/login` | Farmer login & 1-Click Demo Login (`?demo=true`) |
| `GET`, `POST` | `/signup` | New farmer registration |
| `GET` | `/logout` | Clear session and redirect to login |
| `GET` | `/chat` | Main chat & voice assistant dashboard |
| `POST` | `/api/chat` | Main RAG + Groq multilingual chat endpoint (`message`, `language`) |
| `GET` | `/api/tts` | `gTTS` MP3 audio synthesis (`?lang=mr&text=...`) |
| `GET` | `/api/knowledge` | Knowledge base manifest & live RAG engine status |
| `GET`, `POST` | `/api/search` | Direct semantic/BM25 retrieval inspection (`?q=...&k=3`) |
| `GET` | `/api/status` | Application & AI provider health check |

---

## 🗺️ Roadmap & Current Status

- [x] Project setup, Flask auth, and responsive multilingual UI (`mr` / `hi` / `en`)
- [x] Groq AI integration with automatic model failover
- [x] Agricultural PDF ingestion pipeline + `SHREE-DEV-0727` Marathi font decoder
- [x] RAG engine with FAISS vector index + Devanagari-aware BM25 fallback
- [x] Browser Speech-to-Text (Web Speech API) & dual-tier Text-to-Speech (`speechSynthesis` + `gTTS`)
- [ ] Server-side Whisper voice transcription endpoint for browsers without Web Speech API
- [ ] Live weather API integration for the sidebar weather widget
- [ ] Crop disease image diagnosis via vision model
- [ ] Persistent database (SQLite / PostgreSQL) replacing in-memory `users_db`
- [ ] Automated `pytest` test suite

---

## 🛡️ Security Notes

- `.env` is excluded via `.gitignore` so API keys are never pushed to GitHub.
- Passwords are hashed with Werkzeug's `generate_password_hash`.
- Replace the in-memory `users_db` and default `SECRET_KEY` before deploying to production.

---

## 📄 License

This project is intended for educational and agricultural assistance purposes.
