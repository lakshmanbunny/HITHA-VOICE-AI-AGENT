from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types

from app.config.settings import settings
from app.modules.llm.base import BaseLLMAdapter
from app.modules.llm.prompts import (
    SYSTEM_PROMPT,
    VALID_BOOKING_KEYS,
    VALID_INTENTS,
    build_user_message,
)

logger = logging.getLogger(__name__)

_REQUIRED_TOP_KEYS = frozenset({"intent", "language", "booking", "confirmed", "escalate"})


class ExtractionValidationError(Exception):
    """Raised when Gemini output fails strict contract validation."""


class GeminiAdapter(BaseLLMAdapter):
    """Async adapter for Google Gemini (google-genai SDK) with strict JSON output."""

    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def extract_structured(
        self,
        transcript: str,
        current_state: dict,
        language: str,
    ) -> dict:
        user_message = build_user_message(current_state, transcript)

        response = await self._client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        raw_text = response.text.strip()
        logger.debug("Gemini raw response: %s", raw_text)

        parsed = self._parse_json(raw_text)
        self._validate_structure(parsed)
        return parsed

    # -- validation ----------------------------------------------------------

    @staticmethod
    def _parse_json(text: str) -> dict:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ExtractionValidationError(
                f"Gemini returned invalid JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ExtractionValidationError(
                f"Expected JSON object, got {type(data).__name__}"
            )
        return data

    @staticmethod
    def _validate_structure(data: dict) -> None:
        top_keys = set(data.keys())

        missing = _REQUIRED_TOP_KEYS - top_keys
        if missing:
            raise ExtractionValidationError(
                f"Missing required top-level keys: {sorted(missing)}"
            )

        extra = top_keys - _REQUIRED_TOP_KEYS
        if extra:
            raise ExtractionValidationError(
                f"Unknown top-level keys: {sorted(extra)}"
            )

        if data["intent"] not in VALID_INTENTS:
            raise ExtractionValidationError(
                f"Invalid intent value: {data['intent']!r}. "
                f"Must be one of {sorted(VALID_INTENTS)}"
            )

        if not isinstance(data["language"], str) or not data["language"]:
            raise ExtractionValidationError(
                f"'language' must be a non-empty string, got {data['language']!r}"
            )

        if not isinstance(data["booking"], dict):
            raise ExtractionValidationError(
                f"'booking' must be a JSON object, got {type(data['booking']).__name__}"
            )

        booking_keys = set(data["booking"].keys())

        missing_bk = VALID_BOOKING_KEYS - booking_keys
        if missing_bk:
            for k in missing_bk:
                data["booking"][k] = None

        extra_bk = booking_keys - VALID_BOOKING_KEYS
        if extra_bk:
            logger.warning("Stripping unknown booking keys from LLM output: %s", sorted(extra_bk))
            for k in extra_bk:
                del data["booking"][k]

        if not isinstance(data["confirmed"], bool):
            raise ExtractionValidationError(
                f"'confirmed' must be boolean, got {type(data['confirmed']).__name__}"
            )

        if not isinstance(data["escalate"], bool):
            raise ExtractionValidationError(
                f"'escalate' must be boolean, got {type(data['escalate']).__name__}"
            )
