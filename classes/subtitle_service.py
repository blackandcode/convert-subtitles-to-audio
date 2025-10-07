from __future__ import annotations

import re
from pathlib import Path
from typing import List

import srt
from cyrtranslit import to_cyrillic

"""Subtitle loading utilities."""


class SubtitleService:
    """Handle subtitle loading and optional transliteration."""

    def __init__(self, transliterate: bool = True) -> None:
        self.transliterate = transliterate

    def load(self, source: Path) -> List[srt.Subtitle]:
        """Load and optionally transliterate subtitles from the given SRT file path."""
        # Determine the file to use
        file_to_use = self._prepare_file(source)

        with file_to_use.open("r", encoding="utf-8") as handle:
            return list(srt.parse(handle.read()))

    def _prepare_file(self, source: Path) -> Path:
        """Prepare the SRT file, transliterating if needed."""
        if not self.transliterate:
            return source

        # Check if already Cyrillic
        if self._is_cyrillic(source):
            return source

        # Create transliterated copy
        transliterated_path = source.parent / "input-transliterated.srt"
        self._transliterate_file(source, transliterated_path)
        return transliterated_path

    def _is_cyrillic(self, file_path: Path) -> bool:
        """Check if the SRT file contains Cyrillic characters."""
        cyrillic_pattern = re.compile(r'[\u0400-\u04FF]')
        with file_path.open("r", encoding="utf-8") as f:
            content = f.read()
            return bool(cyrillic_pattern.search(content))

    def _transliterate_file(self, source: Path, target: Path) -> None:
        """Transliterate the SRT file to Cyrillic Serbian."""
        with source.open("r", encoding="utf-8") as src:
            content = src.read()

        # Parse SRT to preserve structure
        subtitles = list(srt.parse(content))

        # Transliterate each subtitle's content
        transliterated_subtitles = []
        for sub in subtitles:
            transliterated_content = to_cyrillic(sub.content, "sr")
            transliterated_sub = srt.Subtitle(
                index=sub.index,
                start=sub.start,
                end=sub.end,
                content=transliterated_content
            )
            transliterated_subtitles.append(transliterated_sub)

        # Write back to target
        with target.open("w", encoding="utf-8") as tgt:
            tgt.write(srt.compose(transliterated_subtitles))
