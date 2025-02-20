import os

def train_tesseract(image_dir, label_dir, output_dir, lang='kor'):
    """Tesseract OCR 학습"""
    images = os.listdir(image_dir)
    for image in images:
        image_path = os.path.join(image_dir, image)
        label_path = os.path.join(label_dir, f"{os.path.splitext(image)[0]}.box")
        output_path = os.path.join(output_dir, os.path.splitext(image)[0])

        # Tesseract 학습 실행
        os.system(f"tesseract {image_path} {output_path} -l {lang} box.train")

if __name__ == "__main__":
    train_tesseract('./images', './labels', './generated', lang='kor')

