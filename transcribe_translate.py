"""Local speech transcription with optional online English/Spanish translation."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

VERSION = "1.0.0"


@dataclass
class SegmentLine:
    start: float
    end: float
    text: str
    translation: str = ""
    translation_status: str = "pending"
    translation_error: str | None = None


class TranslationError(RuntimeError):
    """A provider failure that must remain visible in the exported results."""


def language_code(value: str) -> str:
    value = value.lower()
    if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z]{2})?", value):
        raise argparse.ArgumentTypeError("Use a language code such as en, es, or pt.")
    return value


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("The value must be at least 1.")
    return number


def positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("The value must be finite and greater than 0.")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", nargs="?", type=Path, help="Audio or video path.")
    parser.add_argument("--resume", type=Path, metavar="METADATA", help="Retry pending/failed translations without transcribing again.")
    parser.add_argument("--output-dir", type=Path, help="Default: the input or metadata file's directory.")
    parser.add_argument("--model", default="small.en", help="Model name or local model directory (default: small.en).")
    parser.add_argument("--language", default="en", help="Whisper language code, or auto (default: en).")
    parser.add_argument("--target-lang", type=language_code, default="es", help="Translation language (default: es).")
    parser.add_argument("--no-translate", action="store_true", help="Local transcription only; do not contact Google.")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--compute-type", default="int8", help="Default: int8 for CPU; CUDA may need float16.")
    parser.add_argument("--beam-size", type=positive_int, default=5)
    parser.add_argument("--timeout", type=positive_float, default=12, help="Translation request timeout in seconds.")
    parser.add_argument("--retries", type=positive_int, default=2, help="Maximum attempts per segment (default: 2).")
    parser.add_argument("--local-files-only", action="store_true", help="Load cached models only; never download model files.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output files. Required for resuming in place.")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args(argv)
    if (args.input_file is None) == (args.resume is None):
        parser.error("Provide either input_file or --resume METADATA, but not both.")
    if args.resume and args.no_translate:
        parser.error("--resume cannot be combined with --no-translate.")
    if args.language != "auto":
        try:
            args.language = language_code(args.language)
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
    if not args.resume and args.model.endswith(".en") and args.language != "en":
        parser.error("English-only models require --language en. Use --model small for other languages or auto detection.")
    return args


def format_timestamp(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"


def collect_segment_rows(segments: object) -> list[SegmentLine]:
    return [SegmentLine(float(s.start), float(s.end), s.text.strip()) for s in segments if s.text.strip()]


def transcribe_file(args: argparse.Namespace) -> tuple[dict, list[SegmentLine]]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Missing transcription dependencies. Install requirements.txt in your virtual environment.") from exc
    print(f"Loading model {args.model!r} on {args.device}...", flush=True)
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type,
                         local_files_only=args.local_files_only)
    options = dict(language=None if args.language == "auto" else args.language,
                   beam_size=args.beam_size, condition_on_previous_text=True)
    print("Transcribing locally...", flush=True)
    segments, info = model.transcribe(str(args.input_file), vad_filter=True, **options)
    rows = collect_segment_rows(segments)
    if not rows:
        print("No speech found with VAD; retrying without VAD...", flush=True)
        segments, info = model.transcribe(str(args.input_file), vad_filter=False, **options)
        rows = collect_segment_rows(segments)
    if not rows:
        raise RuntimeError("No speech was detected. Check the recording and source language.")
    return {
        "detected_language": info.language,
        "language_probability": info.language_probability,
        "duration_seconds": info.duration,
        "model": args.model,
        "device": args.device,
        "compute_type": args.compute_type,
    }, rows


class GoogleTranslator:
    """Best-effort public Google endpoint; not an official or guaranteed API."""

    def __init__(self, source: str, target: str, timeout: float = 12, retries: int = 2):
        self.source, self.target = source, target
        self.timeout, self.retries = timeout, retries
        self.rate_limited = False

    def translate(self, text: str) -> str:
        if self.rate_limited:
            raise TranslationError("Provider rate limit: retry this translation later.")
        query = urlencode({"client": "gtx", "sl": self.source, "tl": self.target, "dt": "t", "q": text})
        request = Request("https://translate.googleapis.com/translate_a/single?" + query,
                          headers={"User-Agent": "AudioTexto/" + VERSION})
        reason = "Provider request failed."
        for attempt in range(self.retries):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
                    raise ValueError("Unexpected response structure")
                parts = [part[0] for part in payload[0]
                         if isinstance(part, list) and part and isinstance(part[0], str)]
                translated = "".join(parts).strip()
                if not translated:
                    raise ValueError("Empty translation")
                return translated
            except HTTPError as exc:
                reason = f"Provider returned HTTP {exc.code}."
                exc.close()
                if exc.code == 429:
                    self.rate_limited = True
                    break
                if exc.code < 500:
                    break
            except (URLError, TimeoutError, OSError):
                reason = "Network, timeout, or TLS error while contacting the provider."
            except (ValueError, TypeError, IndexError):
                reason = "Provider returned an invalid or empty translation."
            if attempt + 1 < self.retries:
                time.sleep(min(2 ** attempt, 4))
        # Do not include the request URL: it contains the transcript text.
        raise TranslationError(reason)


def translate_segments(rows: list[SegmentLine], translator: GoogleTranslator) -> None:
    for index, row in enumerate(rows, 1):
        if row.translation_status == "complete" and row.translation.strip():
            continue
        print(f"Translating segment {index}/{len(rows)}...", flush=True)
        try:
            if not any(c.isalnum() for c in row.text):
                row.translation = row.text
            elif translator.source == translator.target:
                row.translation = row.text
            else:
                row.translation = translator.translate(row.text)
            row.translation_status = "complete"
            row.translation_error = None
        except TranslationError as exc:
            row.translation = ""
            row.translation_status = "failed"
            row.translation_error = str(exc)
            print(f"Warning: segment {index}: {exc}", file=sys.stderr, flush=True)


def output_paths(input_name: str, output_dir: Path, source: str, target: str) -> dict[str, Path]:
    stem = Path(input_name).stem
    return {
        "transcript": output_dir / f"{stem}.transcript.{source}.txt",
        "transcript_timestamps": output_dir / f"{stem}.transcript.{source}.timestamps.txt",
        "translation": output_dir / f"{stem}.translation.{target}.txt",
        "translation_timestamps": output_dir / f"{stem}.translation.{target}.timestamps.txt",
        "metadata": output_dir / f"{stem}.metadata.json",
    }


def check_outputs(paths: dict[str, Path], overwrite: bool) -> None:
    existing = [path.name for path in paths.values() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError("Output files already exist: " + ", ".join(existing) + ". Choose another output directory or use --overwrite.")


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8-sig", newline="\n",
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text + "\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def translation_content(row: SegmentLine) -> str:
    if row.translation_status == "complete":
        return row.translation
    return f"[TRANSLATION {row.translation_status.upper()}]"


def write_outputs(paths: dict[str, Path], metadata: dict, rows: list[SegmentLine]) -> None:
    metadata = dict(metadata, segment_count=len(rows), segments=[asdict(row) for row in rows])
    metadata["translation_complete"] = all(r.translation_status == "complete" for r in rows)
    metadata["translation_failed_count"] = sum(r.translation_status == "failed" for r in rows)
    metadata["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    for field, key in (("text", "transcript"), ("translation", "translation")):
        values = [r.text if field == "text" else translation_content(r) for r in rows]
        atomic_write(paths[key], "\n".join(values))
        timed = [f"[{format_timestamp(r.start)} -> {format_timestamp(r.end)}] {value}"
                 for r, value in zip(rows, values)]
        atomic_write(paths[key + "_timestamps"], "\n".join(timed))
    atomic_write(paths["metadata"], json.dumps(metadata, ensure_ascii=False, indent=2))


def load_checkpoint(path: Path) -> tuple[dict, list[SegmentLine]]:
    with path.open(encoding="utf-8-sig") as stream:
        metadata = json.load(stream)
    if metadata.get("schema_version") != 1:
        raise ValueError("Unsupported checkpoint. Use metadata generated by this repository version.")
    # Output names must not be able to escape the chosen directory.
    name = metadata.get("input_file", "")
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise ValueError("Checkpoint input_file must be a file name, not a path.")
    for key in ("detected_language", "target_language"):
        language_code(metadata[key])
    rows = [SegmentLine(**row) for row in metadata["segments"]]
    if not rows:
        raise ValueError("Checkpoint has no segments.")
    for row in rows:
        if (not isinstance(row.text, str) or not row.text.strip()
                or not isinstance(row.translation, str)
                or not math.isfinite(row.start) or not math.isfinite(row.end)
                or row.start < 0 or row.end < row.start
                or row.translation_status not in {"complete", "pending", "failed", "skipped"}):
            raise ValueError("Checkpoint contains an invalid segment.")
    return metadata, rows


def run(args: argparse.Namespace) -> int:
    if args.resume:
        args.resume = args.resume.expanduser().resolve()
        metadata, rows = load_checkpoint(args.resume)
        output_dir = (args.output_dir or args.resume.parent).expanduser().resolve()
        source, target = metadata["detected_language"], metadata["target_language"]
    else:
        args.input_file = args.input_file.expanduser().resolve()
        if not args.input_file.is_file():
            raise FileNotFoundError("Input audio/video file not found.")
        output_dir = (args.output_dir or args.input_file.parent).expanduser().resolve()
        # With auto detection, the source suffix is not known until transcription.
        if args.language != "auto":
            check_outputs(output_paths(args.input_file.name, output_dir, args.language, args.target_lang), args.overwrite)
        details, rows = transcribe_file(args)
        source, target = language_code(details["detected_language"]), args.target_lang
        metadata = dict(details, schema_version=1, script_version=VERSION,
                        input_file=args.input_file.name, target_language=target)
    paths = output_paths(metadata["input_file"], output_dir, source, target)
    if args.input_file and any(p.resolve() == args.input_file for p in paths.values()):
        raise ValueError("An output path would overwrite the input file. Choose another directory.")
    check_outputs(paths, args.overwrite)
    if args.no_translate:
        for row in rows:
            row.translation_status = "skipped"
    # Save the transcript and checkpoint before any external translation request.
    write_outputs(paths, metadata, rows)
    if not args.no_translate:
        print("Online translation sends transcript text to Google Translate.", flush=True)
        translator = GoogleTranslator(source, target, args.timeout, args.retries)
        translate_segments(rows, translator)
        write_outputs(paths, metadata, rows)
    failed = sum(row.translation_status == "failed" for row in rows)
    print(f"Finished: {len(rows)} segments; {failed} failed translations.")
    for key, path in paths.items():
        print(f"{key}: {path}")
    return 2 if failed else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        print("Interrupted. If a checkpoint exists, resume translation with --resume.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
