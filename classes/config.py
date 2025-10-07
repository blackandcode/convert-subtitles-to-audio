"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CACHE_DIR = ".cache"
DEFAULT_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "alloy"
DEFAULT_FORMAT = "mp3"


def _env_or_default(name: str, default):
    """Get environment variable value or return default if not set."""
    value = os.getenv(name)
    return value if value is not None else default


def _env_bool(name: str, default: bool) -> bool:
    """Parse environment variable as boolean, with fallback to default."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    """Parse environment variable as integer, with fallback to default."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    """Parse environment variable as float, with fallback to default."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return float(raw)


@dataclass
class AppConfig:
    """Runtime configuration derived from CLI arguments and environment variables."""

    model: str
    voice: str
    output_format: str
    cache_dir: Path
    fill_to_end: bool
    hard_cut: bool
    pad_leading_ms: int
    pad_trailing_ms: int
    max_chars_per_call: int
    max_speedup: float
    transliterate: bool

    @classmethod
    def from_args(cls, args) -> "AppConfig":
        """Create AppConfig from CLI args, falling back to environment variables."""
        model = args.model or _env_or_default("OPENAI_TTS_MODEL", DEFAULT_MODEL)
        voice = args.voice or _env_or_default("OPENAI_TTS_VOICE", DEFAULT_VOICE)
        output_format = args.format or _env_or_default("OPENAI_TTS_FORMAT", DEFAULT_FORMAT)

        cache_dir = Path(
            getattr(args, "cache_dir", None)
            or os.getenv("TTS_CACHE_DIR", DEFAULT_CACHE_DIR)
        ).expanduser()

        fill_to_end_env = _env_bool("TTS_FILL_TO_END", True)
        if getattr(args, "no_fill", False):
            fill_to_end = False
        else:
            fill_to_end = fill_to_end_env

        hard_cut_env = _env_bool("TTS_HARD_CUT", False)
        if getattr(args, "hard_cut", False):
            hard_cut = True
        else:
            hard_cut = hard_cut_env

        pad_leading_ms = (
            args.pad_start if args.pad_start is not None else _env_int("TTS_PAD_START_MS", 0)
        )
        pad_trailing_ms = (
            args.pad_end if args.pad_end is not None else _env_int("TTS_PAD_END_MS", 0)
        )

        max_chars_per_call = (
            args.max_chars if args.max_chars is not None else _env_int("TTS_MAX_CHARS", 4000)
        )

        max_speedup = (
            args.max_speedup if args.max_speedup is not None else _env_float("TTS_MAX_SPEEDUP", 1.15)
        )

        transliterate = _env_bool("TTS_TRANSLITERATE", True)

        return cls(
            model=model,
            voice=voice,
            output_format=output_format,
            cache_dir=cache_dir,
            fill_to_end=fill_to_end,
            hard_cut=hard_cut,
            pad_leading_ms=pad_leading_ms,
            pad_trailing_ms=pad_trailing_ms,
            max_chars_per_call=max_chars_per_call,
            max_speedup=max_speedup,
            transliterate=transliterate,
        )
