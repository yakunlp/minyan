import unittest

from phoneqr import DEFAULT_PORT, phone_url, qr_ascii, qr_png


class PhoneQRTests(unittest.TestCase):
    def test_returns_png_bytes(self):
        data = qr_png("http://192.168.1.23:8501")
        self.assertIsNotNone(data)
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_longer_url_is_also_encoded(self):
        data = qr_png("http://10.16.0.232:8501")
        self.assertIsNotNone(data)
        self.assertGreater(len(data), 100)

    def test_ascii_qr_uses_block_characters(self):
        art = qr_ascii("http://192.168.1.23:8501")
        self.assertIsNotNone(art)
        self.assertIn("\u2588", art)

    def test_phone_url_is_none_or_valid(self):
        url = phone_url(9999)
        if url is not None:
            self.assertTrue(url.startswith("http://"))
            self.assertTrue(url.endswith(":9999"))
        self.assertEqual(DEFAULT_PORT, 8501)


if __name__ == "__main__":
    unittest.main()

