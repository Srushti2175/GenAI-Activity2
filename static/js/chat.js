// =========================================================
// KRISHI SAKHI - CHATBOT & VOICE ASSISTANT CLIENT ENGINE
// =========================================================

let currentLanguage = 'mr';
let autoSpeakEnabled = true;
let isRecording = false;
let speechRecognizer = null;
let currentUtterance = null;
let activeSpeakingBtn = null;
let systemVoices = [];

function loadSystemVoices() {
    if ('speechSynthesis' in window) {
        systemVoices = window.speechSynthesis.getVoices();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const langSelect = document.getElementById('languageSelect');
    if (langSelect) {
        currentLanguage = langSelect.value || 'mr';
        applyLanguage(currentLanguage);
    }
    loadSystemVoices();
    if ('speechSynthesis' in window) {
        window.speechSynthesis.onvoiceschanged = loadSystemVoices;
    }
    initSpeechRecognition();
});

// =========================================================
// LANGUAGE SWITCHER & UI LOCALIZATION
// =========================================================
function changeLanguage(lang) {
    currentLanguage = lang;
    applyLanguage(lang);
}

function applyLanguage(lang) {
    const dict = translations[lang] || translations['mr'];

    // Update data-i18n elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            el.innerHTML = dict[key];
        }
    });

    // Update placeholder
    const input = document.getElementById('userInput');
    if (input && dict.input_placeholder) {
        input.placeholder = dict.input_placeholder;
    }

    // Update welcome banner if visible
    const heroTitle = document.getElementById('welcomeTitle');
    const heroSubtitle = document.getElementById('welcomeSubtitle');
    if (heroTitle && heroSubtitle) {
        // Extract farmer first name
        const profileName = document.querySelector('.profile-name');
        const firstName = profileName ? profileName.textContent.trim().split(' ')[0] : 'शेतकरी';
        heroTitle.innerHTML = dict.welcome_title(firstName);
        heroSubtitle.innerHTML = dict.welcome_subtitle;
    }

    // Update prompt chips
    renderPromptChips(dict.chips);

    // Update speech recognition language
    if (speechRecognizer) {
        if (lang === 'mr') speechRecognizer.lang = 'mr-IN';
        else if (lang === 'hi') speechRecognizer.lang = 'hi-IN';
        else speechRecognizer.lang = 'en-IN';
    }
}

function renderPromptChips(chips) {
    const grid = document.querySelector('.prompt-chips-grid');
    if (!grid || !chips) return;

    grid.innerHTML = '';
    chips.forEach(chip => {
        const btn = document.createElement('button');
        btn.className = 'prompt-chip';
        btn.onclick = () => sendPrompt(chip.query);
        btn.innerHTML = `
            <i class="fa-solid ${chip.icon}"></i>
            <span>${chip.text}</span>
        `;
        grid.appendChild(btn);
    });
}

// =========================================================
// CHAT INTERACTION & API COMMUNICATION
// =========================================================
function handleFormSubmit(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('userInput');
    const query = input.value.trim();
    if (!query) return;

    input.value = '';
    autoResizeTextarea(input);
    sendMessage(query);
}

function handleTextareaKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleFormSubmit();
    }
}

function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function sendPrompt(promptText) {
    sendMessage(promptText);
}

function sendMessage(text) {
    // Hide welcome hero on first message
    const hero = document.getElementById('welcomeHero');
    if (hero) hero.style.display = 'none';

    // Render user message bubble
    appendMessage('user', text);

    // Show AI typing indicator
    const typingId = showTypingIndicator();

    // Call backend API
    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: text,
            language: currentLanguage
        })
    })
    .then(res => res.json())
    .then(data => {
        removeTypingIndicator(typingId);
        if (data.status === 'success') {
            const listenBtn = appendMessage('bot', data.response, data.source);
            if (autoSpeakEnabled) {
                // Read out the response aloud in loud, clear voice
                speakText(data.response, listenBtn);
            }
        } else {
            appendMessage('bot', 'क्षमस्व, काहीतरी अडचण आली आहे. कृपया पुन्हा प्रयत्न करा. (Error processing request)');
        }
    })
    .catch(err => {
        console.error('Chat error:', err);
        removeTypingIndicator(typingId);
        appendMessage('bot', 'सर्व्हरशी संपर्क होऊ शकला नाही. कृपया इंटरनेट तपासा. (Failed to connect to server)');
    });
}

