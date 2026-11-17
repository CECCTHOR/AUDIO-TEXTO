"""Check the bundled audio and exports without a Whisper model or network access."""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import transcribe_translate as app


def main() -> None:
    from faster_whisper.audio import decode_audio
    import numpy as np

    root = Path(__file__).resolve().parents[1] / "examples" / "audio46"
    recording = root / "audio46.ogg"
    expected_hash = "2d57be036e7ace9845411c24028cd619b5303f573d8ca73b871b6fec83d59cab"
    assert hashlib.sha256(recording.read_bytes()).hexdigest() == expected_hash, "Sample hash mismatch"

    metadata, rows = app.load_checkpoint(root / "expected" / "audio46.metadata.json")
    assert metadata["input_file"] == recording.name
    assert metadata["detected_language"] == "en" and metadata["target_language"] == "es"
    assert metadata["segment_count"] == len(rows)
    assert metadata["translation_complete"] is True
    assert metadata["translation_failed_count"] == 0
    assert all(row.translation_status == "complete" and row.translation.strip()
               and row.translation_error is None for row in rows)

    # This exercises faster-whisper's actual PyAV call, not just dependency imports.
    audio = decode_audio(str(recording), sampling_rate=16000)
    duration = len(audio) / 16000
    assert audio.ndim == 1 and len(audio) > 0 and np.isfinite(audio).all()
    assert abs(duration - metadata["duration_seconds"]) < 0.1
    assert all(0 <= row.start <= row.end <= duration + 0.1 for row in rows)

    paths = app.output_paths(recording.name, root / "expected", "en", "es")
    for field, key in (("text", "transcript"), ("translation", "translation")):
        values = [row.text if field == "text" else app.translation_content(row) for row in rows]
        timed = [f"[{app.format_timestamp(row.start)} -> {app.format_timestamp(row.end)}] {value}"
                 for row, value in zip(rows, values)]
        for name, lines in ((key, values), (key + "_timestamps", timed)):
            assert paths[name].read_text(encoding="utf-8-sig") == "\n".join(lines) + "\n", name
    assert all(path.read_bytes().startswith(b"\xef\xbb\xbf") for path in paths.values())
    print(f"PASS: Audio 46 decoding ({duration:.3f}s), {len(rows)} segments, and five consistent exports.")
    print("No Whisper model was loaded and no translation request was made.")


if __name__ == "__main__":
    main()
