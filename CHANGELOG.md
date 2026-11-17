# Changelog

## [1.0.0] - 2026-11-17

First tagged public release.

- Local CPU audio/video transcription with faster-whisper.
- Optional online translation, explicit provider errors, and resumable checkpoints.
- Plain text, timestamped text, and JSON exports with overwrite protection.
- Windows PowerShell and macOS/Linux Bash launchers.
- Audio 46 demonstration recording, generated results, and reproduction commands.
- GitHub Actions checks for Windows, macOS, and Linux with Python 3.12 and 3.14.
- Updated checkout/setup-python actions, pinned to official release commits.
- Weekly Dependabot update proposals for Python dependencies and GitHub Actions.
- PyAV compatibility constraint and a real decoder check for the bundled example.
- MIT-licensed code and documentation; sample media rights are described separately.

### Verification limits

Real-audio example generation was performed on Windows. Remote checks cover
dependency installation/imports, audio decoding, behavior tests, and command-line help; they do not
transcribe real audio on macOS/Linux. Google translation is an unofficial service
and can become unavailable or impose temporary limits.

[1.0.0]: https://github.com/CECCTHOR/AUDIO-TEXTO/releases/tag/v1.0.0
