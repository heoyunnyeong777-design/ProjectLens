FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# CPU 전용 torch 먼저 설치 (용량 대폭 감소: 2.5GB → 200MB)
RUN pip install --no-cache-dir \
    torch==2.3.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# 나머지 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 포트
EXPOSE 8000

# 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
