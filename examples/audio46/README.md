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
| [audio46.translation.es.txt](expected/audio46.translation.es.txt) | Explicit `[TRANSLATION SKIPPED]` markers |
| [audio46.translation.es.timestamps.txt](expected/audio46.translation.es.timestamps.txt) | The same markers with segment times |
| [audio46.metadata.json](expected/audio46.metadata.json) | Settings, times, text, and translation statuses |

Translation was deliberately disabled. This example demonstrates the local workflow
without depending on a translation provider, and no transcript was sent to Google
to generate these results. The Spanish-suffixed files contain status markers, not
Spanish translations. The English transcription is unedited program output and can
contain recognition errors; it is not a verified verbatim transcript or an answer key.

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
`--local-files-only` to require offline operation. Existing outputs are protected;
choose another output directory or use `--overwrite` intentionally for another run.

You should get the same five output types and `skipped` translation statuses.
Text, segment boundaries, and timestamps can vary with dependency/model versions
and hardware. Metadata includes its generation time, so byte-identical reproduction
is not expected. Compare the recognized text with the recording when assessing accuracy.

To translate your generated checkpoint later, use the `--resume` instructions in
the main README. Translation sends transcript text to Google and requires network
access; it is separate from reproducing this local example.

## Recorded environment

- Generation date: 2026-11-17.
- Platform: Windows, 64-bit Python 3.14.7, CPU `int8`, beam size 5, language `en`.
- Program version: 1.0.0; model: `small.en` with VAD enabled.
- Cached model revision: `d1d751a5f8271d482d14ca55d9e2deeebbae577f`.
- faster-whisper 1.2.1, CTranslate2 4.9.0, PyAV 18.1.0, ONNX Runtime 1.32.0.
- Flags: `--no-translate --local-files-only`; target language stored as `es`.
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
