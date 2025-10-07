"""Utility helpers shared across the SRT to audio pipeline."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable, List

from pydub import AudioSegment


def ensure_directory(path: Path) -> None:
    """Create the directory if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def timedelta_to_ms(td) -> int:
    """Convert a ``datetime.timedelta`` into milliseconds."""
    return int(td.total_seconds() * 1000)


def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    """Split text into safe chunks to stay under the API character ceiling."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    parts: List[str] = []
    start = 0
    end = len(text)
    while start < end:
        parts.append(text[start : start + max_chars])
        start += max_chars
    return parts


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp a floating point value into the provided bounds."""
    return max(min_value, min(value, max_value))


def change_playback_speed(segment: AudioSegment, speed: float) -> AudioSegment:
    """Create a new audio segment adjusted to the requested playback speed."""
    if speed <= 0:
        raise ValueError("Playback speed must be greater than zero.")

    if math.isclose(speed, 1.0, rel_tol=1e-3):
        return segment

    # Adjust frame rate to change speed, then reset to original rate for pitch preservation
    new_frame_rate = int(segment.frame_rate * speed)
    shifted = segment._spawn(segment.raw_data, overrides={"frame_rate": new_frame_rate})
    return shifted.set_frame_rate(segment.frame_rate)
