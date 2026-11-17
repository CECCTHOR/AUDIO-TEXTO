# Audio Texto

[![Tests](https://github.com/CECCTHOR/AUDIO-TEXTO/actions/workflows/tests.yml/badge.svg)](https://github.com/CECCTHOR/AUDIO-TEXTO/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Transcribe audio/video locally with faster-whisper and optionally translate the
transcript into Spanish using Google Translate. English is the default source
language. All code, messages, and project documentation are in English.

## What is included

- Local CPU transcription, with no GPU required.
- Audio/video input supported by PyAV, including common MP4, OGG, WAV, and MP3 files.
- Plain text, timestamped text, and JSON output from the same segment records.
- Explicit translation status and errors instead of silently copying English.
- Saved transcripts before translation, resumable translation, and overwrite protection.
- Windows PowerShell and macOS/Linux Bash launchers.
- Automated tests and a GitHub Actions workflow.

This folder is a standalone distribution of an earlier personal audio workflow.
Personal recordings, transcripts, exercise images, installed environments, and model
weights are intentionally not distributed. The original personal workflow is unchanged.

## Requirements and compatibility

- A desktop/server installation of **64-bit Python 3.10 or newer**.
- Windows, macOS, or Linux on a platform with compatible wheels for the dependencies.
- Internet for package installation and the first model download.
- Internet for translation; transcription can run offline once the model is cached.
- Enough free memory and disk space for the chosen model. Use `tiny.en` or `base.en`
  when the default `small.en` model is too demanding.

The application is written for cross-platform use, but not every PC or architecture
is guaranteed to support its native dependencies. Local verification was performed
on Windows with Python 3.14.7. The CI workflow targets Windows, macOS, and Linux with
Python 3.12 and 3.14; those remote checks only run after you publish the repository.
No macOS/Linux runtime verification is claimed by the local Windows test.

Audio decoding uses PyAV. Its usual binary wheels bundle FFmpeg libraries, so a
separate FFmpeg command is not normally needed. Source builds and unusual formats
may require additional platform dependencies. See the
[faster-whisper documentation](https://github.com/SYSTRAN/faster-whisper).

## Installation

Download or clone this repository, then open a terminal **inside this folder**.
Do not copy `.venv` from another computer: create a new environment on each machine.

```bash
git clone https://github.com/CECCTHOR/AUDIO-TEXTO.git
cd AUDIO-TEXTO
```

Windows PowerShell:

```powershell
py --version
py setup_environment.py
.\.venv\Scripts\python.exe transcribe_translate.py --help
```

If Windows does not provide `py`, use `python setup_environment.py` instead.

macOS / Linux:

```bash
python3 --version
python3 setup_environment.py
.venv/bin/python transcribe_translate.py --help
```

On Linux, install your distribution's Python venv package if `venv`/`ensurepip`
is missing. The setup script reuses an existing environment without clearing it.
After changing the base Python installation, recreate the environment rather than
moving or copying it. See [Python venv documentation](https://docs.python.org/3/library/venv.html).

Manual installation is also available:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

On Windows, use `py -m venv .venv` and `.\.venv\Scripts\python.exe` for the last two commands.

## Process a recording

Place a recording in `input/`. Example commands assume its name is `sample.mp4`.
Quote paths containing spaces.

Windows:

```powershell
.\.venv\Scripts\python.exe transcribe_translate.py "input\sample.mp4" --output-dir output
```

macOS / Linux:

```bash
.venv/bin/python transcribe_translate.py "input/sample.mp4" --output-dir output
```

The script shows progress while loading the model, transcribing, and translating.
The first run downloads the model. Following runs reuse the local model cache.
By default, output goes beside the recording if `--output-dir` is omitted.
Do not run several jobs with the same input stem in the same output directory.

Optional wrappers:

```powershell
.\run.ps1 "input\sample.mp4" --output-dir output
```

```bash
bash run.sh "input/sample.mp4" --output-dir output
```

If PowerShell blocks `.ps1` files, use the direct Python command above. No system
execution-policy change is needed. Relative input/output paths refer to your
current working directory, even when a launcher is invoked from another folder.

## Offline and other languages

Transcription only (no transcript is sent to Google):

```bash
python transcribe_translate.py "input/sample.mp4" --no-translate --output-dir output
```

In examples using `python`, substitute your environment's interpreter path.
Add `--local-files-only` to require cached model files and prevent model downloads.

Spanish speech translated into English requires a multilingual model:

```bash
python transcribe_translate.py "input/sample.mp4" --model small --language es --target-lang en --output-dir output
```

For automatic source detection, use `--model small --language auto`. English-only
models ending in `.en` require `--language en`. Language detection and transcription
can be wrong, especially with noise, music, very short speech, or overlapping voices.

CPU with `int8` is the portable default. CUDA is optional and requires compatible
NVIDIA hardware and libraries. See upstream instructions before trying
`--device cuda --compute-type float16`. Apple GPU acceleration is not provided here.

## Output files

For English speech translated to Spanish, `sample.mp4` produces:

| File | Contents |
| --- | --- |
| `sample.transcript.en.txt` | Recognized English speech |
| `sample.transcript.en.timestamps.txt` | Speech with segment times |
| `sample.translation.es.txt` | Spanish text or explicit status placeholders |
| `sample.translation.es.timestamps.txt` | The same translations with times |
| `sample.metadata.json` | Settings, source filename, segments, statuses, and errors |

Language suffixes follow the detected source and selected target. Text files use
UTF-8 with a BOM for Windows compatibility. Timestamps refer to the original media.
Metadata stores only the source filename, not the original machine's absolute path.

Translation statuses are `pending`, `complete`, `failed`, or `skipped`.
Incomplete text is shown as `[TRANSLATION PENDING]`, `[TRANSLATION FAILED]`, or
`[TRANSLATION SKIPPED]`. These English markers are status messages, not translations.
`--no-translate` still creates all five files, with skipped markers for translation.

Each file is replaced atomically, but the five-file set is not a single transaction.
Transcripts and an initial checkpoint are saved before translation starts. If a run
is interrupted during translation, completed work from that interrupted translation
pass may need to be repeated; the saved transcription is still available.

Existing outputs are protected. Use a different output directory or explicitly
pass `--overwrite` when replacement is intended.

## Resume translation

To retry failed translations or translate a previous `--no-translate` run:

```bash
python transcribe_translate.py --resume "output/sample.metadata.json" --overwrite
```

The original recording and Whisper model are not required to resume. Completed
segments are retained; skipped, pending, and failed segments are retried. Resume
uses the source and target languages stored in the checkpoint, regardless of CLI
language/model flags. Choose a new `--output-dir` to keep the previous results.
Only metadata generated by this distribution (`schema_version: 1`) is accepted;
the older personal workflow's metadata requires manual conversion.

Exit codes: `0` = successful transcription (translation may be deliberately skipped),
`1` = error, `2` = results saved with failed translations, `130` = interrupted.
Argument errors also use code `2`; the accompanying message distinguishes them.

## Translation service and privacy

Normal translation sends each transcript segment to Google's public translation
endpoint over HTTPS. The audio itself is processed locally. Initial model downloads
contact Hugging Face. Use `--no-translate --local-files-only` for local-only processing
after caching a model. An `.en` model only supports English transcription.

The translation endpoint is unofficial, has no service guarantee, and can change or
return HTTP 429. It is not the paid Google Cloud Translation API and uses no API key.
On rate limiting, the script stops issuing further translation requests in that run,
marks affected segments as failed, and preserves the transcript. Resume later.
Review all output before using it for study, publication, or important decisions.

Only use recordings you are permitted to process and share. Git ignore rules exclude
common media formats and generated outputs, but always inspect staged files before
publishing. Ignoring a file does not protect a file that was already committed.

## Tests and maintenance

```bash
python -m unittest discover -s tests -v
python -m pip check
```

Unit tests run without downloading a model or contacting a translator. They cover
network failures, rate limiting, output consistency, resume behavior, and overwrite
protection. GitHub Actions also installs dependencies and checks their imports.
An optional local integration check is described in [docs/VERIFICATION.md](docs/VERIFICATION.md).
See [docs/WORKFLOW.md](docs/WORKFLOW.md) for the processing procedure and
[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common problems.

## License

Copyright (c) 2026 CECCTHOR. This project's code and documentation are available
under the [MIT License](LICENSE). Dependencies and downloaded model weights keep
their own licenses.

## Publishing and maintenance

See [docs/PUBLISHING.md](docs/PUBLISHING.md) for the Git publishing procedure.
Check [GitHub Actions](https://github.com/CECCTHOR/AUDIO-TEXTO/actions) for the latest
Windows, macOS, and Linux test results.
