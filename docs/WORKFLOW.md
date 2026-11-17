# Processing procedure

1. Install Python and create this project's virtual environment on the target machine.
2. Install `requirements.txt` with that environment's interpreter.
3. Put a permitted recording in `input/`, or use its full path.
4. Run `transcribe_translate.py`. Select `--no-translate` for local transcription only.
5. The program validates arguments and checks for existing output files.
6. Load the requested Whisper model from cache, or download it on first use.
7. Decode audio and transcribe with voice activity detection (VAD).
8. If VAD finds no speech, retry once without VAD. If still empty, report an error.
9. Save plain and timestamped transcripts plus a checkpoint before contacting Google.
10. Translate each segment, or explicitly mark translation as skipped.
11. Mark provider errors as failed. After HTTP 429, avoid further requests in that run.
12. Export all text formats and JSON from the same segment records.
13. Read the exit status and inspect `translation_status` in the JSON.
14. Review names, numbers, unusual words, and context against the recording.
15. Use `--resume` to retry incomplete translations without transcribing again.

## Corrections

Treat the metadata JSON as the common record when making segment-level corrections.
If you edit only a plain text file, its timestamped version and metadata will differ.
Keep the original recording for verification; transcription is not guaranteed verbatim.

The normal script processes one input per invocation. For several recordings, run
separate commands and keep separate output directories when filenames share a stem.
No exercise-answer generator or speaker diarization is included. Human labels such
as "Speaker 1" are recognized speech, not automatic voice identity assignment.

## Compared with the original workflow

This repository removes hard-coded personal paths and the unused deep-translator
dependency. Output defaults to the input directory. Translation failures are visible,
the transcript is saved first, and existing results require explicit overwrite.
New metadata includes versioned statuses and can be moved between computers.
The original AUDIO 1-40 collection is not bundled or modified.
