from __future__ import annotations

from app.modules.response.templates import FALLBACK_LANGUAGE, TEMPLATES


class ResponseGenerator:
    """Deterministic response mapper.

    Pure lookup — no LLM, no DB, no randomness.
    Maps an engine action dict + language to a fixed response string.
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
            slot_templates = lang_templates.get("ASK_SLOT", {})
            text = slot_templates.get(slot)
            if text is not None:
                return text
            return fallback["ASK_SLOT"].get(slot, fallback["CONTINUE"])

        if action_type == "CONFIRM":
            return lang_templates.get("CONFIRM", fallback["CONFIRM"])

        if action_type == "FINALIZE_BOOKING":
            return lang_templates.get("FINALIZE_BOOKING", fallback["FINALIZE_BOOKING"])

        if action_type == "ESCALATE":
            return lang_templates.get("ESCALATE", fallback["ESCALATE"])

        return lang_templates.get("CONTINUE", fallback["CONTINUE"])
