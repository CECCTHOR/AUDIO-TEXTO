# Verification record

Verification date: 2026-11-17.

## Completed locally

- Platform: Windows, 64-bit Python 3.14.7.
- 26 automated behavior tests passed in the existing transcription environment.
- Tests passed again with `ResourceWarning` treated as an error.
- A newly created temporary virtual environment installed `requirements.txt` from
  scratch, passed `pip check`, imported faster-whisper and PyAV, and passed all
  26 tests. The temporary environment was removed afterward.
- The fresh installation resolved faster-whisper 1.2.1, CTranslate2 4.9.0,
  PyAV 19.0.2, and ONNX Runtime 1.32.0 on this Windows/Python combination.
  Transitive dependency versions may differ on other platforms or future installs.
- The cached `small.en` CPU model transcribed 12 seconds of an existing recording
  using the new script in the existing transcription environment. The integration
  check verified three nonempty segments, all five exports, and checkpoint reload.
- Temporary audio and integration outputs from that initial check were removed.
- A live Google translation request for the synthetic sentence
  "The house has a small garden." returned the expected Spanish translation.
  The sandbox initially blocked the network request; the permitted network run passed.
- Command-line help, PowerShell syntax, and Bash launcher syntax were checked.
- Git ignore rules were verified in a disposable repository: media, generated
  results, bytecode, and virtual environments are ignored; source files and the
  empty input/output placeholders remain publishable.

## Completed on GitHub Actions

The [initial published run](https://github.com/CECCTHOR/AUDIO-TEXTO/actions/runs/44184817452)
passed all six jobs for commit `c46505a69edfd11f6a2f48dd9879e6a4f657c92d`:

| Runner | Python 3.12 | Python 3.14 |
| --- | --- | --- |
| `ubuntu-latest` | Passed | Passed |
| `macos-latest` | Passed | Passed |
| `windows-latest` | Passed | Passed |

Each job installed `requirements.txt`, passed `pip check`, imported faster-whisper
and PyAV, passed the 26 behavior tests, and ran command-line help successfully.
These checks do not download a Whisper model, process a real recording, or contact
Google Translate. The real-model integration check described above ran locally on
Windows. Runner images and resolved transitive dependencies may change over time;
see [Actions](https://github.com/CECCTHOR/AUDIO-TEXTO/actions) for current results.

## Version 1.0.0 example and maintenance checks

- Created a standalone project environment on Windows with Python 3.14.7 and
  installed the complete requirements. Faster-whisper 1.2.1 remains the latest
  published version checked for this release.
- A real decoder call exposed incompatibility between faster-whisper 1.2.1 and
  PyAV 19: `metadata_errors` was removed. Requirements now constrain PyAV below 19;
  PyAV 18.1.0 successfully decoded the complete bundled recording.
- Generated all five Audio 46 reference exports from the full recording using
  cached `small.en`, CPU `int8`, and `--no-translate --local-files-only`.
  The result contains 24 segments and skipped translation statuses. No transcript
  was submitted to Google to generate the bundled example.
- Recorded the input hash, model revision, dependency versions, and reproduction
  commands in [the example README](../examples/audio46/README.md).
- Added a decoder/export smoke check that loads no model and uses no network.
  The updated CI workflow runs it in addition to the 26 existing behavior tests.
- Updated checkout to v7.0.1 and setup-python to v7.1.0, pinned to their official
  release commits. Both use Node.js 24.
- Configured weekly Dependabot proposals for Python dependencies and GitHub
  Actions. Branch pushes to `main`, pull requests, and manual dispatch run CI;
  release tags use the checks already run for their exact commit.

This section records the local release preparation. The release notes link to the
completed CI run for the tagged commit. Decoder validation is not a real-model
transcription test on macOS/Linux.

## Not claimed

Real-audio transcription on macOS/Linux, CUDA acceleration, all audio codecs, all
languages, all Python versions, and every CPU architecture have not been tested.
The clean environment and remote checks validated imports and behavior tests; the
real model integration check used the existing Windows environment.

Google translation remains an unofficial best-effort service. A successful request
does not guarantee future availability or linguistic accuracy.

## Repeat the checks

After installation, use your project's environment interpreter in place of `python`:

```bash
python -m unittest discover -s tests -v
python tests/example_smoke.py
python -m pip check
python transcribe_translate.py --help
```

Optional real-model check, using your own English recording and a cached model:

```bash
python tests/integration_smoke.py "/path/to/recording.ogg"
```

This takes the first 12 seconds, writes temporary local files, uses
`--no-translate --local-files-only`, checks the exported results, and cleans up.
Make sure the beginning contains speech. For another language, pass a compatible
cached multilingual model and language, for example `--model small --language es`.
It fails if the model is not already cached; run the main script once with downloads
enabled to obtain the model first.

To test the translation connection without sending a real transcript:

```bash
python -c "from transcribe_translate import GoogleTranslator; print(GoogleTranslator('en', 'es').translate('The house has a small garden.'))"
```

An unavailable provider raises `TranslationError`. In normal processing, that error
is recorded explicitly in segment metadata and does not discard the transcript.
