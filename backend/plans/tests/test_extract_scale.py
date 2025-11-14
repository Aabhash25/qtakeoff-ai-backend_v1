import unittest
from unittest.mock import patch, MagicMock
from plans.extract_scale import extract_scale_from_image, clean_text, extract_text_from_image
import unicodedata


def clean_text(text):
    text = unicodedata.normalize('NFKC', text)
    replacements = {
        '“': '"', '”': '"',
        '‘': "'", '’': "'",
        '–': '-', '—': '-',
        '‐': '-',
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text

class ExtractScaleTests(unittest.TestCase):
    
    def test_clean_text(self):
        dirty_text = '1/4“ = 1’–0”'
        print("Dirty text:")
        cleaned = clean_text(dirty_text)
        print("Cleaned text:")
        self.assertIn('1/4', cleaned)
        self.assertIn('"', cleaned)
        self.assertIn("1'", cleaned)

    @patch('plans.extract_scale.extract_text_from_image')
    def test_extract_scale_detected(self, mock_ocr):
        mock_ocr.return_value = '1/4" = 1\'-0"'
        fake_image = MagicMock()
        scale = extract_scale_from_image(fake_image)
        self.assertAlmostEqual(scale, 0.25)

    @patch('plans.extract_scale.extract_text_from_image')
    def test_extract_scale_fallback(self, mock_ocr):
        mock_ocr.return_value = '1 / 8 scale'
        fake_image = MagicMock()
        scale = extract_scale_from_image(fake_image)
        self.assertAlmostEqual(scale, 0.125)

    @patch('plans.extract_scale.extract_text_from_image')
    def test_extract_scale_not_found(self, mock_ocr):
        mock_ocr.return_value = 'No scale info here'
        fake_image = MagicMock()
        scale = extract_scale_from_image(fake_image)
        self.assertIsNone(scale)

    def test_extract_text_from_image_runs(self):
        # Only test that it runs and returns a string — no need to verify OCR output here
        from PIL import Image
        blank = Image.new('RGB', (100, 100), color='white')
        result = extract_text_from_image(blank)
        self.assertIsInstance(result, str)

# if __name__ == '__main__':
#     unittest.main()
