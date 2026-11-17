# Audio 46 example

This example uses the maintainer-provided Audio 46 recording: about two minutes of
English conversation about living in Prague and Argentina. The recording is copied
without modification as [audio46.ogg](audio46.ogg). See [NOTICE.md](NOTICE.md) for
the scope of the sample's rights and the project's MIT License.

## Included results

The complete recording was transcribed on Windows with this repository's program.
The [expected](expected) folder contains 24 speech segments exported into five files:

| File | Contents |
| --- | --- |
| [audio46.transcript.en.txt](expected/audio46.transcript.en.txt) | Raw English transcription |
| [audio46.transcript.en.timestamps.txt](expected/audio46.transcript.en.timestamps.txt) | The same text with segment times |
| [audio46.translation.es.txt](expected/audio46.translation.es.txt) | Automatic Spanish translation |
| [audio46.translation.es.timestamps.txt](expected/audio46.translation.es.timestamps.txt) | The same translation with segment times |
| [audio46.metadata.json](expected/audio46.metadata.json) | Settings, times, text, and translation statuses |

The English transcript was generated locally, then its checkpoint was resumed to
translate the 24 segments into Spanish through Google Translate. All translation
statuses are `complete`, with zero failed translations. The audio itself was not
sent to Google. Both languages are unedited program output and may contain errors;
they are not a verified verbatim transcript or an answer key.

## Reproduce it

First install the project using the main [README](../../README.md). Run the following
commands from the repository root. Your generated files go into `output/audio46`,
leaving the included reference results available for comparison.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe transcribe_translate.py examples/audio46/audio46.ogg --output-dir output/audio46 --model small.en --language en --target-lang es --no-translate
```

macOS / Linux command syntax (real-model execution on these systems is not claimed):

```bash
.venv/bin/python transcribe_translate.py examples/audio46/audio46.ogg --output-dir output/audio46 --model small.en --language en --target-lang es --no-translate
```

The first execution downloads `small.en` if it is not cached. Once cached, add
`--local-files-only` to the commands above to require offline transcription.
Existing outputs are protected;
choose another output directory or use `--overwrite` intentionally for another run.

This first step produces the five output types with `skipped` translation statuses.
To also reproduce the Spanish translation, resume the generated checkpoint:

```powershell
.\.venv\Scripts\python.exe transcribe_translate.py --resume output/audio46/audio46.metadata.json --overwrite
```

Use `.venv/bin/python` on macOS/Linux. This second step sends transcript text to
Google and requires internet access, even when the model is cached. Successful
translation changes the statuses to `complete`. Provider limits or failures are
recorded explicitly, and the saved transcript remains available to retry later.

Text, segment boundaries, and timestamps can vary with dependency/model versions
and hardware. Metadata includes its generation time, so byte-identical reproduction
is not expected. Compare the recognized text with the recording when assessing accuracy.

Keep only the first step if you prefer local transcription without a translator.
Its Spanish-suffixed files will contain `[TRANSLATION SKIPPED]` markers instead of
matching the included Spanish reference results.

## Recorded environment

- Generation date: 2026-11-17.
- Platform: Windows, 64-bit Python 3.14.7, CPU `int8`, beam size 5, language `en`.
- Program version: 1.0.0; model: `small.en` with VAD enabled.
- Cached model revision: `d1d751a5f8271d482d14ca55d9e2deeebbae577f`.
- faster-whisper 1.2.1, CTranslate2 4.9.0, PyAV 18.1.0, ONNX Runtime 1.32.0.
- Transcription flags: `--no-translate --local-files-only`; target language `es`.
- Translation pass: `--resume expected/audio46.metadata.json --overwrite` through Google.
- Recording size: 281,026 bytes; decoded duration: approximately 123.174 seconds.
- Recording SHA-256: `2d57be036e7ace9845411c24028cd619b5303f573d8ca73b871b6fec83d59cab`.

PyAV is constrained below version 19 because faster-whisper 1.2.1 passes the
`metadata_errors` argument removed by PyAV 19. The example check exercises this
decoder call so an import-only check cannot hide that incompatibility.

## Check the bundled files

After installing dependencies:

```bash
python tests/example_smoke.py
```

Use your virtual environment's interpreter instead of `python` as appropriate.
This checks the recording hash, decodes the audio, and validates all five exports
against their metadata. It loads no Whisper model and makes no network requests.
GitHub Actions runs this decoder/export check on all six OS/Python combinations.
