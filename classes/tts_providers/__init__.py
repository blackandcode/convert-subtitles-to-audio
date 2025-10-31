"""Text-to-speech provider package exports."""

from .base import (
    GoogleProviderConfig,
    OpenAIProviderConfig,
    ElevenLabsProviderConfig,
    SynthesisResult,
    TTSProvider,
)

__all__ = [
    "GoogleProviderConfig",
    "OpenAIProviderConfig",
    "ElevenLabsProviderConfig",
    "SynthesisResult",
    "TTSProvider",
]

