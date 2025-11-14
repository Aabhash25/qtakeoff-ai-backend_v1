import pytesseract
import re
import tempfile
import subprocess
from PIL import Image
from io import BytesIO

def is_pdf_file_bytes(file_bytes):
    return file_bytes.startswith(b'%PDF')


def is_image_file_bytes(file_bytes):
    try:
        Image.open(BytesIO(file_bytes))
        return True
    except IOError:
        return False

def extract_text_from_image(image: Image.Image) -> str:
    return pytesseract.image_to_string(image)

def extract_scale_from_image(image: Image.Image) -> float | None:
    text = extract_text_from_image(image)
    cleaned_text = clean_text(text)

    pattern = re.compile(
        r'(?<!\d)(\d{1,2})\s*/\s*(\d{1,2})\s*(?:["”]\s*[=:]?\s*1\s*[\'][-–]?\d*["”]?)'
    )
    match = pattern.search(cleaned_text)
    if match:
        numerator = int(match.group(1))
        denominator = int(match.group(2))
        scale = numerator / denominator
        print(f"[Detected SCALE]: {numerator}/{denominator} = {scale}")
        return scale

    fallback_match = re.search(
        r"(?<!\d)(\d{1,2})\s*/\s*(\d{1,2})(?!\d)",
        cleaned_text
    )
    if fallback_match:
        numerator = int(fallback_match.group(1))
        denominator = int(fallback_match.group(2))
        scale = numerator / denominator
        print(f"[Fallback SCALE]: {numerator}/{denominator} = {scale}")
        return scale

    print("[Scale Not Found], defaulting to 1.1")
    return 1.1


def extract_scale_from_image_subprocess(image: Image.Image) -> float | None:
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            image.save(tmp_path)

        text = subprocess.check_output(["tesseract", tmp_path, "stdout"], stderr=subprocess.DEVNULL).decode()

        return extract_scale_from_text(text)

    except Exception as e:
        print(f"[Tesseract Subprocess OCR Failed]: {e}")
        return 1.1

    finally:
        import os
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)


def extract_scale_from_text(text: str) -> float | None:
    cleaned_text = clean_text(text)
    

    pattern = re.compile(
        r'(\d{1,2})\s*/\s*(\d{1,2})'  # Match 1/4, 3/8, etc.
    )
    match = pattern.search(cleaned_text)
    if match:
        numerator = int(match.group(1))
        denominator = int(match.group(2))
        scale = numerator / denominator
        print(f"[Detected SCALE]: {numerator}/{denominator} = {scale}")
        return scale

    print("[Scale Not Found], defaulting to 1.1")
    return 1.1

def clean_text(text: str) -> str:
    text = text.upper()
    text = text.replace('I', '1').replace('l', '1')
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('=L', '=1').replace('=I', '=1')
    text = re.sub(r'O(?=\d)', '0', text)  # O5 → 05
    return text