function appendMessage(sender, content, source) {
    const container = document.getElementById('chatMessages');
    const row = document.createElement('div');
    row.className = `message-row ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' 
        ? '<i class="fa-solid fa-user"></i>' 
        : '<i class="fa-solid fa-wheat-awn"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    let listenBtn = null;

    if (sender === 'user') {
        bubble.textContent = content;
    } else {
        // Parse markdown for rich formatting
        const formattedHtml = typeof marked !== 'undefined' ? marked.parse(content) : content.replace(/\n/g, '<br>');
        bubble.innerHTML = formattedHtml;

        // Source Citation badge
        if (source) {
            const sourceBadge = document.createElement('div');
            sourceBadge.className = 'source-tag';
            sourceBadge.innerHTML = `<i class="fa-solid fa-book-open"></i> <span>संदर्भ (Source): ${source}</span>`;
            bubble.appendChild(sourceBadge);
        }

        // Action Buttons: Listen (TTS), Copy
        const dict = translations[currentLanguage] || translations['mr'];
        const actions = document.createElement('div');
        actions.className = 'bubble-actions';

        listenBtn = document.createElement('button');
        listenBtn.className = 'btn-bubble-action';
        listenBtn.innerHTML = `<i class="fa-solid fa-volume-high"></i> <span class="listen-text">${dict.listen_btn}</span>`;
        listenBtn.onclick = () => toggleSpeechPlayback(content, listenBtn);

        const copyBtn = document.createElement('button');
        copyBtn.className = 'btn-bubble-action';
        copyBtn.innerHTML = `<i class="fa-regular fa-copy"></i> <span>${dict.copy_btn}</span>`;
        copyBtn.onclick = () => copyText(content, copyBtn);

        actions.appendChild(listenBtn);
        actions.appendChild(copyBtn);
        bubble.appendChild(actions);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    container.appendChild(row);

    // Scroll to bottom smoothly
    container.scrollTop = container.scrollHeight;
    return listenBtn;
}

function showTypingIndicator() {
    const container = document.getElementById('chatMessages');
    const row = document.createElement('div');
    const id = 'typing-' + Date.now();
    row.id = id;
    row.className = 'message-row bot';

    row.innerHTML = `
        <div class="message-avatar">
            <i class="fa-solid fa-wheat-awn"></i>
        </div>
        <div class="message-bubble">
            <div class="typing-dots">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        </div>
    `;

    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// =========================================================
// ULTRA-FAST REAL-TIME SPEECH TO TEXT (STT)
// =========================================================
let sttSilenceTimer = null;
let currentRecordedText = '';

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn('Speech recognition not natively supported in this browser.');
        return;
    }

    speechRecognizer = new SpeechRecognition();
    speechRecognizer.continuous = true;
    speechRecognizer.interimResults = true; // Stream words in REAL-TIME milliseconds!
    speechRecognizer.maxAlternatives = 1;
    speechRecognizer.lang = currentLanguage === 'mr' ? 'mr-IN' : (currentLanguage === 'hi' ? 'hi-IN' : 'en-IN');

    speechRecognizer.onstart = () => {
        isRecording = true;
        currentRecordedText = '';
        clearTimeout(sttSilenceTimer);
        updateRecordingUI(true);
    };

    speechRecognizer.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }

        const text = (finalTranscript || interimTranscript).trim();
        if (text) {
            currentRecordedText = text;
            const input = document.getElementById('userInput');
            if (input) {
                input.value = text;
                autoResizeTextarea(input);
            }
        }

        // Fast silence detection: auto-submit in 650ms after speech pause!
        clearTimeout(sttSilenceTimer);
        sttSilenceTimer = setTimeout(() => {
            if (isRecording && currentRecordedText.trim()) {
                const query = currentRecordedText.trim();
                stopVoiceRecognition();
                sendMessage(query);
            }
        }, 650);
    };

    speechRecognizer.onerror = (event) => {
        if (event.error !== 'no-speech') {
            console.warn('STT event error:', event.error);
            stopVoiceRecognition();
        }
    };

    speechRecognizer.onend = () => {
        isRecording = false;
        clearTimeout(sttSilenceTimer);
        updateRecordingUI(false);
    };
}

function toggleVoiceRecognition() {
    if (!speechRecognizer) {
        alert('आपल्या ब्राउझरमध्ये थेट व्हॉईस सपोर्ट उपलब्ध नाही. कृपया Chrome किंवा Edge वापरा. पुढील चरणात बॅकएंड Whisper व्हॉईस जोडले जाईल.');
        return;
    }

    if (isRecording) {
        stopVoiceRecognition();
    } else {
        startVoiceRecognition();
    }
}

function startVoiceRecognition() {
    if (!speechRecognizer) return;
    try {
        speechRecognizer.lang = currentLanguage === 'mr' ? 'mr-IN' : (currentLanguage === 'hi' ? 'hi-IN' : 'en-IN');
        speechRecognizer.start();
    } catch (e) {
        console.error('Speech start error:', e);
    }
}

function stopVoiceRecognition() {
    isRecording = false;
    if (speechRecognizer) {
        try { speechRecognizer.stop(); } catch (e) {}
    }
    updateRecordingUI(false);
}

function updateRecordingUI(active) {
    const micBtn = document.getElementById('micBtn');
    const voiceBanner = document.getElementById('voiceBanner');

    if (micBtn) {
        if (active) micBtn.classList.add('recording');
        else micBtn.classList.remove('recording');
    }

    if (voiceBanner) {
        voiceBanner.style.display = active ? 'flex' : 'none';
    }
}

// =========================================================
// ULTRA-FAST TEXT TO SPEECH (TTS) - STARTS IN MILLISECONDS
// =========================================================
let currentAudio = null;
let speechQueue = [];
let isSpeakingQueue = false;

function stopAllAudio() {
    isSpeakingQueue = false;
    speechQueue = [];
    if (currentAudio) {
        try {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        } catch (e) {}
        currentAudio = null;
    }
    if ('speechSynthesis' in window) {
        try {
            window.speechSynthesis.cancel();
        } catch (e) {}
    }
    resetSpeakingButton();
}

function toggleAutoSpeak() {
    autoSpeakEnabled = !autoSpeakEnabled;
    const btn = document.getElementById('voiceAutoSpeakBtn');
    if (btn) {
        if (autoSpeakEnabled) {
            btn.classList.add('active');
            btn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
            btn.title = "ऑटो व्हॉईस उत्तर चालू (Auto Speak Enabled)";
        } else {
            btn.classList.remove('active');
            btn.innerHTML = '<i class="fa-solid fa-volume-xmark"></i>';
            btn.title = "ऑटो व्हॉईस उत्तर बंद (Auto Speak Muted)";
            stopAllAudio();
        }
    }
}

function cleanTextForSpeech(rawText) {
    if (!rawText) return '';
    return rawText
        .replace(/[*#_~`\[\]()>+\-•]/g, ' ')
        .replace(/https?:\/\/\S+/g, '')
        .replace(/\s+/g, ' ')
        .trim();
}

