"""ElevenLabs text-to-speech provider implementation."""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Dict, Tuple

from elevenlabs.client import ElevenLabs

from .base import ElevenLabsProviderConfig, SynthesisResult, TTSProvider


class ElevenLabsProvider(TTSProvider):
    """Adapter over the ElevenLabs Text-to-Speech API."""

    def __init__(self, config: ElevenLabsProviderConfig, client: ElevenLabs | None = None) -> None:
        self._config = config
        # Explicitly pass API key to the SDK (falls back to env var if not set)
        self._client = client or ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    @property
    def name(self) -> str:
        return "elevenlabs"

    @property
    def output_format(self) -> str:
        return self._config.file_extension

    @property
    def cache_fingerprint(self) -> Tuple[str, ...]:
        return (
            self.name,
            self._config.voice_id,
            self._config.model_id,
            self._config.output_format,
            str(self._config.stability or ""),
            str(self._config.similarity_boost or ""),
            str(self._config.style or ""),
            str(self._config.use_speaker_boost or ""),
        )

    def synthesize(self, text: str) -> SynthesisResult:
        voice_settings = _build_voice_settings(self._config)

        request_kwargs = {
            "text": text,
            "voice_id": self._config.voice_id,
            "model_id": self._config.model_id,
            "output_format": self._config.output_format,
        }

        if voice_settings:
            request_kwargs["voice_settings"] = voice_settings

        audio = self._client.text_to_speech.convert(**request_kwargs)
        audio_bytes = _coerce_to_bytes(audio)

        return SynthesisResult(
            audio_bytes=audio_bytes,
            file_extension=self.output_format,
        )


def _build_voice_settings(config: ElevenLabsProviderConfig) -> Dict[str, float | bool]:
    voice_settings: Dict[str, float | bool] = {}
    if config.stability is not None:
        voice_settings["stability"] = float(config.stability)
    if config.similarity_boost is not None:
        voice_settings["similarity_boost"] = float(config.similarity_boost)
    if config.style is not None:
        voice_settings["style"] = float(config.style)
    if config.use_speaker_boost is not None:
        voice_settings["use_speaker_boost"] = bool(config.use_speaker_boost)
    return voice_settings


def _coerce_to_bytes(audio) -> bytes:
    if isinstance(audio, bytes):
        return audio
    if isinstance(audio, bytearray):
        return bytes(audio)
    if hasattr(audio, "read") and callable(audio.read):
        chunk = audio.read()
        if isinstance(chunk, (bytes, bytearray)):
            return bytes(chunk)
        if isinstance(chunk, memoryview):
            return chunk.tobytes()
        raise TypeError("Unexpected ElevenLabs audio payload chunk type from file-like object")
    if isinstance(audio, str):
        raise TypeError("Unexpected ElevenLabs audio payload type")
    if isinstance(audio, Iterable):
        buffer = bytearray()
        for chunk in audio:
            if isinstance(chunk, bytes):
                buffer.extend(chunk)
            elif isinstance(chunk, bytearray):
                buffer.extend(chunk)
            elif isinstance(chunk, memoryview):
                buffer.extend(chunk)
            else:
                raise TypeError("Unexpected ElevenLabs audio chunk type")
        return bytes(buffer)
    raise TypeError("Unexpected ElevenLabs audio payload type")


