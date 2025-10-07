"""Speech synthesis wrapper with caching and retry logic."""

from __future__ import annotations

import hashlib
import io
import math
from pathlib import Path

from openai import OpenAI
from pydub import AudioSegment
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .utils import change_playback_speed, ensure_directory


class SpeechSynthesizer:
    """Generate speech audio for subtitle chunks with disk caching."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        voice: str,
        output_format: str,
        cache_dir: Path,
    ) -> None:
        self._client = client
        self.model = model
        self.voice = voice
        self.output_format = output_format
        self.cache_dir = cache_dir
        ensure_directory(self.cache_dir)

    def synthesize(self, text: str, speed: float = 1.0) -> AudioSegment:
        """Synthesize speech for the given text and adjust playback speed."""
        base_audio_bytes = self._load_or_generate_bytes(text)
        segment = AudioSegment.from_file(io.BytesIO(base_audio_bytes), format=self.output_format)

        if speed <= 0:
            raise ValueError("Playback speed must be greater than zero.")

        if not math.isclose(speed, 1.0, rel_tol=1e-3):
            segment = change_playback_speed(segment, speed)

        return segment

    def _load_or_generate_bytes(self, text: str) -> bytes:
        """Load cached audio bytes or generate fresh ones via API."""
        cache_file = self.cache_dir / f"{self._make_cache_key(text)}.{self.output_format}"

        if cache_file.exists():
            return cache_file.read_bytes()

        audio_bytes = self._request_speech(text)
        cache_file.write_bytes(audio_bytes)
        return audio_bytes

    def _make_cache_key(self, text: str) -> str:
        """Generate a unique hash key for caching based on synthesis parameters."""
        fingerprint = f"{self.model}|{self.voice}|{self.output_format}|{text}".encode("utf-8")
        return hashlib.sha1(fingerprint).hexdigest()

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def _request_speech(self, text: str) -> bytes:
        """Make the OpenAI TTS API request and extract audio bytes."""
        request_kwargs = {
            "model": self.model,
            "voice": self.voice,
            "input": text,
        }

        if self.output_format:
            request_kwargs["response_format"] = self.output_format

        response = self._client.audio.speech.create(**request_kwargs)

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
