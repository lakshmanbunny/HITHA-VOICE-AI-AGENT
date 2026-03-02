from __future__ import annotations

TEMPLATES: dict[str, dict] = {
    "en": {
        "GREETING": "Hello, welcome to Hitha Hospital. How may I help you today?",
        "ASK_SLOT": {
            "department": "Which department would you like to book an appointment with?",
            "doctor": "Which doctor would you like to consult?",
            "preferred_date": "On which date would you prefer the appointment?",
            "preferred_time": "What time works best for you?",
            "patient_name": "May I have the patient's full name?",
        },
        "CONFIRM": "Do you confirm this appointment?",
        "FINALIZE_BOOKING": "Your appointment has been booked successfully.",
        "ESCALATE": "I am transferring your call to a human representative.",
        "CONTINUE": "Okay.",
    },
    "te": {
        "GREETING": "నమస్కారం, హితా హాస్పిటల్‌కు స్వాగతం. మీకు ఎలా సహాయం చేయగలను?",
        "ASK_SLOT": {
            "department": "మీరు ఏ విభాగంలో అపాయింట్‌మెంట్ బుక్ చేయాలనుకుంటున్నారు?",
            "doctor": "మీరు ఏ డాక్టర్‌ను సంప్రదించాలనుకుంటున్నారు?",
            "preferred_date": "మీకు ఏ తేదీన అపాయింట్‌మెంట్ కావాలి?",
            "preferred_time": "మీకు ఏ సమయం అనుకూలంగా ఉంటుంది?",
            "patient_name": "రోగి పూర్తి పేరు చెప్పగలరా?",
        },
        "CONFIRM": "మీరు ఈ అపాయింట్‌మెంట్‌ను నిర్ధారిస్తున్నారా?",
        "FINALIZE_BOOKING": "మీ అపాయింట్‌మెంట్ విజయవంతంగా బుక్ చేయబడింది.",
        "ESCALATE": "మీ కాల్‌ను మానవ ప్రతినిధికి బదిలీ చేస్తున్నాను.",
        "CONTINUE": "సరే.",
    },
    "hi": {
        "GREETING": "नमस्ते, हिता हॉस्पिटल में आपका स्वागत है। मैं आपकी कैसे सहायता कर सकता हूँ?",
        "ASK_SLOT": {
            "department": "आप किस विभाग में अपॉइंटमेंट बुक करना चाहेंगे?",
            "doctor": "आप किस डॉक्टर से परामर्श लेना चाहेंगे?",
            "preferred_date": "आपको किस तारीख को अपॉइंटमेंट चाहिए?",
            "preferred_time": "आपके लिए कौन सा समय सुविधाजनक रहेगा?",
            "patient_name": "कृपया मरीज़ का पूरा नाम बताएँ।",
        },
        "CONFIRM": "क्या आप इस अपॉइंटमेंट की पुष्टि करते हैं?",
        "FINALIZE_BOOKING": "आपकी अपॉइंटमेंट सफलतापूर्वक बुक कर दी गई है।",
        "ESCALATE": "मैं आपकी कॉल एक प्रतिनिधि को ट्रांसफ़र कर रहा हूँ।",
        "CONTINUE": "ठीक है।",
    },
}

FALLBACK_LANGUAGE = "en"
