"""Behavior tests; no model download or external requests are performed."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

import transcribe_translate as app


class TemporaryProject(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.rows = [app.SegmentLine(0, 1.5, "Hello."), app.SegmentLine(2, 4, "Good morning.")]
        self.metadata = {
            "schema_version": 1, "input_file": "sample with spaces.ogg",
            "detected_language": "en", "target_language": "es",
        }
        self.paths = app.output_paths(self.metadata["input_file"], self.root, "en", "es")


class ArgumentsAndPaths(unittest.TestCase):
    def test_missing_or_conflicting_inputs_are_rejected(self):
        for argv in ([], ["clip.ogg", "--resume", "clip.metadata.json"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    app.parse_args(argv)

    def test_english_model_rejects_non_english_or_auto_language(self):
        for language in ("es", "auto"):
            with self.subTest(language=language), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    app.parse_args(["clip.ogg", "--language", language])

    def test_multilingual_auto_is_accepted(self):
        args = app.parse_args(["clip.ogg", "--model", "small", "--language", "auto"])
        self.assertEqual(args.language, "auto")

    def test_invalid_values_are_rejected(self):
        for flags in (["--timeout", "nan"], ["--timeout", "0"], ["--retries", "0"],
                      ["--beam-size", "-1"], ["--target-lang", "../../file"]):
            with self.subTest(flags=flags), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    app.parse_args(["clip.ogg"] + flags)

    def test_timestamp_rounding_carries_to_next_minute(self):
        self.assertEqual(app.format_timestamp(59.9996), "00:01:00.000")

    def test_source_and_target_suffixes_are_dynamic(self):
        paths = app.output_paths("meeting.mp4", Path("results"), "es", "en")
        self.assertEqual(paths["transcript"].name, "meeting.transcript.es.txt")
        self.assertEqual(paths["translation"].name, "meeting.translation.en.txt")


class TranslationBehavior(unittest.TestCase):
    def response(self, payload):
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        return stream

    def test_provider_response_joins_all_chunks(self):
        with patch.object(app, "urlopen", return_value=self.response([[["Hola", "Hello"], [" mundo", " world"]]])) as request:
            self.assertEqual(app.GoogleTranslator("en", "es", timeout=7).translate("Hello world"), "Hola mundo")
        self.assertEqual(request.call_args.kwargs["timeout"], 7)

    def test_rate_limit_stops_subsequent_requests(self):
        error = HTTPError("https://example.invalid", 429, "Limit", {}, None)
        translator = app.GoogleTranslator("en", "es")
        with patch.object(app, "urlopen", side_effect=error) as request:
            for _ in range(2):
                with self.assertRaises(app.TranslationError):
                    translator.translate("Hello")
        self.assertEqual(request.call_count, 1)

    def test_server_error_is_retried_then_succeeds(self):
        error = HTTPError("https://example.invalid", 503, "Unavailable", {}, None)
        with patch.object(app, "time") as clock, patch.object(
            app, "urlopen", side_effect=[error, self.response([[["Hola", "Hello"]]])]
        ) as request:
            self.assertEqual(app.GoogleTranslator("en", "es").translate("Hello"), "Hola")
        self.assertEqual(request.call_count, 2)
        clock.sleep.assert_called_once()

    def test_network_failure_is_explicit_and_does_not_echo_text(self):
        with patch.object(app, "urlopen", side_effect=URLError("private request details")), patch.object(app, "time"):
            with self.assertRaises(app.TranslationError) as raised:
                app.GoogleTranslator("en", "es").translate("private speech")
        self.assertNotIn("private", str(raised.exception))

    def test_malformed_or_empty_responses_fail(self):
        for payload in ({"error": True}, [], [None], [[]], [[[None]]]):
            with self.subTest(payload=payload), patch.object(app, "urlopen", return_value=self.response(payload)):
                with self.assertRaises(app.TranslationError):
                    app.GoogleTranslator("en", "es", retries=1).translate("Hello")

    def test_failed_translation_is_not_presented_as_english_success(self):
        row = app.SegmentLine(0, 1, "Hello")
        translator = Mock(source="en", target="es")
        translator.translate.side_effect = app.TranslationError("Provider unavailable")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            app.translate_segments([row], translator)
        self.assertEqual(row.translation_status, "failed")
        self.assertEqual(row.translation, "")
        self.assertEqual(app.translation_content(row), "[TRANSLATION FAILED]")

    def test_same_text_can_be_a_valid_translation(self):
        row = app.SegmentLine(0, 1, "Piano")
        translator = Mock(source="en", target="es")
        translator.translate.return_value = "Piano"
        with contextlib.redirect_stdout(io.StringIO()):
            app.translate_segments([row], translator)
        self.assertEqual(row.translation_status, "complete")

    def test_completed_segments_are_not_requested_again(self):
        rows = [app.SegmentLine(0, 1, "Hello", "Hola", "complete"), app.SegmentLine(1, 2, "Bye")]
        translator = Mock(source="en", target="es")
        translator.translate.return_value = "Adios"
        with contextlib.redirect_stdout(io.StringIO()):
            app.translate_segments(rows, translator)
        translator.translate.assert_called_once_with("Bye")


class OutputAndResume(TemporaryProject):
    def test_all_exports_agree_with_segment_records(self):
        self.rows[0].translation = "Hola."
        self.rows[0].translation_status = "complete"
        self.rows[1].translation_status = "failed"
        app.write_outputs(self.paths, self.metadata, self.rows)
        loaded, rows = app.load_checkpoint(self.paths["metadata"])
        self.assertFalse(loaded["translation_complete"])
        self.assertEqual(loaded["translation_failed_count"], 1)
        self.assertEqual(self.paths["translation"].read_text(encoding="utf-8-sig"), "Hola.\n[TRANSLATION FAILED]\n")
        timed = self.paths["translation_timestamps"].read_text(encoding="utf-8-sig")
        self.assertIn("[00:00:02.000 -> 00:00:04.000] [TRANSLATION FAILED]", timed)
        self.assertEqual(rows[0].translation, "Hola.")
        self.assertNotIn(str(self.root), self.paths["metadata"].read_text(encoding="utf-8-sig"))

    def test_existing_outputs_require_explicit_overwrite(self):
        app.write_outputs(self.paths, self.metadata, self.rows)
        with self.assertRaises(FileExistsError):
            app.check_outputs(self.paths, False)
        app.check_outputs(self.paths, True)

    def test_checkpoint_rejects_path_traversal(self):
        self.metadata["input_file"] = "../private.ogg"
        app.write_outputs(self.paths, self.metadata, self.rows)
        with self.assertRaises(ValueError):
            app.load_checkpoint(self.paths["metadata"])

    def test_checkpoint_rejects_invalid_times(self):
        self.rows[0].end = -1
        app.write_outputs(self.paths, self.metadata, self.rows)
        with self.assertRaises(ValueError):
            app.load_checkpoint(self.paths["metadata"])

    def test_legacy_checkpoint_is_not_silently_imported(self):
        self.metadata["schema_version"] = 0
        app.write_outputs(self.paths, self.metadata, self.rows)
        with self.assertRaises(ValueError):
            app.load_checkpoint(self.paths["metadata"])

    def test_transcript_survives_translation_interruption(self):
        source = self.root / self.metadata["input_file"]
        source.touch()
        details = dict(detected_language="en", duration_seconds=4, language_probability=1)
        with patch.object(app, "transcribe_file", return_value=(details, self.rows)), patch.object(
            app, "translate_segments", side_effect=KeyboardInterrupt
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(app.main([str(source)]), 130)
        self.assertIn("Good morning.", self.paths["transcript"].read_text(encoding="utf-8-sig"))
        self.assertTrue(self.paths["metadata"].exists())

    def test_no_translate_never_calls_provider(self):
        source = self.root / self.metadata["input_file"]
        source.touch()
        details = dict(detected_language="en", duration_seconds=4, language_probability=1)
        with patch.object(app, "transcribe_file", return_value=(details, self.rows)), patch.object(
            app, "urlopen"
        ) as provider, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.main([str(source), "--no-translate"]), 0)
        provider.assert_not_called()
        self.assertIn("[TRANSLATION SKIPPED]", self.paths["translation"].read_text(encoding="utf-8-sig"))

    def test_resume_needs_no_original_audio_or_model(self):
        app.write_outputs(self.paths, self.metadata, self.rows)
        fake = Mock(source="en", target="es")
        fake.translate.return_value = "Translated"
        with patch.object(app, "transcribe_file") as transcription, patch.object(
            app, "GoogleTranslator", return_value=fake
        ), contextlib.redirect_stdout(io.StringIO()):
            status = app.main(["--resume", str(self.paths["metadata"]), "--overwrite"])
        self.assertEqual(status, 0)
        transcription.assert_not_called()
        metadata, _ = app.load_checkpoint(self.paths["metadata"])
        self.assertTrue(metadata["translation_complete"])

    def test_provider_failure_returns_partial_success_code(self):
        app.write_outputs(self.paths, self.metadata, self.rows)
        fake = Mock(source="en", target="es")
        fake.translate.side_effect = app.TranslationError("Unavailable")
        with patch.object(app, "GoogleTranslator", return_value=fake), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            status = app.main(["--resume", str(self.paths["metadata"]), "--overwrite"])
        self.assertEqual(status, 2)
        self.assertIn("Hello.", self.paths["transcript"].read_text(encoding="utf-8-sig"))

    def test_existing_outputs_are_checked_before_loading_model(self):
        source = self.root / self.metadata["input_file"]
        source.touch()
        app.write_outputs(self.paths, self.metadata, self.rows)
        with patch.object(app, "transcribe_file") as transcription, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(app.main([str(source)]), 1)
        transcription.assert_not_called()


class TranscriptionFallback(unittest.TestCase):
    def test_empty_vad_retries_without_filtering(self):
        fake_model = Mock()
        info = SimpleNamespace(language="en", language_probability=1, duration=1)
        fake_model.transcribe.side_effect = [([], info), ([SimpleNamespace(start=0, end=1, text=" Hello ")], info)]
        module = SimpleNamespace(WhisperModel=Mock(return_value=fake_model))
        args = app.parse_args(["clip.ogg"])
        with patch.dict("sys.modules", {"faster_whisper": module}), contextlib.redirect_stdout(io.StringIO()):
            _, rows = app.transcribe_file(args)
        self.assertEqual(rows[0].text, "Hello")
        self.assertTrue(fake_model.transcribe.call_args_list[0].kwargs["vad_filter"])
        self.assertFalse(fake_model.transcribe.call_args_list[1].kwargs["vad_filter"])

    def test_empty_audio_is_reported(self):
        fake_model = Mock()
        fake_model.transcribe.return_value = ([], SimpleNamespace())
        module = SimpleNamespace(WhisperModel=Mock(return_value=fake_model))
        with patch.dict("sys.modules", {"faster_whisper": module}), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "No speech"):
                app.transcribe_file(app.parse_args(["clip.ogg"]))


if __name__ == "__main__":
    unittest.main()
