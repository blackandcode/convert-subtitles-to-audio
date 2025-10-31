"""Google Cloud Text-to-Speech provider implementation."""

from __future__ import annotations

from typing import Tuple

import google.cloud.texttospeech as tts

from .base import GoogleProviderConfig, SynthesisResult, TTSProvider


class GoogleTTSProvider(TTSProvider):
    """Adapter over the Google Cloud Text-to-Speech API."""

    def __init__(self, config: GoogleProviderConfig, client: tts.TextToSpeechClient | None = None) -> None:
        self._config = config
        self._client = client or tts.TextToSpeechClient()

    @property
    def name(self) -> str:
        return "google"

    @property
    def output_format(self) -> str:
        return self._config.output_format

    @property
    def cache_fingerprint(self) -> Tuple[str, ...]:
        return (
            self.name,
            self._config.voice_name,
            self._config.audio_encoding.upper(),
            str(self._config.speaking_rate or ""),
            str(self._config.pitch or ""),
            str(self._config.sample_rate_hertz or ""),
            str(self._config.volume_gain_db or ""),
            "|".join(self._config.effects_profile_ids),
            self._config.language_code or "",
        )

    def synthesize(self, text: str) -> SynthesisResult:
        language_code = self._config.language_code or _derive_language(self._config.voice_name)

        synthesis_input = tts.SynthesisInput(text=text)
        voice_params = tts.VoiceSelectionParams(
            language_code=language_code,
            name=self._config.voice_name,
        )

        audio_config_kwargs = {
            "audio_encoding": _resolve_audio_encoding(self._config.audio_encoding),
        }

        if self._config.speaking_rate is not None:
            audio_config_kwargs["speaking_rate"] = self._config.speaking_rate
        if self._config.pitch is not None:
            audio_config_kwargs["pitch"] = self._config.pitch
        if self._config.sample_rate_hertz is not None:
            audio_config_kwargs["sample_rate_hertz"] = self._config.sample_rate_hertz
        if self._config.volume_gain_db is not None:
            audio_config_kwargs["volume_gain_db"] = self._config.volume_gain_db
        if self._config.effects_profile_ids:
            audio_config_kwargs["effects_profile_id"] = list(self._config.effects_profile_ids)

        audio_config = tts.AudioConfig(**audio_config_kwargs)

        response = self._client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config,
        )

        return SynthesisResult(
            audio_bytes=response.audio_content,
            file_extension=self.output_format,
        )


def _derive_language(voice_name: str) -> str:
    parts = voice_name.split("-")
    if len(parts) >= 2:
        return "-".join(parts[:2])
    return "en-US"


def _resolve_audio_encoding(value: str) -> tts.AudioEncoding:
    normalized = value.upper()
    try:
        return tts.AudioEncoding[normalized]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Unsupported Google TTS audio encoding '{value}'.") from exc


