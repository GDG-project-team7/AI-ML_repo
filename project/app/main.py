from flask import Flask, request, jsonify
from ocr_model.tesseract import OCRProcessor
import requests
import os
import re
from datetime import datetime

app = Flask(__name__)

# 🔹 서버에서 저장된 이미지를 가져오는 API (서버팀이 제공해야 함)
SERVER_IMAGE_FETCH_URL = "https://server-team-api.com/get_image"
# 🔹 OCR 결과를 서버에 저장하는 API (서버팀이 제공해야 함)
SERVER_SAVE_OCR_URL = "https://server-team-api.com/save_ocr_result"

ocr_processor = OCRProcessor(lang='kor')

def extract_last_move_in_date(text):
    """OCR에서 날짜 추출"""
    pattern = r'(\d{4}-\d{2}-\d{2})|(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'
    current_year = datetime.now().year

    matches = re.findall(pattern, text)
    if matches:
        date_list = []
        for match in matches:
            try:
                if match[0]:  # YYYY-MM-DD 형식
                    date_obj = datetime.strptime(match[0], "%Y-%m-%d")
                else:  # YYYY년 MM월 DD일 형식
                    year, month, day = match[1], match[2], match[3]
                    date_obj = datetime.strptime(f"{year}-{int(month):02d}-{int(day):02d}", "%Y-%m-%d")

                if date_obj.year <= current_year + 5:
                    date_list.append(date_obj)

            except ValueError:
                continue  

        if date_list:
            last_date = max(date_list).strftime("%Y-%m-%d")
            return last_date
    return None


@app.route('/ocr', methods=['POST'])
def ocr():
    """서버에서 저장된 이미지를 가져와 OCR 실행 후 결과 반환"""
    data = request.json
    image_id = data.get("image_id")

    if not image_id:
        return jsonify({'error': 'No image_id provided'}), 400

    # 🔹 서버에서 이미지 가져오기 요청
    response = requests.get(f"{SERVER_IMAGE_FETCH_URL}?image_id={image_id}")

    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch image from server'}), 500

    # 이미지 파일 저장
    image_path = f"static/{image_id}.jpg"
    os.makedirs("static", exist_ok=True)
    with open(image_path, "wb") as f:
        f.write(response.content)

    try:
        # 🔍 OCR 실행
        text = ocr_processor.process_image(image_path)
        print(f"📌 OCR 원본 결과:\n{text}", flush=True)

        # 🔹 OCR 결과를 서버에 저장
        save_response = requests.post(SERVER_SAVE_OCR_URL, json={'image_id': image_id, 'ocr_text': text})

        if save_response.status_code == 200:
            return jsonify({'message': 'OCR completed', 'ocr_text': text})
        else:
            return jsonify({'error': 'Failed to save OCR result', 'response': save_response.text}), 500

    except Exception as e:
        print(f"❌ OCR 처리 중 오류 발생: {e}")
        return jsonify({'error': 'OCR 처리 중 오류 발생', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
