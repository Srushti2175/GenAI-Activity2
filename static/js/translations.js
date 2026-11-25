// =========================================================
// KRISHI SAKHI - MULTILINGUAL TRANSLATION DICTIONARY
// Supports: Marathi (mr), Hindi (hi), English (en)
// =========================================================

const translations = {
    mr: {
        app_name: "कृषी सखी",
        new_chat: "नवीन चर्चा (New Chat)",
        recent_queries: "अलीकडील प्रश्न",
        logout: "लॉगआउट",
        assistant_tagline: "शेतकरी मित्र व व्हॉईस सहाय्यक",
        listening: "कृषी सखी ऐकत आहे...",
        speak_now: "आपला शेतीविषयक प्रश्न बोला",
        input_placeholder: "येथे आपला शेतीचा प्रश्न विचारा... (किंवा माईक वापरा)",
        footer_note: "कृषी सखी AI शेतकरी सहाय्यक • बहुभाषिक मोफत सेवा",
        welcome_title: (name) => `राम-राम, ${name} जी!`,
        welcome_subtitle: "मी आपली <strong>कृषी सखी</strong> आहे. आपल्या पिकांची कीड, हवामान, खते किंवा सरकारी योजनांबद्दल कोणताही प्रश्न मराठी, हिंदी किंवा इंग्रजीत विचारा. आपण खालील मायक्रोफोन दाबून थेट <strong>बोलूनही</strong> विचारू शकता!",
        listen_btn: "ऐका (Listen)",
        stop_listen_btn: "थांबवा (Stop)",
        copy_btn: "कॉपी",
        copied: "कॉपी झाले!",
        chips: [
            { icon: "fa-bug", text: "सोयाबीन कीड निवारण सल्ला", query: "सोयाबीनवरील पाने खाणाऱ्या अळीसाठी सर्वोत्तम कीटकनाशक कोणते?" },
            { icon: "fa-cloud-sun-rain", text: "पुढील २ दिवसांचा हवामान अंदाज", query: "माझ्या परिसरातील पुढील २ दिवसांचा पावसाचा हवामान अंदाज सांगा" },
            { icon: "fa-landmark", text: "PM-KISAN हप्ता व पात्रता", query: "पीएम-किसान योजनेचा पुढील हप्ता कधी जमा होणार व पात्रता काय?" },
            { icon: "fa-flask", text: "कापूस खत व्यवस्थापन सल्ला", query: "कापूस पिकासाठी योग्य खत व्यवस्थापन आणि युरियाचे प्रमाण काय असावे?" }
        ]
    },
    hi: {
        app_name: "कृषि सखी",
        new_chat: "नई बातचीत (New Chat)",
        recent_queries: "हाल के प्रश्न",
        logout: "लॉगआउट",
        assistant_tagline: "किसान मित्र एवं वॉयस सहायक",
        listening: "कृषि सखी सुन रही है...",
        speak_now: "अपनी फसल या खेती से जुड़ा सवाल बोलें",
        input_placeholder: "यहाँ अपना कृषि प्रश्न पूछें... (या माइक का उपयोग करें)",
        footer_note: "कृषि सखी AI किसान सहायक • बहुभाषी निःशुल्क सेवा",
        welcome_title: (name) => `नमस्ते, ${name} जी!`,
        welcome_subtitle: "मैं आपकी <strong>कृषि सखी</strong> हूँ। अपनी फसलों में कीट, रोग, मौसम, उर्वरक या सरकारी योजनाओं के बारे में कोई भी प्रश्न पूछें। आप माइक दबाकर <strong>बोलकर भी</strong> पूछ सकते हैं!",
        listen_btn: "सुनें (Listen)",
        stop_listen_btn: "रोकें (Stop)",
        copy_btn: "कॉपी",
        copied: "कॉपी हुआ!",
        chips: [
            { icon: "fa-bug", text: "फसल कीट निवारण सलाह", query: "सोयाबीन और कपास में इल्ली और कीट नियंत्रण के लिए क्या उपाय करें?" },
            { icon: "fa-cloud-sun-rain", text: "अगले २ दिनों का मौसम पूर्वानुमान", query: "हमारे क्षेत्र में अगले २ दिन बारिश होगी या सूखा रहेगा?" },
            { icon: "fa-landmark", text: "पीएम-किसान सम्मान निधि स्थिति", query: "पीएम-किसान योजना की अगली किस्त के नियम और e-KYC की जानकारी दें" },
            { icon: "fa-flask", text: "उर्वरक एवं खाद प्रबंधन", query: "गेहूं और सरसों की फसल के लिए यूरिया और डीएपी का सही अनुपात क्या है?" }
        ]
    },
    en: {
        app_name: "Krishi Sakhi",
        new_chat: "New Chat",
        recent_queries: "Recent Chats",
        logout: "Logout",
        assistant_tagline: "Farmer Companion & Voice Assistant",
        listening: "Krishi Sakhi is listening...",
        speak_now: "Speak your farming query now",
        input_placeholder: "Ask your farming question here... (or use microphone)",
        footer_note: "Krishi Sakhi AI Farmer Assistant • Multilingual Free Tier Service",
        welcome_title: (name) => `Greetings, ${name}!`,
        welcome_subtitle: "I am your <strong>Krishi Sakhi</strong>. Ask me anything about crop pests, weather forecasts, fertilizers, or government welfare schemes in Marathi, Hindi, or English. You can also tap the mic and <strong>speak directly</strong>!",
        listen_btn: "Listen",
        stop_listen_btn: "Stop",
        copy_btn: "Copy",
        copied: "Copied!",
        chips: [
            { icon: "fa-bug", text: "Crop Pest Control Advice", query: "What is the best pesticide and biological control for caterpillars in soybean?" },
            { icon: "fa-cloud-sun-rain", text: "2-Day Weather & Rain Forecast", query: "What is the 48-hour rainfall forecast and agricultural weather advisory?" },
            { icon: "fa-landmark", text: "PM-KISAN Scheme Status", query: "What are the eligibility requirements and status for PM-Kisan installment?" },
            { icon: "fa-flask", text: "Cotton Fertilizer Management", query: "What is the recommended fertilizer schedule and urea dosage for cotton?" }
        ]
    }
};
