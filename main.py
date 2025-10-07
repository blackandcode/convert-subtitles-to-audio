#!/usr/bin/env python3
"""Command line entry point for converting SRT subtitles into speech audio."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from classes.audio_pipeline import AudioPipeline
from classes.config import AppConfig
from classes.speech_synthesizer import SpeechSynthesizer
from classes.subtitle_service import SubtitleService

# Ensure environment variables (OPENAI_API_KEY, etc.) are available early on.
load_dotenv()


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an SRT subtitle file into a timed speech track using OpenAI TTS."
    )
    parser.add_argument(
        "srt_path",
        nargs="?",
        default=None,
        help="Path to the input SRT file (defaults to ./input.srt or TTS_SRT_PATH)",
    )
    parser.add_argument(
        "-o",
        "--out",
        default=None,
        help="Destination audio file path (e.g. voiceover.mp3)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI TTS model identifier",
    )
    parser.add_argument(
        "--voice",
        default=None,
        help="Voice preset to use for synthesis",
    )
    parser.add_argument(
        "--format",
        default=None,
        choices=["mp3", "wav", "flac", "aac", "opus", "pcm"],
        help="Audio format produced by the service",
    )
    parser.add_argument(
        "--no-fill",
        action="store_true",
        help="Do not pad segments to the subtitle end time (looser sync).",
    )
    parser.add_argument(
        "--hard-cut",
        action="store_true",
        help="Trim segments that exceed their subtitle slot when padding is enabled.",
    )
    parser.add_argument(
        "--pad-start",
        type=int,
        default=None,
        help="Leading silence in milliseconds before the first subtitle.",
    )
    parser.add_argument(
        "--pad-end",
        type=int,
        default=None,
        help="Trailing silence in milliseconds after the last subtitle.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=None,
        help="Maximum characters per TTS request.",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Directory used to cache TTS chunks so reruns resume instantly.",
    )
    parser.add_argument(
        "--max-speedup",
        type=float,
        default=None,
        help="Maximum playback speed multiplier applied when speech overruns its slot.",
    )
    return parser


def create_openai_client() -> OpenAI:
    """Instantiate the OpenAI client, relying on environment configuration."""
    return OpenAI()

def run_cli(argv: list[str] | None = None) -> int:
    parser = create_argument_parser()
    args = parser.parse_args(argv)

    config = AppConfig.from_args(args)
    subtitle_service = SubtitleService(transliterate=config.transliterate)

    default_srt = os.getenv("TTS_SRT_PATH", "input.srt")
    subtitle_path = Path(args.srt_path or default_srt)
    if not subtitle_path.exists():
        parser.error(f"Subtitle file not found: {subtitle_path}")

    subtitles = subtitle_service.load(subtitle_path)

    client = create_openai_client()
    synthesizer = SpeechSynthesizer(
        client=client,
        model=config.model,
        voice=config.voice,
        output_format=config.output_format,
        cache_dir=config.cache_dir,
    )

    pipeline = AudioPipeline(
        synthesizer=synthesizer,
        fill_to_end=config.fill_to_end,
        hard_cut=config.hard_cut,
        pad_leading_ms=config.pad_leading_ms,
        pad_trailing_ms=config.pad_trailing_ms,
        max_chars_per_call=config.max_chars_per_call,
        max_speedup=config.max_speedup,
    )

    final_audio = pipeline.build(subtitles)

    default_output = os.getenv("TTS_OUTPUT_PATH", "voiceover.mp3")
    output_path = Path(args.out or default_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_format = output_path.suffix.lstrip(".") or config.output_format
    final_audio.export(output_path, format=output_format)

    print(f"Done: {output_path}")
    return 0


def main() -> None:
    sys.exit(run_cli())


if __name__ == "__main__":
    main()
