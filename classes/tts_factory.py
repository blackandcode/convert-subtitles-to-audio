"""Factory helpers to instantiate configured TTS providers."""

from __future__ import annotations

from .config import AppConfig
from .tts_providers import (
    ElevenLabsProviderConfig,
    GoogleProviderConfig,
    OpenAIProviderConfig,
    TTSProvider,
)
from .tts_providers.elevenlabs_provider import ElevenLabsProvider
from .tts_providers.google_provider import GoogleTTSProvider
from .tts_providers.openai_provider import OpenAIProvider


def create_tts_provider(config: AppConfig) -> TTSProvider:
    """Build a TTSProvider instance based on application configuration."""

    provider_config = config.provider_config

    if isinstance(provider_config, OpenAIProviderConfig):
        return OpenAIProvider(config=provider_config)

    if isinstance(provider_config, ElevenLabsProviderConfig):
        return ElevenLabsProvider(config=provider_config)

    if isinstance(provider_config, GoogleProviderConfig):
        return GoogleTTSProvider(config=provider_config)

    raise ValueError(f"Unsupported provider configuration type: {type(provider_config)!r}")


