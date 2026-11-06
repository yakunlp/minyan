from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from streamlit.testing.v1 import AppTest

from bbc import BBCEpisode
from transcriber import Transcript, TranscriptSegment


APP = Path(__file__).resolve().parents[1] / "app.py"


class WebAppTests(unittest.TestCase):
    def test_initial_page_and_model_selection(self):
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(app.button[0].disabled)
        self.assertEqual(app.selectbox[0].value, "base.en")
        # Speaker separation must be off by default now.
        self.assertFalse(app.checkbox[0].value)
        # The phone hint is rendered as markdown when an IP is found, otherwise
        # as a caption; either way it must mention 手机访问.
        hint = " ".join(e.value for e in app.markdown) + " " + " ".join(
            e.value for e in app.caption
        )
        self.assertIn("手机访问", hint)
        app.selectbox[0].select("small.en").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.selectbox[0].value, "small.en")

    def test_result_editing_and_reset(self):
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        app.session_state["transcript"] = Transcript(
            (TranscriptSegment(0.0, 1.0, "Hello world."),), 1.0
        )
        app.session_state["result_name"] = "news.txt"
        app.session_state["elapsed"] = 1.0
        app.session_state["editable_text"] = "Hello world."
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.text_area[0].value, "Hello world.")
        app.text_area[0].input("Corrected text.").run()
        self.assertEqual(app.text_area[0].value, "Corrected text.")
        app.selectbox[0].select("small.en").run()
        self.assertEqual(len(app.text_area), 0)
        self.assertEqual(len(app.exception), 0)

    def test_speaker_controls_and_result_reset(self):
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        app.checkbox[0].check().run()
        self.assertTrue(app.checkbox[0].value)
        self.assertEqual(app.selectbox[1].value, "自动估计")
        app.session_state["transcript"] = Transcript(
            (TranscriptSegment(0, 1, "Hello.", "Speaker 1"),), 1
        )
        app.session_state["result_name"] = "news.txt"
        app.session_state["elapsed"] = 1.0
        app.session_state["editable_text"] = "[Speaker 1] Hello."
        app.run()
        self.assertEqual(app.text_area[0].value, "[Speaker 1] Hello.")
        app.selectbox[1].select(2).run()
        self.assertEqual(len(app.text_area), 0)
        app.checkbox[0].uncheck().run()
        self.assertEqual(len(app.selectbox), 1)
        self.assertEqual(len(app.exception), 0)

    def test_fetched_episode_info_is_shown(self):
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        app.session_state["bbc_episode"] = BBCEpisode(
            pid="w1730nkz05yjldd",
            title="04/11/2026 14:01 GMT",
            broadcast="2026-11-04T14:00:00Z",
            stream_url="https://example/hls.m3u8",
            download_url="https://example/audio.mp3",
        )
        app.run()
        self.assertEqual(len(app.exception), 0)
        shown = " ".join(element.value for element in app.markdown)
        self.assertIn("04/11/2026 14:01 GMT", shown)
        self.assertIn("w1730nkz05yjldd", shown)
        app.selectbox[0].select("small.en").run()
        self.assertEqual(len(app.exception), 0)
        shown = " ".join(element.value for element in app.markdown)
        self.assertNotIn("w1730nkz05yjldd", shown)

    def test_saved_episode_audio_and_text_paths_are_shown(self):
        with TemporaryDirectory() as directory:
            audio = Path(directory) / "BBC-News-2026-11-04_1400-w1730nkz05yjldd.mp3"
            audio.write_bytes(b"ID3")
            text = Path(directory) / "BBC-News-2026-11-04_1400-w1730nkz05yjldd.txt"

            app = AppTest.from_file(str(APP), default_timeout=20).run()
            app.session_state["bbc_episode"] = BBCEpisode(
                pid="w1730nkz05yjldd",
                title="04/11/2026 14:01 GMT",
                broadcast="2026-11-04T14:00:00Z",
                stream_url="https://example/hls.m3u8",
                download_url="https://example/audio.mp3",
            )
            app.session_state["bbc_audio_path"] = str(audio)
            app.session_state["bbc_text_path"] = str(text)
            app.run()
            self.assertEqual(len(app.exception), 0)
            shown = " ".join(element.value for element in app.markdown)
            self.assertIn(str(audio), shown)
            self.assertIn(str(text), shown)
            self.assertIn("04/11/2026 14:01 GMT", shown)
            # A saved MP3 exposes exactly one download button (the TXT button
            # only exists when a transcript is present).
            self.assertEqual(len(app.download_button), 1)


if __name__ == "__main__":
    unittest.main()