// Finds best available Marathi or Indian voice in milliseconds
function getBestVoice(lang) {
    const voices = systemVoices.length ? systemVoices : (('speechSynthesis' in window) ? window.speechSynthesis.getVoices() : []);
    if (!voices || voices.length === 0) return null;

    // 1. Direct Marathi voice (e.g., Google मराठी, Microsoft Hemant/Kalpana)
    if (lang === 'mr') {
        const marathiVoice = voices.find(v => 
            (v.lang && (v.lang.toLowerCase().startsWith('mr') || v.lang.toLowerCase().includes('mr-in'))) ||
            (v.name && (v.name.toLowerCase().includes('marathi') || v.name.includes('मराठी')))
        );
        if (marathiVoice) return marathiVoice;
    }

    // 2. Hindi Indian voice (native Devanagari pronunciation, loud & clear)
    if (lang === 'mr' || lang === 'hi') {
        const hindiVoice = voices.find(v => 
            (v.lang && (v.lang.toLowerCase().startsWith('hi') || v.lang.toLowerCase().includes('hi-in'))) ||
            (v.name && (v.name.toLowerCase().includes('hindi') || v.name.includes('हिन्दी')))
        );
        if (hindiVoice) return hindiVoice;
    }

    // 3. Any Indian accent voice
    const indianVoice = voices.find(v => v.lang && v.lang.toLowerCase().includes('-in'));
    if (indianVoice) return indianVoice;

    // 4. Default voice
    return voices.find(v => v.default) || voices[0];
}

function speakText(rawText, buttonEl) {
    stopAllAudio();

    const cleanText = cleanTextForSpeech(rawText);
    if (!cleanText) return;

    if (buttonEl) {
        setSpeakingButtonActive(buttonEl);
    }

    const lang = currentLanguage || 'mr';

    // FAST-PATH: Native Browser SpeechSynthesis starts in 10-20 MILLISECONDS!
    if ('speechSynthesis' in window) {
        try {
            window.speechSynthesis.cancel();

            // Split into sentences so browser starts audio in 10ms and never stalls on long text
            const sentences = cleanText.match(/[^.!?।\n]+[.!?।\n]*/g) || [cleanText];
            speechQueue = sentences.map(s => s.trim()).filter(s => s.length > 0);

            if (speechQueue.length > 0) {
                isSpeakingQueue = true;
                playNextSentence(lang);
                return;
            }
        } catch (e) {
            console.warn('Browser SpeechSynthesis error, using backup:', e);
        }
    }

    // BACKUP: Network audio via /api/tts (gTTS) if browser synthesis is missing
    fallbackNetworkTTS(cleanText, lang);
}

