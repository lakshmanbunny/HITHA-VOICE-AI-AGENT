import logging

from fastapi import APIRouter, Query
from livekit.api import AccessToken, CreateAgentDispatchRequest, LiveKitAPI, VideoGrants

from app.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Token"])


@router.get("/api/token")
async def get_token(
    room: str = Query(..., min_length=1, description="LiveKit room name"),
    identity: str = Query(..., min_length=1, description="Participant identity"),
) -> dict:
    token = (
        AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_grants(VideoGrants(room_join=True, room=room, room_create=True))
        .to_jwt()
    )

    async with LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    ) as api:
        await api.agent_dispatch.create_dispatch(
            CreateAgentDispatchRequest(
                room=room,
                agent_name="hitha-voice-agent",
            )
        )
    logger.info("Agent dispatched to room=%s for identity=%s", room, identity)

    return {"token": token, "url": settings.LIVEKIT_URL}
