"""Speech synthesis wrapper with caching and retry logic."""

from __future__ import annotations

import hashlib
import io
import math
from pathlib import Path

from pydub import AudioSegment
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .tts_providers import TTSProvider
from .utils import change_playback_speed, ensure_directory


class SpeechSynthesizer:
    """Generate speech audio for subtitle chunks with disk caching."""

    def __init__(
        self,
        provider: TTSProvider,
        cache_dir: Path,
    ) -> None:
        self._provider = provider
        self.output_format = provider.output_format.lower()
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
        cache_key = self._make_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.{self.output_format}"

        if cache_file.exists():
            return cache_file.read_bytes()

        audio_bytes = self._request_speech(text)

        # The provider may adjust the effective output format; recompute destination if needed.
        cache_file = self.cache_dir / f"{cache_key}.{self.output_format}"
        cache_file.write_bytes(audio_bytes)
        return audio_bytes

    def _make_cache_key(self, text: str) -> str:
        """Generate a unique hash key for caching based on synthesis parameters."""
        provider_parts = "|".join(self._provider.cache_fingerprint)
        fingerprint = f"{provider_parts}|{self.output_format}|{text}".encode("utf-8")
        return hashlib.sha1(fingerprint).hexdigest()

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def _request_speech(self, text: str) -> bytes:
        """Delegate synthesis to the configured provider."""
        result = self._provider.synthesize(text)

        if result.file_extension:
            new_format = result.file_extension.lower()
            if new_format != self.output_format:
                self.output_format = new_format

        return result.audio_bytes
