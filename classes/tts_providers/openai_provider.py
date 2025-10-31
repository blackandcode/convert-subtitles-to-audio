"""OpenAI text-to-speech provider implementation."""

from __future__ import annotations

from typing import Tuple

from openai import OpenAI

from .base import OpenAIProviderConfig, SynthesisResult, TTSProvider


class OpenAIProvider(TTSProvider):
    """Adapter over the OpenAI TTS API."""

    def __init__(self, config: OpenAIProviderConfig, client: OpenAI | None = None) -> None:
        self._config = config
        self._client = client or OpenAI()

    @property
    def name(self) -> str:
        return "openai"

    @property
    def output_format(self) -> str:
        return self._config.output_format.lower()

    @property
    def cache_fingerprint(self) -> Tuple[str, ...]:
        return (
            self.name,
            self._config.model,
            self._config.voice,
            self._config.response_format,
            self._config.instructions,
            self._config.force_language or "",
        )

    def synthesize(self, text: str) -> SynthesisResult:
        payload_text = text
        if self._config.force_language:
            payload_text = f"[lang:{self._config.force_language}]  {payload_text}"

        request_kwargs = {
            "model": self._config.model,
            "voice": self._config.voice,
            "input": payload_text,
            "response_format": self._config.response_format,
        }

        if self._config.instructions:
            request_kwargs["instructions"] = self._config.instructions

        response = self._client.audio.speech.create(**request_kwargs)
        audio_bytes = _materialize_audio_bytes(response)

        return SynthesisResult(
            audio_bytes=audio_bytes,
            file_extension=self.output_format,
            mime_type=None,
        )


def _materialize_audio_bytes(response) -> bytes:
    if hasattr(response, "read") and callable(response.read):
        return response.read()
    if hasattr(response, "to_bytes") and callable(response.to_bytes):
        return response.to_bytes()
    if hasattr(response, "getvalue") and callable(response.getvalue):
        return response.getvalue()
    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, bytes):
            return content
    raise TypeError("Unexpected response type returned by OpenAI audio.speech.create")


