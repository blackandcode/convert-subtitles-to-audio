"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from .tts_providers import (
    ElevenLabsProviderConfig,
    GoogleProviderConfig,
    OpenAIProviderConfig,
)

DEFAULT_CACHE_DIR = ".cache"
DEFAULT_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "alloy"
DEFAULT_FORMAT = "mp3"
DEFAULT_INSTRUCTIONS = "You are an assistant that reads the provided text aloud clearly and naturally. Keep a neutral, engaging tone; pronounce names as written; do not read timing or markup; only read the text content."
DEFAULT_PROVIDER = "openai"
DEFAULT_ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
DEFAULT_ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_ELEVENLABS_FORMAT = "mp3_44100_128"
DEFAULT_GOOGLE_VOICE_NAME = "en-US-Neural2-A"
DEFAULT_GOOGLE_ENCODING = "MP3"


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


ProviderConfigType = Union[
    OpenAIProviderConfig,
    ElevenLabsProviderConfig,
    GoogleProviderConfig,
]


@dataclass
class AppConfig:
    """Runtime configuration derived from CLI arguments and environment variables."""

    provider: str
    provider_config: ProviderConfigType
    output_format: str
    cache_dir: Path
    job_name: str
    fill_to_end: bool
    hard_cut: bool
    pad_leading_ms: int
    pad_trailing_ms: int
    max_chars_per_call: int
    max_speedup: float
    transliterate: bool
    srt_path: Path

    @classmethod
    def from_args(cls, args) -> "AppConfig":
        """Create AppConfig from CLI args, falling back to environment variables."""
        raw_provider = (args.provider or _env_or_default("TTS_PROVIDER", DEFAULT_PROVIDER)).strip().lower()
        provider = _canonicalize_provider(raw_provider)

        job_name = getattr(args, "job_name", None) or os.getenv("TTS_JOB_NAME", "default")
        job_name = job_name.strip()

        base_cache_dir = Path(
            getattr(args, "cache_dir", None)
            or os.getenv("TTS_CACHE_DIR", DEFAULT_CACHE_DIR)
        ).expanduser()
        
        # Organize cache by provider and job name
        cache_dir = base_cache_dir / provider / job_name

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

        srt_path_env = _env_or_default("TTS_SRT_PATH", "example/input.srt")
        if getattr(args, "srt_path", None) is not None:
            srt_path = Path(args.srt_path)
        else:
            srt_path = Path(srt_path_env)        

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

        provider_config = _build_provider_config(
            provider=provider,
            args=args,
        )

        output_format_override = getattr(args, "format", None)
        if output_format_override:
            normalized_override = output_format_override.strip().lower()
        else:
            normalized_override = None

        output_format = _resolve_output_format(provider_config, normalized_override)

        return cls(
            provider=provider,
            provider_config=provider_config,
            output_format=output_format,
            cache_dir=cache_dir,
            job_name=job_name,
            fill_to_end=fill_to_end,
            hard_cut=hard_cut,
            srt_path=srt_path,
            pad_leading_ms=pad_leading_ms,
            pad_trailing_ms=pad_trailing_ms,
            max_chars_per_call=max_chars_per_call,
            max_speedup=max_speedup,
            transliterate=transliterate,
        )


def _canonicalize_provider(value: str) -> str:
    if value in {"openai", "open-ai"}:
        return "openai"
    if value in {"elevenlabs", "11labs", "11-labs"}:
        return "elevenlabs"
    if value in {"google", "google-cloud", "google_tts", "googletts", "gcloud"}:
        return "google"
    return value


def _build_provider_config(provider: str, args) -> ProviderConfigType:
    if provider == "openai":
        return _build_openai_config(args)
    if provider == "elevenlabs":
        return _build_elevenlabs_config()
    if provider == "google":
        return _build_google_config()
    raise ValueError(f"Unsupported TTS provider '{provider}'.")


