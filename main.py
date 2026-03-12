import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import projects
from app.api import chat
from app.api import analysis
from init_db import init_db

# DB 초기화 (서버 시작 시 자동 실행)
try:
    init_db()
    print("✅ DB 초기화 완료!")
except Exception as e:
    print(f"⚠️ DB 초기화 실패: {e}")

# FastAPI 앱 생성
# Java로 치면 Spring Boot 애플리케이션 시작점이에요
app = FastAPI(
    title="ProjectLens",
    description="AI 기반 프로젝트 자동 분석 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])


# 서버 정상 동작 확인용 API
@app.get("/")
async def root():
    return {"message": "ProjectLens API 정상 동작중 🚀"}


# 헬스체크 API
@app.get("/health")
async def health():
    return {"status": "ok"}

