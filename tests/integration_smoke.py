"""Optional local model check using 12 seconds of a user-supplied recording."""

import argparse
import array
import contextlib
import io
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import transcribe_translate as app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", type=Path)
    parser.add_argument("--model", default="small.en")
    parser.add_argument("--language", default="en")
    args = parser.parse_args()
    from faster_whisper.audio import decode_audio

    audio = decode_audio(str(args.recording))[:12 * 16000]
    if len(audio) == 0:
        raise ValueError("The recording is empty.")
    samples = array.array("h", (int(max(-1, min(1, float(value))) * 32767) for value in audio))
    if sys.byteorder != "little":
        samples.byteswap()
    with tempfile.TemporaryDirectory(prefix="audio-texto-check-") as directory:
        root = Path(directory)
        clip = root / "test recording.wav"
        with wave.open(str(clip), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(samples.tobytes())
        # Suppress transcript paths/output from this private integration check.
        with contextlib.redirect_stdout(io.StringIO()):
            status = app.main([str(clip), "--model", args.model, "--language", args.language,
                               "--no-translate", "--local-files-only"])
        if status != 0:
            raise RuntimeError(f"Smoke test failed with exit code {status}.")
        metadata, rows = app.load_checkpoint(root / "test recording.metadata.json")
        assert rows and all(row.text.strip() for row in rows)
        assert all(row.translation_status == "skipped" for row in rows)
        assert metadata["duration_seconds"] <= 12.1
        transcript = (root / f'test recording.transcript.{metadata["detected_language"]}.txt').read_text(encoding="utf-8-sig")
        assert transcript.strip() == "\n".join(row.text for row in rows)
        print(f"PASS: local model, audio decoding, {len(rows)} speech segments, five exports, and checkpoint reload.")
    print("Temporary audio and results removed. No transcript was sent to a translation provider.")


if __name__ == "__main__":
    main()
