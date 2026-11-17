# Verification record

Local verification date: 2026-11-17.

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
- Temporary audio and integration outputs were removed. No recording is bundled.
- A live Google translation request for the synthetic sentence
  "The house has a small garden." returned the expected Spanish translation.
  The sandbox initially blocked the network request; the permitted network run passed.
- Command-line help, PowerShell syntax, and Bash launcher syntax were checked.
- Git ignore rules were verified in a disposable repository: media, generated
  results, bytecode, and virtual environments are ignored; source files and the
  empty input/output placeholders remain publishable.

## Not claimed

No macOS or Linux runtime test was performed locally. The GitHub Actions matrix is
provided for those platforms and has not been run remotely during this preparation.
CUDA acceleration, all audio codecs, all languages, all Python versions, and every
CPU architecture have not been tested. The clean environment check validated imports
and behavior tests; the real model integration check used the existing environment.

Google translation remains an unofficial best-effort service. A successful request
does not guarantee future availability or linguistic accuracy.

## Repeat the checks

After installation, use your project's environment interpreter in place of `python`:

```bash
python -m unittest discover -s tests -v
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
