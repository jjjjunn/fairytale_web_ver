from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from contextlib import contextmanager

load_dotenv()  # .env 파일에서 환경변수 로드
#load_dotenv(dotenv_path='G:/my_fastapi/fairytale/.env')

# 데이터베이스 URL 설정 (PostgreSQL)
# DATABASE_URL = os.getenv('POSTGRESQL_URL')
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/fairy_db"

# 환경 변수 검사
if not DATABASE_URL:
    raise ValueError("DATABASE_URL이 설정되지 않았습니다! .env 파일을 확인해 주세요.")
else:
    print("DATABASE_URL from .env:", DATABASE_URL)
    print(type(DATABASE_URL))

# 엔진 생성
engine = create_engine(DATABASE_URL)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

def init_db():
    """데이터베이스 테이블 초기화"""
    try:
        # ⭐ models.py 파일에서 모든 모델 import
        print("📦 models.py에서 모델들을 import 중...")
        
        import models_dir.models  # models.py 파일 import
        print("✅ models.py import 완료")
        
        # 모든 모델의 테이블 생성
        print("🔨 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        print("✅ 테이블 생성 완료!")
        
        # 생성된 테이블 목록 출력
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 생성된 테이블 목록: {tables}")
        
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        raise


# 데이터베이스 연결 테스트
try:
    with engine.connect() as connection:
        print("✅ 데이터베이스 연결 성공!")
        init_db()  # 테이블 생성 함수 호출
except Exception as e:
    import traceback
    print("❌ 데이터베이스 연결 실패")
    traceback.print_exc()  # 전체 에러 트레이스백을 안전하게 출력

# 세션 컨텍스트 관리자
@contextmanager
def get_db():
    # 데이터베이스 세션 컨텍스트 관리자
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()