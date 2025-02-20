from flask import Flask, request, jsonify
from ocr_model.tesseract import OCRProcessor
from database import Database
from datetime import datetime
import os
import cv2
import re

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ocr_processor = OCRProcessor(lang='kor')
db = Database()

def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # 대비 조정 (명암 강조)
    img = cv2.equalizeHist(img)

    # 해상도 증가
    height, width = img.shape[:2]
    img = cv2.resize(img, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)

    # 가우시안 블러 적용하여 노이즈 제거
    img = cv2.GaussianBlur(img, (5, 5), 0)

    # 적응형 이진화 적용
    img_bin = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    return img_bin


def is_more_than_three_years(date_str):
    """3년 이상 거주 여부 판단"""
    move_in_date = datetime.strptime(date_str, "%Y-%m-%d")
    current_date = datetime.now()
    diff_years = (current_date - move_in_date).days / 365
    return diff_years >= 3


def remove_unwanted_text(text):
    # 불필요한 텍스트 제거
    cleaned_text = re.sub(r'※[\s\S]*?확인하여야\s+합니다\.', '', text)
    cleaned_text = re.sub(r'인천광역시\s+계양구청[\s\S]*?확인하여야\s+합니다\.', '', cleaned_text)
    return cleaned_text


def clean_date_format(text):
    """
    잘못된 날짜 형식 수정 (예: '2025년 월 114일' -> '2025년 01월 14일')
    """
    text = re.sub(r'(\d{4}년\s*)월\s*(\d{3,4})일', r'\1월 14일', text)  # 예시로 수정
    text = re.sub(r'(\d{4}년\s*)월\s*(\d{1})일', r'\1월 14일', text)  # 1일 수정 예시
    return text


def extract_move_in_date(text):
    # 날짜 형식 수정
    text = clean_date_format(text)
    print(f"📌 정리된 텍스트:\n{text}")  # 수정된 텍스트 로그 출력

    # YYYY-MM-DD 형식 찾기
    match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if match:
        return match.group(1)

    # "YYYY년 MM월 DD일" 형식 찾기
    match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', text)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    return None


def extract_last_move_in_date(text):
    # YYYY-MM-DD 및 YYYY년 MM월 DD일 형식 찾기
    pattern = r'(\d{4}-\d{2}-\d{2})|(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'

    # 현재 연도 가져오기
    current_year = datetime.now().year

    # 모든 날짜 찾기
    matches = re.findall(pattern, text)
    
    if matches:
        # 날짜 변환하여 리스트에 저장
        date_list = []
        for match in matches:
            try:
                if match[0]:  # YYYY-MM-DD 형식
                    date_obj = datetime.strptime(match[0], "%Y-%m-%d")
                else:  # YYYY년 MM월 DD일 형식
                    year, month, day = match[1], match[2], match[3]
                    date_obj = datetime.strptime(f"{year}-{int(month):02d}-{int(day):02d}", "%Y-%m-%d")

                # 🔹 비정상적인 미래 날짜 필터링 (현재 연도 + 5년 초과 제거)
                if date_obj.year <= current_year + 5:
                    date_list.append(date_obj)

            except ValueError:
                continue  # 날짜 변환 오류 방지

        # 최신 날짜 반환
        if date_list:
            last_date = max(date_list).strftime("%Y-%m-%d")
            return last_date

    return None




@app.route('/ocr', methods=['POST'])
def ocr():
    """OCR 실행 및 디버깅"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

    # 업로드 폴더가 없으면 생성
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(file_path)

    try:
        # OCR 텍스트 추출
        text = ocr_processor.process_image(file_path)
        print(f"📌 OCR 원본 결과:\n{text}", flush=True)  # 원본 OCR 결과를 로그에 출력

        # 불필요한 텍스트 정리
        text = remove_unwanted_text(text)
        print(f"📌 정리된 OCR 텍스트:\n{text}", flush=True)  # 정리된 텍스트 출력

        if not text:
            return jsonify({'error': 'No text found in the image'}), 400

# 날짜 추출 (마지막 전입 신고일)
        move_in_date = extract_last_move_in_date(text)  # 마지막 전입 신고일 추출
        print(f"📌 최종 추출된 전입 신고일: {move_in_date}", flush=True)  # 최종 추출된 날짜 로그 출력

        if move_in_date:
            is_certified = is_more_than_three_years(move_in_date)
            return jsonify({
                'move_in_date': move_in_date,
                'is_certified': is_certified
            })
        else:
            return jsonify({'error': 'Unable to extract move-in date', 'ocr_text': text})


    except Exception as e:
        print(f"❌ OCR 처리 중 오류 발생: {e}")
        return jsonify({'error': 'OCR 처리 중 오류 발생', 'message': str(e)}), 500


@app.route('/register', methods=['POST'])
def register():
    """회원가입 처리"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    certified = data.get('certified', False)  # OCR 인증 여부

    if not (username and email and password):
        return jsonify({'error': 'Missing required fields'}), 400

    success, message = db.register_user(username, email, password, certified)
    
    if success:
        return jsonify({'message': message}), 201
    else:
        return jsonify({'error': message}), 409


if __name__ == '__main__':
    db.init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
