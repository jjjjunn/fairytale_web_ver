from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_dir.models import Base
from models_dir.database import engine, init_db
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from controllers.users_controller import router as users_router
from controllers.babies_controller import router as babies_router
from ai_server import router as ai_router
import sys
import os
import logging

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Fairytale API",
    description="아이들을 위한 동화 생성 API",
    version="1.0.0"
)

# 세션 미들웨어 설정
app.add_middleware(
    SessionMiddleware,
    secret_key="your_secret_key",
    max_age=60 * 60, # 1시간 후 세션 만료
    same_site="lax", # same_site 없을 시 세션 쿠키가 인증 흐름 중 브라우저에서 차단될 수 있음
    https_only=False, # 테스트용
    session_cookie="session",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit 프론트엔드
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)  # 로깅 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logger = logging.getLogger(__name__)

# 라우터 등록
app.include_router(users_router, tags=["users"])
app.include_router(ai_router, tags=["ai"])
app.include_router(babies_router, tags=["babies"])

# 시작 시 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        logger.info("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        raise

# 시스템 정보 로깅
logger.debug(f"System encoding: {sys.getdefaultencoding()}")
logger.debug(f"Current working directory: {os.getcwdb()}")
logger.debug(f"Database URL: {os.environ.get('DATABASE_URL')}")

# 에러 핸들링 추가
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )