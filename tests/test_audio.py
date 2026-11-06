"""Real decoder compatibility check; no model download needed."""
import io
import unittest
import wave

from faster_whisper.audio import decode_audio


class AudioCompatibilityTests(unittest.TestCase):
    def test_decode_pcm_wav_with_installed_pyav(self):
        audio = io.BytesIO()
        with wave.open(audio, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            output.writeframes(b"\0\0" * 16000)
        audio.seek(0)
        decoded = decode_audio(audio, sampling_rate=16000)
        self.assertEqual(len(decoded), 16000)
        self.assertTrue((decoded == 0).all())


if __name__ == "__main__":
    unittest.main()