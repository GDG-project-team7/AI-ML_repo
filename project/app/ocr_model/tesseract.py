import pytesseract
from PIL import Image
import re
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))



class OCRProcessor:
    def __init__(self, lang='kor'):
        self.lang = lang

    def process_image(self, image_path):
        """이미지에서 텍스트 추출"""
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=self.lang)
        return text

    def extract_move_in_date(self, text):
        """전입 신고일 추출"""
        match = re.search(r'(\d{4}-\d{2}-\d{2}).*전입', text)
        return match.group(1) if match else None
