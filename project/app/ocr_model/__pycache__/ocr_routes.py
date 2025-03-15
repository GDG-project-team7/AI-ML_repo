import requests
import os
from flask import Blueprint, request, jsonify
from ocr_model.tesseract import OCRProcessor  # OCR 기능을 위한 클래스

ocr_blueprint = Blueprint('ocr', __name__)
ocr_processor = OCRProcessor(lang='kor')

# 🔹 서버에서 저장된 이미지를 가져오는 API (서버팀이 제공해야 함)
SERVER_IMAGE_FETCH_URL = "https://server-team-api.com/get_image"
# 🔹 OCR 결과를 서버에 저장하는 API (서버팀이 제공해야 함)
SERVER_SAVE_OCR_URL = "https://server-team-api.com/save_ocr_result"

@ocr_blueprint.route('/ocr', methods=['POST'])
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
    os.makedirs("static", exist_ok=True)  # 폴더 없으면 생성
    with open(image_path, "wb") as f:
        f.write(response.content)

    try:
        # 🔍 OCR 실행
        text = ocr_processor.process_image(image_path)
        print(f"📌 OCR 결과:\n{text}", flush=True)

        # 🔹 OCR 결과를 서버에 저장
        save_response = requests.post(SERVER_SAVE_OCR_URL, json={'image_id': image_id, 'ocr_text': text})

        if save_response.status_code == 200:
            return jsonify({'message': 'OCR completed', 'ocr_text': text})
        else:
            return jsonify({'error': 'Failed to save OCR result', 'response': save_response.text}), 500

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return jsonify({'error': 'OCR 처리 중 오류 발생', 'message': str(e)}), 500
