# SRT to Audio

Convert an SRT subtitle file into a fully timed voice-over using OpenAI TTS.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and set your credentials:

   ```bash
   cp .env.example .env
   ```

   Add your OpenAI API key to `.env`. You can also adjust defaults like model, voice, or output paths.

## Usage

Place your SRT file as `input.srt` (or set `TTS_SRT_PATH` in `.env`).

If the SRT is in Latin Serbian, it will be automatically transliterated to Cyrillic for better TTS recognition (controlled by `TTS_TRANSLITERATE`).

Run the tool:

```bash
python3 main.py
```

This generates `voiceover.mp3` (or your configured output path).

### Options

- `--model`, `--voice`, `--format`: Override voice settings.
- `--no-fill`: Skip padding to subtitle ends.
- `--hard-cut`: Trim overruns instead of speeding up.
- `--max-speedup`: Cap speech acceleration (default 1.15x).

## Troubleshooting

- Install `ffmpeg` for audio processing.
- Clear `.cache` to force re-synthesis.
