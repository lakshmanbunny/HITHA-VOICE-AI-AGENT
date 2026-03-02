from __future__ import annotations

import asyncio
import base64
import json
import logging
from urllib.parse import urlencode

import websockets
from websockets.asyncio.client import ClientConnection

from app.config.settings import settings
from app.modules.tts.base import AudioCallback, BaseTTSAdapter

logger = logging.getLogger(__name__)

_LANG_MAP: dict[str, str] = {
    "en": "en-IN",
    "hi": "hi-IN",
    "te": "te-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "mr": "mr-IN",
    "od": "od-IN",
    "pa": "pa-IN",
    "ta": "ta-IN",
}

_FALLBACK_LANG = "en-IN"


class SarvamStreamingTTS(BaseTTSAdapter):
    """Production-grade Sarvam streaming TTS over a single persistent WebSocket.

    One connection per call lifecycle.
    Text is sent as JSON, audio chunks arrive as base64-encoded PCM linear16.
    Audio leaves via the registered callback only.
    """

    def __init__(
        self,
        *,
        speaker: str | None = None,
        sample_rate: int | None = None,
        pace: float = 1.0,
        min_buffer_size: int = 30,
    ) -> None:
        self._speaker = speaker or settings.SARVAM_TTS_SPEAKER
        self._sample_rate = sample_rate or settings.SARVAM_TTS_SAMPLE_RATE
        self._pace = pace
        self._min_buffer_size = min_buffer_size

        self._ws: ClientConnection | None = None
        self._receive_task: asyncio.Task | None = None
        self._audio_callback: AudioCallback | None = None
        self._running = False
        self._lock = asyncio.Lock()
        self._completion_event = asyncio.Event()
        self._current_language: str = _FALLBACK_LANG

    # -- public API ----------------------------------------------------------

    def set_audio_callback(self, callback: AudioCallback) -> None:
        self._audio_callback = callback

    async def start(self) -> None:
        if self._running:
            logger.warning("SarvamStreamingTTS already running, ignoring start()")
            return

        url = self._build_url()
        headers = {"Api-Subscription-Key": settings.SARVAM_API_KEY}

        logger.info("Connecting to Sarvam TTS: %s", url.split("?")[0])

        self._ws = await websockets.connect(
            url,
            additional_headers=headers,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=5,
        )
        self._running = True
        self._receive_task = asyncio.create_task(
            self._receive_loop(), name="sarvam-tts-recv"
        )

        await self._send_config(self._current_language)
        logger.info("Sarvam TTS connected and configured")

    async def speak(self, text: str, language: str) -> None:
        """Send text for synthesis and wait until all audio chunks are received.

        Guarded by a lock — concurrent speak() calls queue, never overlap.
        """
        if not self._running or self._ws is None:
            raise RuntimeError("TTS not running — call start() first")

        async with self._lock:
            bcp47 = _to_bcp47(language)

            if bcp47 != self._current_language:
                await self._send_config(bcp47)
                self._current_language = bcp47

            self._completion_event.clear()

            payload = json.dumps({
                "type": "text",
                "data": {"text": text},
            })
            await self._ws.send(payload)
            await self._ws.send(json.dumps({"type": "flush"}))

            logger.debug("TTS text sent (%d chars, lang=%s)", len(text), bcp47)

            try:
                await asyncio.wait_for(self._completion_event.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning("TTS completion event timed out after 30s")

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False

        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

        if self._receive_task is not None:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        logger.info("Sarvam TTS stopped")

    # -- internal ------------------------------------------------------------

    def _build_url(self) -> str:
        params: dict[str, str] = {
            "model": settings.SARVAM_TTS_MODEL,
            "send_completion_event": "true",
        }
        return f"{settings.SARVAM_TTS_WS_URL}?{urlencode(params)}"

    async def _send_config(self, language: str) -> None:
        assert self._ws is not None

        config = {
            "type": "config",
            "data": {
                "speaker": self._speaker,
                "target_language_code": language,
                "speech_sample_rate": str(self._sample_rate),
                "output_audio_codec": "linear16",
                "pace": self._pace,
                "min_buffer_size": self._min_buffer_size,
            },
        }
        await self._ws.send(json.dumps(config))
        logger.debug("TTS config sent: lang=%s speaker=%s", language, self._speaker)

    async def _receive_loop(self) -> None:
        assert self._ws is not None

        try:
            async for raw in self._ws:
                if not self._running:
                    break

                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    logger.error("Sarvam TTS: non-JSON message: %s", str(raw)[:200])
                    continue

                msg_type = msg.get("type")
                data = msg.get("data", {})

                if msg_type == "audio":
                    audio_b64 = data.get("audio", "")
                    if audio_b64 and self._audio_callback:
                        pcm_bytes = base64.b64decode(audio_b64)
                        await self._audio_callback(pcm_bytes)

                elif msg_type == "event":
                    event_type = data.get("event_type")
                    if event_type == "final":
                        logger.debug("TTS completion event received")
                        self._completion_event.set()

                elif msg_type == "error":
                    error_msg = data.get("message", "unknown")
                    error_code = data.get("code", "unknown")
                    logger.error(
                        "Sarvam TTS error: %s (code=%s)", error_msg, error_code
                    )
                    self._completion_event.set()
                    raise RuntimeError(
                        f"Sarvam TTS error: {error_msg} (code={error_code})"
                    )

                else:
                    logger.warning("Sarvam TTS: unknown message type: %s", msg_type)

        except websockets.ConnectionClosed as exc:
            if self._running:
                logger.warning("Sarvam TTS WS closed unexpectedly: %s", exc)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Sarvam TTS receive loop error")
        finally:
            self._running = False
            self._completion_event.set()


def _to_bcp47(language: str) -> str:
    lang = (language or "").strip().lower()
    if "-" in lang:
        lang = lang.split("-")[0]
    return _LANG_MAP.get(lang, _FALLBACK_LANG)