function playNextSentence(lang) {
    if (!isSpeakingQueue || speechQueue.length === 0) {
        isSpeakingQueue = false;
        resetSpeakingButton();
        return;
    }

    const sentence = speechQueue.shift();
    const utterance = new SpeechSynthesisUtterance(sentence);
    utterance.volume = 1.0; // 100% MAXIMUM LOUDNESS for farmers
    utterance.rate = 1.0;   // Fast, natural conversational pace
    utterance.pitch = 1.0;

    const langTag = lang === 'mr' ? 'mr-IN' : (lang === 'hi' ? 'hi-IN' : 'en-IN');
    utterance.lang = langTag;

    const voice = getBestVoice(lang);
    if (voice) {
        utterance.voice = voice;
    }

    utterance.onend = () => {
        if (isSpeakingQueue) {
            playNextSentence(lang);
        }
    };

    utterance.onerror = (e) => {
        console.warn('Utterance error:', e);
        if (isSpeakingQueue) {
            playNextSentence(lang);
        }
    };

    // Starts playing in ~15 milliseconds!
    window.speechSynthesis.speak(utterance);
}

function fallbackNetworkTTS(cleanText, lang) {
    const audioUrl = `/api/tts?lang=${encodeURIComponent(lang)}&text=${encodeURIComponent(cleanText.substring(0, 800))}`;
    const audio = new Audio(audioUrl);
    audio.volume = 1.0;
    currentAudio = audio;

    audio.onended = () => {
        currentAudio = null;
        resetSpeakingButton();
    };

    audio.onerror = () => {
        currentAudio = null;
        resetSpeakingButton();
    };

    audio.play().catch(err => {
        console.warn('Audio play error:', err);
        resetSpeakingButton();
    });
}

function toggleSpeechPlayback(text, buttonEl) {
    // If already playing from this button, stop it
    if ((currentAudio && !currentAudio.paused && activeSpeakingBtn === buttonEl) ||
        (window.speechSynthesis && window.speechSynthesis.speaking && activeSpeakingBtn === buttonEl)) {
        stopAllAudio();
        return;
    }

    speakText(text, buttonEl);
}

function setSpeakingButtonActive(buttonEl) {
    resetSpeakingButton();
    activeSpeakingBtn = buttonEl;
    const dict = translations[currentLanguage] || translations['mr'];
    buttonEl.classList.add('speaking');
    const textSpan = buttonEl.querySelector('.listen-text');
    if (textSpan) textSpan.textContent = dict.stop_listen_btn || 'थांबवा (Stop)';
    const icon = buttonEl.querySelector('i');
    if (icon) icon.className = 'fa-solid fa-stop';
}

function resetSpeakingButton() {
    if (activeSpeakingBtn) {
        const dict = translations[currentLanguage] || translations['mr'];
        activeSpeakingBtn.classList.remove('speaking');
        const textSpan = activeSpeakingBtn.querySelector('.listen-text');
        if (textSpan) textSpan.textContent = dict.listen_btn || 'ऐका (Listen)';
        const icon = activeSpeakingBtn.querySelector('i');
        if (icon) icon.className = 'fa-solid fa-volume-high';
        activeSpeakingBtn = null;
    }
}

// =========================================================
// UTILITY FUNCTIONS
// =========================================================
function copyText(text, btn) {
    const dict = translations[currentLanguage] || translations['mr'];
    navigator.clipboard.writeText(text).then(() => {
        const span = btn.querySelector('span');
        const originalText = span.textContent;
        span.textContent = dict.copied;
        setTimeout(() => {
            span.textContent = originalText;
        }, 2000);
    });
}

function clearCurrentChat() {
    const container = document.getElementById('chatMessages');
    const hero = document.getElementById('welcomeHero');
    container.innerHTML = '';
    if (hero) {
        hero.style.display = 'block';
        container.appendChild(hero);
    }
    stopAllAudio();
}

function startNewChat() {
    clearCurrentChat();
    // In mobile, close sidebar
    toggleSidebar(false);
}

function selectSession(sessionId, el) {
    document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
    if (el) el.classList.add('active');
    // Preload query or clear chat for new thread
    clearCurrentChat();
    toggleSidebar(false);
}

function toggleSidebar(forceState) {
    const sidebar = document.getElementById('chatSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (!sidebar || !overlay) return;

    if (typeof forceState === 'boolean') {
        if (forceState) {
            sidebar.classList.add('open');
            overlay.classList.add('open');
        } else {
            sidebar.classList.remove('open');
            overlay.classList.remove('open');
        }
    } else {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
    }
}

function triggerPhotoUpload() {
    const input = document.getElementById('cropPhotoInput');
    if (input) input.click();
}

function handlePhotoSelected(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        // Placeholder for future crop disease diagnosis step
        sendMessage(`[पिकाचा फोटो जोडला: ${file.name}] कृपया या पिकावरील कीड किंवा रोग तपासून उपाय सांगा.`);
        input.value = '';
    }
}