def _build_openai_config(args) -> OpenAIProviderConfig:
    model = args.model or _env_or_default("OPENAI_TTS_MODEL", DEFAULT_MODEL)
    voice = args.voice or _env_or_default("OPENAI_TTS_VOICE", DEFAULT_VOICE)
    response_format = args.format or _env_or_default("OPENAI_TTS_FORMAT", DEFAULT_FORMAT)
    instructions = (
        getattr(args, "instructions", None)
        or _env_or_default("OPENAI_TTS_INSTRUCTIONS", DEFAULT_INSTRUCTIONS)
    )
    force_language_arg = getattr(args, "force_language", None)
    raw_force_language = (
        force_language_arg
        if force_language_arg is not None
        else os.getenv("OPENAI_TTS_FORCE_LANGUAGE")
    ) or None
    return OpenAIProviderConfig(
        model=model,
        voice=voice,
        response_format=response_format,
        instructions=instructions,
        force_language=raw_force_language,
    )


def _build_elevenlabs_config() -> ElevenLabsProviderConfig:
    voice_id = _env_or_default("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID)
    model_id = _env_or_default("ELEVENLABS_MODEL_ID", DEFAULT_ELEVENLABS_MODEL_ID)
    output_format = _env_or_default("ELEVENLABS_OUTPUT_FORMAT", DEFAULT_ELEVENLABS_FORMAT)
    stability = _env_float_optional("ELEVENLABS_STABILITY")
    similarity_boost = _env_float_optional("ELEVENLABS_SIMILARITY_BOOST")
    style = _env_float_optional("ELEVENLABS_STYLE")
    use_speaker_boost = _env_bool_optional("ELEVENLABS_USE_SPEAKER_BOOST")
    return ElevenLabsProviderConfig(
        voice_id=voice_id,
        model_id=model_id,
        output_format=output_format,
        stability=stability,
        similarity_boost=similarity_boost,
        style=style,
        use_speaker_boost=use_speaker_boost,
    )


def _build_google_config() -> GoogleProviderConfig:
    voice_name = _env_or_default("GOOGLE_TTS_VOICE_NAME", DEFAULT_GOOGLE_VOICE_NAME)
    audio_encoding = _env_or_default("GOOGLE_TTS_AUDIO_ENCODING", DEFAULT_GOOGLE_ENCODING)
    speaking_rate = _env_float_optional("GOOGLE_TTS_SPEAKING_RATE")
    pitch = _env_float_optional("GOOGLE_TTS_PITCH")
    sample_rate = _env_int_optional("GOOGLE_TTS_SAMPLE_RATE_HZ")
    volume_gain = _env_float_optional("GOOGLE_TTS_VOLUME_GAIN_DB")
    language_override = os.getenv("GOOGLE_TTS_LANGUAGE_CODE") or None
    effects_raw = os.getenv("GOOGLE_TTS_EFFECTS_PROFILE_IDS")
    effects: tuple[str, ...]
    if effects_raw:
        effects = tuple(part.strip() for part in effects_raw.split(",") if part.strip())
    else:
        effects = ()
    return GoogleProviderConfig(
        voice_name=voice_name,
        audio_encoding=audio_encoding,
        speaking_rate=speaking_rate,
        pitch=pitch,
        sample_rate_hertz=sample_rate,
        volume_gain_db=volume_gain,
        effects_profile_ids=effects,
        language_code=(language_override.strip() if language_override else None),
    )


def _resolve_output_format(provider_config: ProviderConfigType, override: str | None) -> str:
    if override:
        return override
    if isinstance(provider_config, OpenAIProviderConfig):
        return provider_config.output_format
    if isinstance(provider_config, ElevenLabsProviderConfig):
        return provider_config.file_extension
    if isinstance(provider_config, GoogleProviderConfig):
        return provider_config.output_format
    return DEFAULT_FORMAT


def _env_float_optional(name: str) -> float | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    return float(raw)


def _env_int_optional(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    return int(raw)


def _env_bool_optional(name: str) -> bool | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}
