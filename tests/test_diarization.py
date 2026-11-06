from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from diarization import (
    DiarizationError, SpeakerDiarizer, SpeakerTurn, UNKNOWN_SPEAKER, align_words,
)
from transcriber import Transcript, TranscriptSegment, TranscriptionService


class DiarizationTests(unittest.TestCase):
    def test_alignment_chronological_labels_and_unknown(self):
        turns = [SpeakerTurn(2, 4, 0), SpeakerTurn(0, 2, 7)]
        words = [SimpleNamespace(start=s, end=e, word=t) for s, e, t in (
            (0, 1, "Hello"), (2, 3, " Hi"), (4, 5, " silence"), (1.5, 2.5, " overlap")
        )]
        aligned = align_words(words, turns)
        self.assertEqual([r[3] for r in aligned], [
            "Speaker 1", "Speaker 2", UNKNOWN_SPEAKER, UNKNOWN_SPEAKER
        ])
        self.assertEqual("".join(r[2] for r in aligned), "Hello Hi silence overlap")

    def test_missing_models(self):
        with TemporaryDirectory() as directory, patch("diarization.SPEAKER_MODEL_DIR", Path(directory)):
            with self.assertRaises(DiarizationError):
                SpeakerDiarizer()

    def test_text_labels_and_plain_compatibility(self):
        transcript = Transcript((TranscriptSegment(0, 1, "Hi", "Speaker 1"),), 1)
        self.assertEqual(transcript.text, "[Speaker 1] Hi")
        self.assertEqual(Transcript((TranscriptSegment(0, 1, "Hi"),), 1).text, "Hi")

    def test_service_word_splitting_cache_and_cleanup(self):
        calls = []
        paths = []
        words = [SimpleNamespace(start=s, end=e, word=t) for s, e, t in (
            (0, 0.5, "Hello"), (0.5, 1, " there."), (1, 2, " Welcome.")
        )]
        model = SimpleNamespace(transcribe=lambda audio, **kwargs: (
            self.assertTrue(kwargs["word_timestamps"]) or iter([
                SimpleNamespace(start=0, end=2, text="Hello there. Welcome.", words=words)
            ]), SimpleNamespace(duration=2)
        ))

        def decode(path, **kwargs):
            paths.append(Path(path))
            self.assertTrue(paths[-1].exists())
            return [0.0] * 100

        def factory(count):
            calls.append(count)
            return SimpleNamespace(process=lambda audio, on_progress: [
                SpeakerTurn(0, 1, 8), SpeakerTurn(1, 2, 2)
            ])

        service = TranscriptionService(lambda name: model, factory)
        with patch("faster_whisper.audio.decode_audio", side_effect=decode):
            result = service.transcribe(b"audio", "a.wav", distinguish_speakers=True)
            self.assertEqual(result.text, "[Speaker 1] Hello there.\n[Speaker 2] Welcome.")
            self.assertFalse(paths[-1].exists())
            service.transcribe(b"audio", "a.wav", distinguish_speakers=True)
            self.assertEqual(calls, [None])
            service.transcribe(b"audio", "a.wav", distinguish_speakers=True, num_speakers=2)
            self.assertEqual(calls, [None, 2])

    def test_diarization_failure_unlocks_service(self):
        def factory(count):
            raise DiarizationError("unavailable")

        service = TranscriptionService(diarizer_factory=factory)
        for _ in range(2):
            with self.assertRaises(DiarizationError):
                service.transcribe(b"audio", "a.wav", distinguish_speakers=True)
        self.assertFalse(service._lock.locked())

    def test_invalid_speaker_count(self):
        for count in (0, 11, True, 2.5):
            with self.assertRaises(ValueError):
                TranscriptionService().transcribe(b"audio", "a.wav", num_speakers=count)


if __name__ == "__main__":
    unittest.main()