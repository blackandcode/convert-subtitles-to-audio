# Subtitle (.srt) to Audio Voiceover Generator / Converter

Convert any SRT subtitle file into a fully timed voice-over. The tool reads subtitles, generates speech with your chosen TTS provider (OpenAI, ElevenLabs, or Google Cloud), and outputs a single synced audio track. It supports caching, multiple jobs, and optional Serbian Latin→Cyrillic transliteration for better pronunciation.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. **Important:** Copy `.env.example` to `.env` and populate with your real credentials:

   ```bash
   cp .env.example .env
   ```

   Open the `.env` file and replace placeholder values with your actual API keys and preferences. Each variable is documented with descriptions and valid options. At minimum, you must set the API key for your chosen provider:
   
   - For OpenAI: Set `OPENAI_API_KEY`
   - For ElevenLabs: Set `ELEVENLABS_API_KEY`
   - For Google Cloud: Set `GOOGLE_APPLICATION_CREDENTIALS` path

3. Prepare your input SRT file:

   Place your subtitle file as `input.srt` in the project root, or specify a custom path using the `TTS_SRT_PATH` environment variable or command-line argument. An example file is provided in the `example/` directory for reference.

## Usage

### Basic Usage

Run a basic conversion (replace with your file and job name):

```bash
python3 main.py --srt_path examples/basic/input.srt --provider openai --job-name your_job_name
```

This generates an audio file in the `output/` directory with the naming pattern: `{job_name}-{provider}-voiceover.mp3`.

### Specifying a Provider

Choose your TTS provider:

```bash
# Use ElevenLabs
python3 main.py --provider elevenlabs

# Use Google Cloud TTS
python3 main.py --provider google

# Use OpenAI
python3 main.py --provider openai
```

Or set `TTS_PROVIDER` in your `.env` file.

### Using Job Names for Organization

Job names are important because they:
- Organize cache per job and provider at `.cache/{provider}/{job_name}/`
- Form the final output filename: `output/{job_name}-{provider}-voiceover.mp3`

Use them to keep different projects/versions separate and reproducible:

```bash
# Process a specific project
python3 main.py --job-name contest-training

# Output: output/contest-training-openai-voiceover.mp3
# Cache: .cache/openai/contest-training/
```

```bash
# Different job with different provider
python3 main.py --job-name production-narration --provider elevenlabs

# Output: output/production-narration-elevenlabs-voiceover.mp3
# Cache: .cache/elevenlabs/production-narration/
```

Job names default to `"default"` if not specified. Set `TTS_JOB_NAME` in `.env` for a persistent default.

### Custom Input Files

Specify a custom SRT file path:

```bash
# Using command-line argument
python3 main.py path/to/your/subtitles.srt

# Using environment variable (in .env)
TTS_SRT_PATH=path/to/your/subtitles.srt
```

### Custom Output Path

Override the default output location:

```bash
python3 main.py -o custom/path/my-audio.mp3
```

When using `-o`, the job name prefix is not added to maintain your exact filename.

### Serbian Transliteration (why it helps)

When the SRT text is Serbian in Latin script, we automatically transliterate it to Cyrillic (configurable via `TTS_TRANSLITERATE`). Some TTS models recognize and pronounce Serbian more accurately from Cyrillic text, improving prosody and proper names. The transliterated file is cached at `.cache/{provider}/{job_name}/input-transliterated.srt`.

### Common Command-Line Options

- `--provider`: Selects the TTS backend (`openai`, `elevenlabs`, `google`)
- `--job-name`: Organizes cache and output by project/version name
- `-o`, `--out`: Custom output file path
- `--model`, `--voice`, `--instructions`, `--force-language`: OpenAI-specific overrides
- `--format`: Request a different output format/extension when supported
- `--no-fill`: Skip padding to subtitle ends
- `--hard-cut`: Trim overruns instead of speeding up
- `--max-speedup`: Cap speech acceleration (default 1.15x)
- `--pad-start`, `--pad-end`: Add leading/trailing silence in milliseconds
- `--max-chars`: Limit characters per TTS call
- `--cache-dir`: Override base cache directory

### Complete Example

```bash
python3 main.py \
  --provider elevenlabs \
  --job-name my-project \
  --max-speedup 1.2 \
  --pad-start 1000 \
  --pad-end 1000 \
  path/to/subtitles.srt
```

This command:
- Uses ElevenLabs for synthesis
- Organizes cache under `.cache/elevenlabs/my-project/`
- Outputs to `output/my-project-elevenlabs-voiceover.mp3`
- Allows up to 20% speed increase if needed
- Adds 1 second of silence at start and end
- Processes the specified SRT file

> ℹ️ Copy `.env.example` to `.env` and populate it with your real provider credentials before running the app.

## File Organization

- **Input**: Your SRT can live anywhere (not just project root). Our suggestion for getting started is to keep a copy under an `examples/` folder, e.g. `examples/basic/input.srt`. You can replace it with your own file at any time.
- **Cache**: `.cache/{provider}/{job_name}/` — cached TTS chunks and transliterated SRT for fast reruns and isolation across jobs/providers.
- **Output**: `output/{job_name}-{provider}-{output_name}.mp3` — final generated audio. The folder is created automatically and ignored by Git.
This structure keeps projects tidy, enables multiple jobs side-by-side, and makes outputs easy to find.
## Troubleshooting

- **Missing input file**: Ensure `input.srt` exists in the project root, or provide a path via `TTS_SRT_PATH` or command-line argument.
- **API errors**: Verify your API keys are correctly set in `.env` for your chosen provider.
- **Audio processing issues**: Install `ffmpeg` for audio processing: `sudo apt install ffmpeg` (Linux) or `brew install ffmpeg` (macOS).
- **Cache issues**: Clear provider/job cache to force re-synthesis: `rm -rf .cache/{provider}/{job_name}/`
- **Google Cloud TTS**: Confirm your service account has `roles/cloudtexttospeech.user` permission and `GOOGLE_APPLICATION_CREDENTIALS` points to a valid JSON file.
- **ElevenLabs voices**: Find available voice IDs at https://elevenlabs.io/app/voice-library
