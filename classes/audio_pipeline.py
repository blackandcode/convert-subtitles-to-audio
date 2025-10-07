"""Audio assembly logic that respects subtitle timing."""

from __future__ import annotations

from typing import Sequence

import math
import srt
from pydub import AudioSegment

from .speech_synthesizer import SpeechSynthesizer
from .utils import change_playback_speed, chunk_text, timedelta_to_ms


class AudioPipeline:
    """Combine synthesized speech chunks into a single timed audio track."""

    def __init__(
        self,
        synthesizer: SpeechSynthesizer,
        fill_to_end: bool,
        hard_cut: bool,
        pad_leading_ms: int,
        pad_trailing_ms: int,
        max_chars_per_call: int,
        max_speedup: float,
    ) -> None:
        self.synthesizer = synthesizer
        self.fill_to_end = fill_to_end
        self.hard_cut = hard_cut
        self.pad_leading_ms = max(0, pad_leading_ms)
        self.pad_trailing_ms = max(0, pad_trailing_ms)
        self.max_chars_per_call = max_chars_per_call
        self.max_speedup = max(1.0, max_speedup)

    def build(self, subtitles: Sequence[srt.Subtitle]) -> AudioSegment:
        """Assemble subtitles into a single audio track with proper timing.

        Iterates through subtitles, synthesizes speech, adjusts speed if needed,
        and pads with silence to match subtitle durations.
        """
        final_audio = AudioSegment.silent(duration=0)
        cursor_ms = 0

        # Add leading silence if configured
        if self.pad_leading_ms > 0:
            final_audio += AudioSegment.silent(duration=self.pad_leading_ms)
            cursor_ms += self.pad_leading_ms

        for subtitle in subtitles:
            start = timedelta_to_ms(subtitle.start)
            end = timedelta_to_ms(subtitle.end)
            slot_length = max(0, end - start)

            # Add silence to reach the start of this subtitle
            if start > cursor_ms:
                final_audio += AudioSegment.silent(duration=start - cursor_ms)
                cursor_ms = start

            raw_text = (subtitle.content or "").strip().replace("\n", " ")
            if not raw_text:
                # No text: just pad to end if filling
                if self.fill_to_end and cursor_ms < end:
                    final_audio += AudioSegment.silent(duration=end - cursor_ms)
                    cursor_ms = end
                continue

            # Synthesize speech in chunks
            speech_segments = AudioSegment.silent(duration=0)
            for chunk in chunk_text(raw_text, max_chars=self.max_chars_per_call):
                chunk_audio = self.synthesizer.synthesize(chunk)
                speech_segments += chunk_audio

            speech_length = len(speech_segments)

            # If speech is longer than slot, speed it up (capped)
            if slot_length > 0 and speech_length > slot_length:
                desired_ms = slot_length
                speed_factor = speech_length / desired_ms if desired_ms else 1.0
                speed_factor = min(speed_factor, self.max_speedup)
                if speed_factor > 1.0 and not math.isclose(speed_factor, 1.0, rel_tol=1e-2):
                    speech_segments = change_playback_speed(speech_segments, speed_factor)
                    speech_length = len(speech_segments)

            if self.fill_to_end:
                # Hard cut if enabled and still too long
                if speech_length > slot_length and self.hard_cut:
                    speech_segments = speech_segments[:slot_length]
                    speech_length = len(speech_segments)

                # Add speech and pad to end of slot
                final_audio += speech_segments
                cursor_ms += speech_length

                if cursor_ms < end:
                    final_audio += AudioSegment.silent(duration=end - cursor_ms)
                    cursor_ms = end
            else:
                # Natural flow: just add speech
                final_audio += speech_segments
                cursor_ms += speech_length

        # Add trailing silence
        if self.pad_trailing_ms > 0:
            final_audio += AudioSegment.silent(duration=self.pad_trailing_ms)

        return final_audio
