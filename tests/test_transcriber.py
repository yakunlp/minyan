from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory

from transcriber import (
    BusyError,
    MAX_UPLOAD_BYTES,
    ModelLoadError,
    create_model,
    TranscriptionService,
    validate_upload,
)


class FakeModel:
    def __init__(self, fail=False):
        self.fail = fail
        self.path = None

    def transcribe(self, path, **options):
        self.path = Path(path)
        assert self.path.read_bytes() == b"test audio"
        assert options == {
            "language": "en", "task": "transcribe", "beam_size": 5, "vad_filter": True
        }

        def segments():
            assert self.path.exists(), "Temporary audio must exist during inference"
            if self.fail:
                raise RuntimeError("decoder failed")
            yield SimpleNamespace(start=0.0, end=1.0, text=" Hello world. ")
            yield SimpleNamespace(start=1.0, end=2.0, text=" ")

        return segments(), SimpleNamespace(duration=2.0)


class TranscriberTests(unittest.TestCase):
    def test_local_model_does_not_use_network(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            model_path = root / "base.en"
            model_path.mkdir()
            for filename in ("config.json", "model.bin", "tokenizer.json"):
                (model_path / filename).write_bytes(b"test")
            with patch("transcriber.MODEL_ROOT", root), patch("faster_whisper.WhisperModel") as model:
                create_model("base.en")
                self.assertEqual(model.call_args.args, (str(model_path),))
                self.assertTrue(model.call_args.kwargs["local_files_only"])

    def test_model_download_error_is_specific(self):
        with TemporaryDirectory() as directory:
            with patch("transcriber.MODEL_ROOT", Path(directory)), patch(
                "faster_whisper.WhisperModel", side_effect=OSError("network unavailable")
            ) as model:
                with self.assertRaises(ModelLoadError) as caught:
                    create_model("base.en")
                self.assertFalse(model.call_args.kwargs["local_files_only"])
                self.assertIsInstance(caught.exception.__cause__, OSError)

    def test_validation(self):
        self.assertEqual(validate_upload("NEWS.MP3", 1), ".mp3")
        self.assertEqual(validate_upload("voice.m4a", MAX_UPLOAD_BYTES), ".m4a")
        for name, size in (("a.exe", 1), ("a.mp3", 0), ("a.wav", MAX_UPLOAD_BYTES + 1)):
            with self.subTest(name=name, size=size), self.assertRaises(ValueError):
                validate_upload(name, size)

    def test_transcription_progress_cache_and_cleanup(self):
        model = FakeModel()
        loaded = []

        def factory(name):
            loaded.append(name)
            return model

        service = TranscriptionService(factory)
        progress = []
        result = service.transcribe(b"test audio", "../../news.mp3", on_progress=progress.append)
        self.assertEqual(result.text, "Hello world.")
        self.assertEqual(result.duration, 2.0)
        self.assertEqual(len(result.segments), 1)
        self.assertEqual(progress, [0.5, 0.99])
        self.assertEqual(model.path.name, "audio.mp3")
        self.assertFalse(model.path.parent.exists())
        service.transcribe(b"test audio", "news.mp3")
        self.assertEqual(loaded, ["base.en"])
        service.transcribe(b"test audio", "news.mp3", "small.en")
        self.assertEqual(loaded, ["base.en", "small.en"])

    def test_failure_cleans_file_and_releases_lock(self):
        model = FakeModel(fail=True)
        service = TranscriptionService(lambda name: model)
        with self.assertRaises(RuntimeError):
            service.transcribe(b"test audio", "news.wav")
        self.assertFalse(model.path.parent.exists())
        model.fail = False
        self.assertEqual(service.transcribe(b"test audio", "news.wav").text, "Hello world.")

    def test_loading_failure_can_be_retried(self):
        attempts = []

        def factory(name):
            attempts.append(name)
            if len(attempts) == 1:
                raise RuntimeError("download failed")
            return FakeModel()

        service = TranscriptionService(factory)
        with self.assertRaises(RuntimeError):
            service.transcribe(b"test audio", "news.mp3")
        self.assertTrue(service.transcribe(b"test audio", "news.mp3").text)

    def test_busy_service(self):
        service = TranscriptionService()
        service._lock.acquire()
        try:
            with self.assertRaises(BusyError):
                service.transcribe(b"test audio", "news.mp3")
        finally:
            service._lock.release()

    def test_invalid_model(self):
        with self.assertRaises(ValueError):
            TranscriptionService().transcribe(b"test audio", "news.mp3", "invalid")


if __name__ == "__main__":
    unittest.main()