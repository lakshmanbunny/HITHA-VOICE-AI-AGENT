from __future__ import annotations

from app.modules.response.templates import FALLBACK_LANGUAGE, TEMPLATES


class ResponseGenerator:
    """Deterministic response mapper.

    Pure lookup — no LLM, no DB, no randomness.
    Maps an engine action dict + language to a fixed response string.
    Supports dynamic content for time-slot presentation and booking confirmation.
    """

    def generate(self, action: dict, language: str) -> str:
        language = (language or "").strip().lower()
        if "-" in language:
            language = language.split("-")[0]

        lang_templates = TEMPLATES.get(language) or TEMPLATES[FALLBACK_LANGUAGE]
        fallback = TEMPLATES[FALLBACK_LANGUAGE]
        action_type: str = action.get("action", "")

        if action_type == "GREETING":
            return lang_templates.get("GREETING", fallback["GREETING"])

        if action_type == "ASK_SLOT":
            slot: str = action.get("slot", "")

            if slot == "preferred_time":
                available_slots = action.get("available_slots")
                if available_slots:
                    return self._build_slot_response(
                        available_slots, language, lang_templates, fallback,
                    )

            slot_templates = lang_templates.get("ASK_SLOT", {})
            text = slot_templates.get(slot)
            if text is not None:
                return text
            return fallback["ASK_SLOT"].get(slot, fallback["CONTINUE"])

        if action_type == "CONFIRM":
            booking = action.get("booking", {})
            return self._build_confirm_response(
                booking, language, lang_templates, fallback,
            )

        if action_type == "FINALIZE_BOOKING":
            return lang_templates.get("FINALIZE_BOOKING", fallback["FINALIZE_BOOKING"])

        if action_type == "ESCALATE":
            return lang_templates.get("ESCALATE", fallback["ESCALATE"])

        return lang_templates.get("CONTINUE", fallback["CONTINUE"])

    @staticmethod
    def _build_slot_response(
        slots: list[str],
        language: str,
        lang_templates: dict,
        fallback: dict,
    ) -> str:
        slot_list = ", ".join(slots[:6])

        if language == "te":
            return (
                f"ఈ సమయాలు అందుబాటులో ఉన్నాయి: {slot_list}. "
                "మీకు ఏ సమయం అనుకూలంగా ఉంటుంది?"
            )
        if language == "hi":
            return (
                f"ये समय उपलब्ध हैं: {slot_list}. "
                "आपके लिए कौन सा समय सुविधाजनक रहेगा?"
            )
        return (
            f"The following slots are available: {slot_list}. "
            "Which time works best for you?"
        )

    @staticmethod
    def _build_confirm_response(
        booking: dict,
        language: str,
        lang_templates: dict,
        fallback: dict,
    ) -> str:
        if not booking:
            return lang_templates.get("CONFIRM", fallback["CONFIRM"])

        dept = booking.get("department", "")
        doctor = booking.get("doctor", "")
        date = booking.get("preferred_date", "")
        time = booking.get("preferred_time", "")
        name = booking.get("patient_name", "")

        if language == "te":
            parts = []
            if name:
                parts.append(f"రోగి: {name}")
            if dept:
                parts.append(f"విభాగం: {dept}")
            if doctor:
                parts.append(f"డాక్టర్: {doctor}")
            if date:
                parts.append(f"తేదీ: {date}")
            if time:
                parts.append(f"సమయం: {time}")
            summary = ", ".join(parts)
            return f"మీ అపాయింట్‌మెంట్ వివరాలు: {summary}. మీరు నిర్ధారిస్తున్నారా?"

        if language == "hi":
            parts = []
            if name:
                parts.append(f"मरीज़: {name}")
            if dept:
                parts.append(f"विभाग: {dept}")
            if doctor:
                parts.append(f"डॉक्टर: {doctor}")
            if date:
                parts.append(f"तारीख: {date}")
            if time:
                parts.append(f"समय: {time}")
            summary = ", ".join(parts)
            return f"आपकी अपॉइंटमेंट का विवरण: {summary}. क्या आप पुष्टि करते हैं?"

        parts = []
        if name:
            parts.append(f"Patient: {name}")
        if dept:
            parts.append(f"Department: {dept}")
        if doctor:
            parts.append(f"Doctor: {doctor}")
        if date:
            parts.append(f"Date: {date}")
        if time:
            parts.append(f"Time: {time}")
        summary = ", ".join(parts)
        return f"Your appointment details: {summary}. Do you confirm?"
