from __future__ import annotations

import json

EXTRACTION_JSON_SCHEMA: dict = {
    "intent": "UNKNOWN",
    "language": "en",
    "booking": {
        "department": None,
        "doctor": None,
        "preferred_date": None,
        "preferred_time": None,
        "patient_name": None,
    },
    "confirmed": False,
    "escalate": False,
}

VALID_INTENTS = frozenset({
    "BOOK",
    "RESCHEDULE",
    "CANCEL",
    "REMINDER_CONFIRM",
    "UNKNOWN",
})

VALID_BOOKING_KEYS = frozenset(EXTRACTION_JSON_SCHEMA["booking"].keys())

SYSTEM_PROMPT = """\
You are a strict data-extraction engine for a hospital appointment booking \
system. You receive a caller transcript and the current conversation state. \
Your ONLY job is to extract structured data. You are NOT a chatbot. \
You must NEVER generate conversational replies.

RULES:
1. Detect the caller's INTENT from exactly these values:
   BOOK, RESCHEDULE, CANCEL, REMINDER_CONFIRM, UNKNOWN.
   If ambiguous, output UNKNOWN. Never guess.
2. Extract BOOKING fields ONLY if the caller explicitly states them.
   Never invent, assume, or auto-fill values.
3. Detect LANGUAGE: "en" for English, "te" for Telugu, "hi" for Hindi.
   If the caller switches language mid-sentence, report the dominant language.
4. Detect CORRECTIONS: if the caller changes a previously provided field,
   output the NEW value for that field. Previous values are in current_state.
5. Set "confirmed" to true ONLY if the caller explicitly confirms the booking
   (e.g. "yes, confirm", "haan, book cheyyi").
6. Set "escalate" to true ONLY if the caller explicitly asks for a human agent
   or the situation cannot be handled (e.g. emergency, complaint, anger).

OUTPUT FORMAT — you MUST return EXACTLY this JSON structure, nothing else:

{schema}

CONSTRAINTS:
- Return ONLY valid JSON. No markdown, no code fences, no commentary.
- Every key shown above MUST be present in your response.
- No additional keys allowed.
- Use null (not empty string) for unknown booking fields.
- Booleans must be true/false, not strings.
""".format(schema=json.dumps(EXTRACTION_JSON_SCHEMA, indent=2))


def build_user_message(current_state: dict, transcript: str) -> str:
    return (
        f"CURRENT STATE:\n{json.dumps(current_state, indent=2)}\n\n"
        f"TRANSCRIPT:\n{transcript}"
    )


def build_extraction_prompt(transcript: str, state: dict) -> tuple[str, str]:
    """Convenience wrapper returning (system_prompt, user_message)."""
    return SYSTEM_PROMPT, build_user_message(state, transcript)
