import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bbc
from transcriber import TranscriptionService


LISTING_HTML = """
<div class="programme programme--radio programme--episode" data-pid="w111aaa111aaa111">
<div class="programme programme--radio programme--episode" data-pid="w222bbb222bbb222">
<div class="programme programme--radio programme--episode" data-pid="w111aaa111aaa111">
<div class="brand" data-pid="p002vsmz">
"""

PROGRAMME_JSON = {
    "programme": {
        "display_title": {"title": "BBC News", "subtitle": "03/11/2026 16:01 GMT"},
        "first_broadcast_date": "2026-11-03T16:00:00Z",
        "versions": [{"pid": "vpid123"}],
    }
}
MEDIA_JSON = {
    "media": [
        {
            "kind": "audio",
            "connection": [
                {"protocol": "http", "transferFormat": "hls", "href": "http://insecure/a.m3u8"},
                {"protocol": "https", "transferFormat": "hls", "href": "https://example/a.m3u8"},
            ],
        }
    ]
}


class FakeUrlModel:
    def __init__(self):
        self.source = None

    def transcribe(self, source, **options):
        self.source = source
        return iter([SimpleNamespace(start=0.0, end=1.0, text=" Hello world. ")]), SimpleNamespace(
            duration=1.0
        )


class BBCTests(unittest.TestCase):
    def test_parse_episode_pids_order_and_dedup(self):
        self.assertEqual(
            bbc.parse_episode_pids(LISTING_HTML),
            ["w111aaa111aaa111", "w222bbb222bbb222"],
        )

    def test_parse_episode_pids_empty(self):
        self.assertEqual(bbc.parse_episode_pids("<html></html>"), [])

    def test_select_audio_href_prefers_https_hls(self):
        self.assertEqual(bbc.select_audio_href(MEDIA_JSON), "https://example/a.m3u8")

    def test_select_audio_href_fallback_and_error(self):
        fallback = {
            "media": [
                {"kind": "audio", "connection": [{"protocol": "https", "href": "https://x/a.mp4"}]}
            ]
        }
        self.assertEqual(bbc.select_audio_href(fallback), "https://x/a.mp4")
        with self.assertRaises(bbc.BBCError):
            bbc.select_audio_href({"media": [{"kind": "video", "connection": []}]})

    def test_latest_episode_resolves_stream(self):
        seen = []

        def fake_json(url):
            seen.append(url)
            return MEDIA_JSON if "mediaselector" in url else PROGRAMME_JSON

        with patch("bbc._get_text", return_value=LISTING_HTML), patch(
            "bbc._get_json", side_effect=fake_json
        ):
            episode = bbc.latest_episode()
        self.assertEqual(episode.pid, "w111aaa111aaa111")
        self.assertEqual(episode.title, "03/11/2026 16:01 GMT")
        self.assertEqual(episode.stream_url, "https://example/a.m3u8")
        self.assertIn("vpid/vpid123", episode.download_url)
        self.assertTrue(episode.download_url.endswith(".mp3"))
        self.assertTrue(any("vpid/vpid123/format/json" in url for url in seen))

    def test_build_episode_uses_version_with_media(self):
        programme = {
            "programme": {
                "display_title": {"title": "BBC News", "subtitle": "04/11/2026 14:01 GMT"},
                "first_broadcast_date": "2026-11-04T14:00:00Z",
                "versions": [{"pid": "vfirst"}, {"pid": "vsecond"}],
            }
        }

        def fake_json(url):
            if "mediaselector" in url:
                if "vfirst" in url:
                    raise RuntimeError("404 for the first version")
                return MEDIA_JSON
            return programme

        with patch("bbc._get_json", side_effect=fake_json):
            episode = bbc.build_episode("w999")
        self.assertEqual(episode.title, "04/11/2026 14:01 GMT")
        self.assertEqual(episode.stream_url, "https://example/a.m3u8")
        self.assertIn("vpid/vsecond", episode.download_url)
        self.assertTrue(episode.download_url.endswith(".mp3"))

    def test_latest_episode_without_episodes_raises(self):
        with patch("bbc._get_text", return_value="<html></html>"):
            with self.assertRaises(bbc.BBCError):
                bbc.latest_episode()

    def test_latest_episode_network_error_is_wrapped(self):
        with patch("bbc._get_text", side_effect=OSError("offline")):
            with self.assertRaises(bbc.BBCError):
                bbc.latest_episode()

    def test_transcribe_source_passes_url_to_model(self):
        model = FakeUrlModel()
        service = TranscriptionService(lambda name: model)
        result = service.transcribe_source("https://example/a.m3u8")
        self.assertEqual(model.source, "https://example/a.m3u8")
        self.assertEqual(result.text, "Hello world.")

    def test_transcribe_source_rejects_empty(self):
        with self.assertRaises(ValueError):
            TranscriptionService().transcribe_source("")


class BBCStoreTests(unittest.TestCase):
    def episode(self):
        return bbc.BBCEpisode(
            pid="w1730nkz05yjldd",
            title="04/11/2026 14:01 GMT",
            broadcast="2026-11-04T14:00:00Z",
            stream_url="https://example/hls.m3u8",
            download_url="https://example/audio.mp3",
        )

    def test_episode_slug_uses_broadcast_date_and_time(self):
        self.assertEqual(bbc.episode_slug(self.episode()), "2026-11-04_1400")

    def test_episode_slug_falls_back_to_title(self):
        episode = bbc.BBCEpisode("w1", "BBC News", "", "", "")
        self.assertEqual(bbc.episode_slug(episode), "BBC-News")

    def test_download_audio_saves_named_file(self):
        with TemporaryDirectory() as directory:
            target = Path(directory)
            with patch("bbc.urllib.request.urlopen", return_value=io.BytesIO(b"audio")):
                path = bbc.download_audio(self.episode(), target)
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes(), b"audio")
            self.assertIn("2026-11-04_1400", path.name)
            self.assertIn("w1730nkz05yjldd", path.name)
            self.assertEqual(list(target.glob("*.part")), [])

    def test_download_audio_rejects_empty(self):
        with TemporaryDirectory() as directory:
            target = Path(directory)
            with patch("bbc.urllib.request.urlopen", return_value=io.BytesIO(b"")):
                with self.assertRaises(bbc.BBCError):
                    bbc.download_audio(self.episode(), target)
            self.assertEqual(list(target.glob("*.mp3")), [])

    def test_save_transcript_states_episode(self):
        with TemporaryDirectory() as directory:
            path = bbc.save_transcript(self.episode(), "Hello world.", Path(directory))
            text = path.read_text(encoding="utf-8")
        self.assertTrue(path.name.endswith(".txt"))
        self.assertIn("04/11/2026 14:01 GMT", text)
        self.assertIn("w1730nkz05yjldd", text)
        self.assertIn("Hello world.", text)


if __name__ == "__main__":
    unittest.main()
