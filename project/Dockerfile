# 1. Python 3.9 이미지 사용
FROM python:3.9

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 프로젝트 파일 개별 복사 (파일 누락 방지)
COPY main.py /app/
COPY requirements.txt /app/
COPY . /app/

# 4. Tesseract OCR 설치
RUN apt-get update && apt-get install -y tesseract-ocr

# 5. Python 패키지 설치
RUN pip install --no-cache-dir -r /app/requirements.txt

# 6. 실행 명령 수정 (명확한 경로 지정)
CMD ["python", "/app/main.py"]

