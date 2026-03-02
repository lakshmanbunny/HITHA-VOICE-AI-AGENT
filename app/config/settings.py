from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    APP_NAME: str = "Hitha Voice AI"
    DATABASE_URL: str = "sqlite+aiosqlite:///./hitha.db"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"

    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    SARVAM_API_KEY: str = ""
    SARVAM_STT_WS_URL: str = "wss://api.sarvam.ai/speech-to-text/ws"
    SARVAM_STT_MODEL: str = "saaras:v3"
    SARVAM_STT_LANGUAGE: str = "unknown"
    SARVAM_STT_MODE: str = "transcribe"
    SARVAM_STT_SAMPLE_RATE: int = 16000

    SARVAM_TTS_WS_URL: str = "wss://api.sarvam.ai/text-to-speech/ws"
    SARVAM_TTS_MODEL: str = "bulbul:v3"
    SARVAM_TTS_SPEAKER: str = "priya"
    SARVAM_TTS_SAMPLE_RATE: int = 16000


settings = Settings()
