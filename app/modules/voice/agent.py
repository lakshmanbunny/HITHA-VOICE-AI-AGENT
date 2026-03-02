"""LiveKit Agent with full STT → Engine → TTS pipeline.

Run as a standalone process:

    python -m app.modules.voice.agent dev

Audio pipeline:
    Inbound:  LiveKit AudioStream (16 kHz mono) → SarvamSTT → VoiceSession → Engine
    Outbound: Engine action → ResponseGenerator → SarvamTTS → AudioSource → LiveKit
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid

from dotenv import load_dotenv

load_dotenv()

import logging.handlers

_LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent.log")
_file_handler = logging.handlers.RotatingFileHandler(
    os.path.abspath(_LOG_FILE), maxBytes=2_000_000, backupCount=2,
)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
)
logging.root.addHandler(_file_handler)
logging.root.setLevel(logging.DEBUG)

from livekit import agents, rtc
from livekit.agents import AutoSubscribe, JobContext

from app.modules.conversation.engine import ConversationEngine
from app.modules.conversation.service import ConversationService
from app.modules.dashboard.service import DashboardService
from app.modules.database.session import async_session_factory
from app.modules.llm.gemini_adapter import GeminiAdapter
from app.modules.response.generator import ResponseGenerator
from app.modules.stt.sarvam_streaming import SarvamStreamingSTT
from app.modules.tts.sarvam_streaming import SarvamStreamingTTS
from app.modules.voice.voice_session import VoiceSession

logger = logging.getLogger(__name__)

server = agents.AgentServer()

_AUDIO_SAMPLE_RATE = 16_000
_AUDIO_NUM_CHANNELS = 1
_TTS_PING_INTERVAL = 30


# ── Helper coroutines ────────────────────────────────────────────────────


async def _feed_audio(
    track: rtc.Track,
    stt: SarvamStreamingSTT,
    call_id: str,
) -> None:
    """Stream 16 kHz mono PCM from a LiveKit audio track into the STT adapter."""
    audio_stream = rtc.AudioStream(
        track,
        sample_rate=_AUDIO_SAMPLE_RATE,
        num_channels=_AUDIO_NUM_CHANNELS,
    )
    frame_count = 0
    try:
        async for event in audio_stream:
            if not stt._running:
                break
            await stt.send_audio(bytes(event.frame.data))
            frame_count += 1
            if frame_count == 1:
                logger.info("[%s] First audio frame sent to STT", call_id)
            if frame_count % 500 == 0:
                logger.debug("[%s] Audio frames sent to STT: %d", call_id, frame_count)
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("[%s] Audio feed error", call_id)
    finally:
        await audio_stream.aclose()
        logger.info("[%s] Audio feed stopped (total frames: %d)", call_id, frame_count)


async def _safe_speak(
    tts: SarvamStreamingTTS,
    text: str,
    language: str,
    call_id: str,
) -> None:
    """Fire-and-forget wrapper for TTS speak with error logging."""
    try:
        await tts.speak(text, language)
    except Exception:
        logger.exception("[%s] TTS speak failed", call_id)


async def _tts_keepalive(tts: SarvamStreamingTTS, done: asyncio.Event) -> None:
    """Send periodic pings to prevent Sarvam TTS 408 timeout."""
    try:
        while not done.is_set() and tts._running and tts._ws is not None:
            await asyncio.sleep(_TTS_PING_INTERVAL)
            if not tts._running or tts._ws is None:
                break
            try:
                import json
                await tts._ws.send(json.dumps({"type": "ping"}))
                logger.debug("TTS keepalive ping sent")
            except Exception:
                break
    except asyncio.CancelledError:
        pass


# ── Agent entrypoint ──────────────────────────────────────────────────────


@server.rtc_session(agent_name="hitha-voice-agent")
async def entrypoint(ctx: JobContext) -> None:
    logger.info("Job started — room=%s", ctx.room.name)

    call_id = str(uuid.uuid4())
    room_id = ctx.room.name
    done = asyncio.Event()
    audio_feed_task: asyncio.Task | None = None
    stt: SarvamStreamingSTT | None = None

    # ── Register event handlers BEFORE connecting ─────────────────
    # This prevents the race condition where tracks are subscribed
    # before handlers are registered.

    def _start_audio_feed(
        track: rtc.Track,
        remote_participant: rtc.RemoteParticipant,
    ) -> None:
        nonlocal audio_feed_task

        if track.kind != rtc.TrackKind.KIND_AUDIO:
            return

        if audio_feed_task is not None and not audio_feed_task.done():
            logger.warning(
                "[%s] Audio feed already running, ignoring extra track",
                call_id,
            )
            return

        if stt is None:
            logger.warning("[%s] STT not ready yet, deferring track", call_id)
            return

        logger.info(
            "[%s] Audio track subscribed — starting feed (participant=%s)",
            call_id, remote_participant.identity,
        )
        audio_feed_task = asyncio.create_task(
            _feed_audio(track, stt, call_id),
            name=f"audio-feed-{call_id}",
        )

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        remote_participant: rtc.RemoteParticipant,
    ) -> None:
        _start_audio_feed(track, remote_participant)

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(
        remote_participant: rtc.RemoteParticipant,
    ) -> None:
        logger.info(
            "[%s] Participant disconnected — identity=%s",
            call_id, remote_participant.identity,
        )
        done.set()

    @ctx.room.on("disconnected")
    def on_disconnected() -> None:
        logger.info("[%s] Room disconnected", call_id)
        done.set()

    async def shutdown_hook() -> None:
        logger.info("[%s] Session ending, cleaning up", call_id)
        done.set()

    ctx.add_shutdown_callback(shutdown_hook)

    # ── Connect and wait for participant ──────────────────────────
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info(
        "Participant joined — identity=%s room=%s",
        participant.identity, ctx.room.name,
    )

    async with async_session_factory() as session:
        svc = ConversationService(session)
        dash_svc = DashboardService(session)
        adapter = GeminiAdapter()
        engine = ConversationEngine(svc, adapter)
        response_gen = ResponseGenerator()

        await svc.create_new_call(
            call_id=call_id,
            language="en",
            livekit_room_id=room_id,
        )
        await dash_svc.create_call_log(
            call_id=call_id,
            caller_name=participant.identity or "Unknown",
            direction="inbound",
        )
        logger.info(
            "Conversation + call log created — call_id=%s room_id=%s",
            call_id, room_id,
        )
        appointment_id: str | None = None

        voice_session = VoiceSession(
            call_id=call_id,
            room_id=room_id,
            engine=engine,
        )

        # ── Audio output: AudioSource → LocalTrack → Room ─────────
        audio_source = rtc.AudioSource(
            sample_rate=_AUDIO_SAMPLE_RATE,
            num_channels=_AUDIO_NUM_CHANNELS,
        )
        local_track = rtc.LocalAudioTrack.create_audio_track(
            "assistant-voice", audio_source,
        )
        publish_options = rtc.TrackPublishOptions(
            source=rtc.TrackSource.SOURCE_MICROPHONE,
        )
        await ctx.room.local_participant.publish_track(
            local_track, publish_options,
        )
        logger.info("[%s] Audio output track published", call_id)

        # ── TTS setup ─────────────────────────────────────────────
        tts = SarvamStreamingTTS()

        _audio_chunk_count = 0

        async def on_audio_chunk(pcm: bytes) -> None:
            nonlocal _audio_chunk_count
            samples_per_channel = len(pcm) // (2 * _AUDIO_NUM_CHANNELS)
            if samples_per_channel == 0:
                return
            frame = rtc.AudioFrame(
                data=pcm,
                sample_rate=_AUDIO_SAMPLE_RATE,
                num_channels=_AUDIO_NUM_CHANNELS,
                samples_per_channel=samples_per_channel,
            )
            await audio_source.capture_frame(frame)
            _audio_chunk_count += 1
            if _audio_chunk_count == 1:
                logger.info("[%s] First TTS audio chunk captured (%d bytes)", call_id, len(pcm))
            if _audio_chunk_count % 20 == 0:
                logger.debug("[%s] TTS audio chunks captured: %d", call_id, _audio_chunk_count)

        tts.set_audio_callback(on_audio_chunk)

        try:
            await tts.start()
        except Exception:
            logger.exception("[%s] TTS failed to start, escalating", call_id)
            await svc.mark_escalated(call_id)
            return

        # ── STT setup ─────────────────────────────────────────────
        stt_instance = SarvamStreamingSTT()
        stt = stt_instance

        async def on_transcript(text: str, is_final: bool) -> None:
            nonlocal appointment_id
            action = await voice_session.handle_transcript(text, is_final=is_final)
            if not action:
                return

            state = await svc.load_state(call_id)
            lang = state.language if state else "en"
            response_text = response_gen.generate(action, lang)

            voice_session.add_assistant_turn(response_text)

            logger.info(
                "[%s] Response (%s): %s", call_id, lang, response_text[:120],
            )

            if action.get("action") == "FINALIZE_BOOKING" and state:
                try:
                    booking = state.booking.model_dump()
                    apt = await dash_svc.create_appointment_from_booking(
                        call_id=call_id,
                        booking_data=booking,
                    )
                    appointment_id = apt.id
                    logger.info(
                        "[%s] Appointment auto-created: %s", call_id, apt.id,
                    )
                except Exception:
                    logger.exception("[%s] Failed to auto-create appointment", call_id)

            asyncio.create_task(
                _safe_speak(tts, response_text, lang, call_id),
                name=f"tts-speak-{call_id}",
            )

        stt.set_transcript_callback(on_transcript)

        try:
            await stt.start()
        except Exception:
            logger.exception("[%s] STT failed to start, escalating", call_id)
            await tts.stop()
            await svc.mark_escalated(call_id)
            return

        # ── Scan for already-subscribed tracks (race condition fix) ─
        for rp in ctx.room.remote_participants.values():
            for pub in rp.track_publications.values():
                if pub.track and pub.subscribed and pub.track.kind == rtc.TrackKind.KIND_AUDIO:
                    logger.info(
                        "[%s] Found pre-existing audio track from %s, starting feed",
                        call_id, rp.identity,
                    )
                    _start_audio_feed(pub.track, rp)

        # ── Health monitors ───────────────────────────────────────
        async def _monitor_stt() -> None:
            if stt._receive_task is None:
                return
            try:
                await stt._receive_task
            except asyncio.CancelledError:
                return

            if not done.is_set():
                logger.error(
                    "[%s] STT connection died mid-call, escalating", call_id,
                )
                try:
                    await svc.mark_escalated(call_id)
                except Exception:
                    logger.exception(
                        "[%s] Failed to escalate after STT death", call_id,
                    )
                done.set()

        stt_monitor = asyncio.create_task(
            _monitor_stt(), name=f"stt-monitor-{call_id}",
        )

        async def _monitor_tts() -> None:
            if tts._receive_task is None:
                return
            try:
                await tts._receive_task
            except asyncio.CancelledError:
                return

            if not done.is_set():
                logger.error(
                    "[%s] TTS connection died mid-call, escalating", call_id,
                )
                try:
                    await svc.mark_escalated(call_id)
                except Exception:
                    logger.exception(
                        "[%s] Failed to escalate after TTS death", call_id,
                    )
                done.set()

        tts_monitor = asyncio.create_task(
            _monitor_tts(), name=f"tts-monitor-{call_id}",
        )

        # ── TTS keepalive ─────────────────────────────────────────
        keepalive_task = asyncio.create_task(
            _tts_keepalive(tts, done), name=f"tts-keepalive-{call_id}",
        )

        logger.info(
            "[%s] Full pipeline ready — STT → Engine → TTS", call_id,
        )

        # ── Initial greeting ──────────────────────────────────────
        greeting = response_gen.generate({"action": "GREETING"}, "en")
        voice_session.add_assistant_turn(greeting)
        logger.info("[%s] Greeting: %s", call_id, greeting[:120])
        asyncio.create_task(
            _safe_speak(tts, greeting, "en", call_id),
            name=f"tts-greeting-{call_id}",
        )

        # ── Idle until session ends ───────────────────────────────
        await done.wait()

        # ── Cleanup (order matters: TTS → STT → feed → monitors) ─
        await tts.stop()
        await stt.stop()

        if audio_feed_task is not None and not audio_feed_task.done():
            audio_feed_task.cancel()
            try:
                await audio_feed_task
            except asyncio.CancelledError:
                pass

        for task in (stt_monitor, tts_monitor, keepalive_task):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # ── Finalize call log ─────────────────────────────────────
        try:
            final_state = await svc.load_state(call_id)
            status = "completed"
            if final_state and final_state.escalated:
                status = "transferred"

            caller_name = None
            languages = None
            if final_state:
                bd = final_state.booking.model_dump()
                if bd.get("patient_name"):
                    caller_name = bd["patient_name"]
                lang_code = final_state.language or "en"
                languages = [DashboardService.language_display(lang_code)]

            await dash_svc.finalize_call_log(
                call_id=call_id,
                transcript=voice_session.get_transcript(),
                status=status,
                caller_name=caller_name,
                languages=languages,
                appointment_id=appointment_id,
            )
            logger.info("[%s] Call log finalized (status=%s)", call_id, status)
        except Exception:
            logger.exception("[%s] Failed to finalize call log", call_id)

    logger.info("[%s] Job complete", call_id)


def run_agent() -> None:
    """Entry point called from ``python -m app.modules.voice.agent``."""
    agents.cli.run_app(server)


if __name__ == "__main__":
    run_agent()
