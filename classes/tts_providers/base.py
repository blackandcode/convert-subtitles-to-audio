"""Base abstractions and configuration models for TTS providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class SynthesisResult:
    """Value object wrapping synthesized audio bytes."""

    audio_bytes: bytes
    file_extension: str | None = None
    mime_type: str | None = None


class TTSProvider(ABC):
    """Strategy interface for text-to-speech providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier (e.g., `openai`)."""

    @property
    @abstractmethod
    def output_format(self) -> str:
        """Audio file extension produced by this provider (e.g., `mp3`)."""

    @property
    @abstractmethod
    def cache_fingerprint(self) -> Tuple[str, ...]:
        """Immutable tuple describing cache-relevant configuration parameters."""

    @abstractmethod
    def synthesize(self, text: str) -> SynthesisResult:
        """Generate spoken audio for the supplied text."""


@dataclass(frozen=True)
class OpenAIProviderConfig:
    """Configuration for the OpenAI TTS backend."""

    model: str
    voice: str
    response_format: str
    instructions: str
    force_language: str | None = None

    @property
    def output_format(self) -> str:
        return self.response_format


@dataclass(frozen=True)
class ElevenLabsProviderConfig:
    """Configuration for the ElevenLabs TTS backend."""

    voice_id: str
    model_id: str
    output_format: str
    stability: float | None = None
    similarity_boost: float | None = None
    style: float | None = None
    use_speaker_boost: bool | None = None

    @property
    def file_extension(self) -> str:
        if self.output_format.startswith("mp3"):
            return "mp3"
        if self.output_format.startswith("ogg"):
            return "ogg"
        if self.output_format.startswith("wav"):
            return "wav"
        return "mp3"


@dataclass(frozen=True)
class GoogleProviderConfig:
    """Configuration for the Google Cloud Text-to-Speech backend."""

    voice_name: str
    audio_encoding: str
    speaking_rate: float | None = None
    pitch: float | None = None
    sample_rate_hertz: int | None = None
    volume_gain_db: float | None = None
    effects_profile_ids: Tuple[str, ...] = ()
    language_code: str | None = None

    @property
    def output_format(self) -> str:
        encoding = self.audio_encoding.upper()
        if encoding == "MP3":
            return "mp3"
        if encoding == "OGG_OPUS":
            return "ogg"
        if encoding in {"LINEAR16", "MULAW", "ALAW"}:
            return "wav"
        return "mp3"


