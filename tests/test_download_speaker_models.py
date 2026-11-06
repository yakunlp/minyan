import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from download_speaker_models import download_asset


class Response(io.BytesIO):
    headers = {"Content-Type": "application/octet-stream"}


class SpeakerDownloadTests(unittest.TestCase):
    def responses(self, size):
        return [Response(json.dumps({"assets": [{
            "name": "model.onnx", "size": size,
            "browser_download_url": "https://example.test/model",
            "url": "https://example.test/api/model",
        }]}).encode()), Response(b"model")]

    def test_download_and_atomic_replacement(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "model.onnx"
            with patch("download_speaker_models.urllib.request.urlopen", side_effect=self.responses(5)):
                download_asset("test", "model.onnx", path)
            self.assertEqual(path.read_bytes(), b"model")
            self.assertFalse(path.with_suffix(".onnx.part").exists())

    def test_wrong_size_does_not_replace_existing_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "model.onnx"
            path.write_bytes(b"previous")
            with patch("download_speaker_models.urllib.request.urlopen", side_effect=self.responses(6)):
                with self.assertRaisesRegex(RuntimeError, "Incomplete download"):
                    download_asset("test", "model.onnx", path)
            self.assertEqual(path.read_bytes(), b"previous")
            self.assertFalse(path.with_suffix(".onnx.part").exists())


if __name__ == "__main__":
    unittest.main()