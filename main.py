#!/usr/bin/env python3
"""Command line entry point for converting SRT subtitles into speech audio."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from classes.audio_pipeline import AudioPipeline
from classes.config import AppConfig
from classes.speech_synthesizer import SpeechSynthesizer
from classes.subtitle_service import SubtitleService
from classes.tts_factory import create_tts_provider

# Ensure environment variables (OPENAI_API_KEY, etc.) are available early on.
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an SRT subtitle file into a timed speech track using configurable TTS providers."
    )
    parser.add_argument(
        "--provider",
        default=None,
        choices=["openai", "elevenlabs", "google"],
        help="TTS provider to use (overrides TTS_PROVIDER environment variable).",
    )
    parser.add_argument(
        "--job-name",
        default=None,
        help="Job name for organizing cache and output files (defaults to 'default' or TTS_JOB_NAME).",
    )
    parser.add_argument(
        "--srt-path",
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
        help="Provider model identifier (OpenAI only).",
    )
    parser.add_argument(
        "--voice",
        default=None,
        help="Voice preset to use for synthesis (OpenAI only).",
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
    parser.add_argument(
        "--instructions",
        default=None,
        help="Optional system instructions for the TTS model (OpenAI only).",
    )
    parser.add_argument(
        "--force-language",
        default=None,
        help="Force a language prefix for the OpenAI provider (e.g. 'sr').",
    )
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    parser = create_argument_parser()
    args = parser.parse_args(argv)

    config = AppConfig.from_args(args)
    
    default_srt = os.getenv("TTS_SRT_PATH", "example/input.srt")
    subtitle_path = Path(args.srt_path or default_srt) 
    if not subtitle_path.exists():
        print(f"Error: Input file not found: {subtitle_path}", file=sys.stderr)
        print(f"Please provide a valid SRT file path or place your file as 'input.srt' in the project root.", file=sys.stderr)
        print(f"You can also set TTS_SRT_PATH environment variable to specify a different default location.", file=sys.stderr)
        return 1
    
    subtitle_service = SubtitleService(transliterate=config.transliterate, cache_dir=config.cache_dir)

    subtitles = subtitle_service.load(subtitle_path)

    provider = create_tts_provider(config)
    synthesizer = SpeechSynthesizer(
        provider=provider,
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

    # Determine output path with job-based naming
    if args.out:
        output_path = Path(args.out)
    else:
        default_output_name = os.getenv("TTS_OUTPUT_PATH", "voiceover.mp3")
        output_base_name = Path(default_output_name).name
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Format: {job_name}-{provider}-{base_output_filename}
        output_filename = f"{config.job_name}-{config.provider}-{output_base_name}"
        output_path = output_dir / output_filename
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_format = output_path.suffix.lstrip(".") or synthesizer.output_format
    final_audio.export(output_path, format=output_format)

    print(f"Done: {output_path}")
    return 0


def main() -> None:
    sys.exit(run_cli())


if __name__ == "__main__":
    main()
