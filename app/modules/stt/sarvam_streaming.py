from __future__ import annotations

import asyncio
import base64
import json
import logging
from urllib.parse import urlencode

import websockets
from websockets.asyncio.client import ClientConnection

from app.config.settings import settings
from app.modules.stt.base import BaseSTTAdapter, TranscriptCallback

logger = logging.getLogger(__name__)


class SarvamStreamingSTT(BaseSTTAdapter):
    """Production-grade Sarvam streaming STT over WebSocket.

    One WebSocket connection per call lifecycle.
    Audio is base64-encoded and sent as JSON frames.
    Transcripts arrive via the registered callback.
    """

    def __init__(
        self,
        *,
        language: str | None = None,
        mode: str | None = None,
        sample_rate: int | None = None,
    ) -> None:
        self._language = language or settings.SARVAM_STT_LANGUAGE
        self._mode = mode or settings.SARVAM_STT_MODE
        self._sample_rate = sample_rate or settings.SARVAM_STT_SAMPLE_RATE

        self._ws: ClientConnection | None = None
        self._receive_task: asyncio.Task | None = None
        self._callback: TranscriptCallback | None = None
        self._running = False
        self._lock = asyncio.Lock()

    # -- public API ----------------------------------------------------------

    def set_transcript_callback(self, callback: TranscriptCallback) -> None:
        self._callback = callback

    async def start(self) -> None:
        if self._running:
            logger.warning("SarvamStreamingSTT already running, ignoring start()")
            return

        url = self._build_url()
        headers = {"Api-Subscription-Key": settings.SARVAM_API_KEY}

        logger.info("Connecting to Sarvam STT: %s", url.split("?")[0])

        self._ws = await websockets.connect(
            url,
            additional_headers=headers,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=5,
        )
        self._running = True
        self._receive_task = asyncio.create_task(
            self._receive_loop(), name="sarvam-stt-recv"
        )
        logger.info("Sarvam STT connected and receiving")

    async def send_audio(self, chunk: bytes) -> None:
        if not self._running or self._ws is None:
            return

        payload = json.dumps({
            "audio": {
                "data": base64.b64encode(chunk).decode("ascii"),
                "sample_rate": str(self._sample_rate),
                "encoding": "audio/wav",
            }
        })

        async with self._lock:
            try:
                await self._ws.send(payload)
            except websockets.ConnectionClosed:
                logger.warning("Sarvam WS closed while sending audio")
                self._running = False

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False

        if self._ws is not None:
            try:
                await self._ws.send(json.dumps({"type": "flush"}))
            except Exception:
                pass

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

        logger.info("Sarvam STT stopped")

    # -- internal ------------------------------------------------------------

    def _build_url(self) -> str:
        params: dict[str, str] = {
            "model": settings.SARVAM_STT_MODEL,
            "mode": self._mode,
            "language-code": self._language,
            "sample_rate": str(self._sample_rate),
            "input_audio_codec": "pcm_s16le",
            "high_vad_sensitivity": "true",
            "vad_signals": "true",
            "flush_signal": "true",
        }
        return f"{settings.SARVAM_STT_WS_URL}?{urlencode(params)}"

    async def _receive_loop(self) -> None:
        assert self._ws is not None

        try:
            async for raw in self._ws:
                if not self._running:
                    break

                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    logger.error("Sarvam STT: non-JSON message: %s", str(raw)[:200])
                    continue

                msg_type = msg.get("type")
                data = msg.get("data", {})

                if msg_type == "data":
                    transcript = data.get("transcript", "").strip()
                    lang = data.get("language_code")
                    if transcript and self._callback:
                        logger.debug("Sarvam transcript: [%s] %s", lang, transcript[:120])
                        await self._callback(transcript, True)

                elif msg_type == "events":
                    signal = data.get("signal_type")
                    logger.debug("Sarvam VAD event: %s", signal)

                elif msg_type == "error":
                    logger.error("Sarvam STT raw error: %s", msg)
                    error_msg = data.get("message") or data.get("error", "unknown")
                    error_code = data.get("code", "unknown")
                    logger.error(
                        "Sarvam STT error: %s (code=%s)", error_msg, error_code
                    )
                    raise RuntimeError(
                        f"Sarvam STT error: {error_msg} (code={error_code})"
                    )

                else:
                    logger.warning("Sarvam STT: unknown message type=%s raw=%s", msg_type, str(msg)[:300])

        except websockets.ConnectionClosed as exc:
            if self._running:
                logger.warning("Sarvam WS closed unexpectedly: %s", exc)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Sarvam STT receive loop error")
        finally:
            self._running = False
