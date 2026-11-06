import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import download_model


class DownloadTests(unittest.TestCase):
    def metadata(self, corrupt=False):
        return json.dumps({
            "Success": True,
            "Data": {"Files": [
                {"Path": name, "Size": 4, "Sha256": (
                    "0" * 64 if corrupt else hashlib.sha256(b"test").hexdigest()
                ), "Revision": "test-revision"}
                for name in download_model.FILES
            ]},
        }).encode()

    def test_verified_download_and_skip(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)

            def response(url, **kwargs):
                if "/files?" in url:
                    return io.BytesIO(self.metadata())
                self.assertIn("Revision=test-revision", url)
                return io.BytesIO(b"test")

            with patch("download_model.MODEL_ROOT", root), patch(
                "download_model.urllib.request.urlopen", side_effect=response
            ) as request:
                download_model.main()
                self.assertEqual(request.call_count, 5)
                download_model.main()
                self.assertEqual(request.call_count, 6)
                for name in download_model.FILES:
                    self.assertEqual((root / "base.en" / name).read_bytes(), b"test")

    def test_corrupt_file_is_not_installed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("download_model.MODEL_ROOT", root), patch(
                "download_model.urllib.request.urlopen",
                side_effect=[io.BytesIO(self.metadata(corrupt=True)), io.BytesIO(b"test")],
            ):
                with self.assertRaisesRegex(RuntimeError, "Integrity check failed"):
                    download_model.main()
                self.assertEqual(list((root / "base.en").iterdir()), [])


if __name__ == "__main__":
    unittest.main()