from fastapi import Request, Depends, HTTPException, APIRouter, BackgroundTasks
from sqlalchemy.orm import Session
from models_dir.models import User, Baby, Story # 모델 import
from scheme_files.babies_schemes import CreateBaby
import logging
import re
from controllers.dependencies import get_db
from datetime import date, timedelta
import streamlit as st
import requests
from dotenv import load_dotenv
import os

router = APIRouter()

# .env 파일에서 환경 변수 로드
load_dotenv()
API_URL = os.getenv("API_URL")

if not API_URL:
    st.error("API_URL 환경 변수가 설정되지 않았습니다!")
    logging.error("API_URL 환경 변수가 설정되지 않았습니다!")
    st.stop()


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 아이 추가
@router.post("/babies/create_baby")
async def create_baby(baby_data: CreateBaby, db: Session = Depends(get_db)):
    try:
        logger.info(f"아이 정보 추가 요청: {baby_data}")
        
        # 사용자 존재 확인
        user = db.query(User).filter(User.id == baby_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # 중복 이름 체크
        existing_baby = db.query(Baby).filter(
            Baby.user_id == baby_data.user_id,
            Baby.baby_name == baby_data.baby_name
        ).first()
        
        if existing_baby:
            raise HTTPException(status_code=400, detail="동일한 아이 이름이 이미 존재합니다.")

        # 새 아기 정보 생성
        new_baby = Baby(
            user_id=baby_data.user_id,
            baby_name=baby_data.baby_name,
            baby_gender=baby_data.baby_gender,
            baby_bday=baby_data.baby_bday
        )
        
        db.add(new_baby)
        db.commit()
        db.refresh(new_baby)
        
        return {
            "message": "아이 정보가 추가되었습니다.",
            "baby": {
                "id": new_baby.id,
                "name": new_baby.baby_name,
                "gender": new_baby.baby_gender,
                "bday": str(new_baby.baby_bday)
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"아이 추가 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 아이 정보 조회
def display_baby_name():
    st.title("아이 정보 조회")

    user_id = st.session_state.get("user_id")  # 로그인한 사용자의 ID를 세션에서 가져오기

    if user_id is None:
        st.warning("로그인 후 이용해 주세요.")
        return

    # 해당 사용자의 아이 정보 가져오기
    response = requests.get(f"{API_URL}/babies/{user_id}")  # 사용자 아이 정보 조회 API 호출

    if response.status_code == 200:
        babies = response.json()  # 아이 정보 목록 가져오기
        if babies:
            # 첫 번째 아이의 이름을 기본값으로 설정
            baby_names = [baby["baby_name"] for baby in babies]
            name = st.selectbox("아이의 이름(태명)을 선택해 주세요", baby_names)  # 선택 박스로 아이 이름 선택

            # 선택한 아이의 추가 정보 표시 가능
            st.success(f"선택한 아이의 이름: {name}")
        else:
            st.warning("등록된 아이가 없습니다.")
    else:
        st.error("아이 정보 조회에 실패했습니다.")

@router.get("/babies/list/{user_id}")
async def get_user_babies(user_id: int, db: Session = Depends(get_db)):
    try:
        babies = db.query(Baby).filter(Baby.user_id == user_id).all()
        return [
            {
                "id": baby.id,
                "baby_name": baby.baby_name,
                "baby_gender": baby.baby_gender,
                "baby_bday": str(baby.baby_bday)
            }
            for baby in babies
        ]
    except Exception as e:
        logger.error(f"아이 목록 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="아이 목록을 가져오는데 실패했습니다.")


# 아이 삭제
@router.delete("/babies/delete/{baby_id}")
async def delete_baby(request: Request, id: int, db: Session = Depends(get_db)):
    logger.info(f"아기 정보 삭제 요청: {id}")

    user_id = request.session.get("id") # 사용자 ID
    
    if user_id is None:
        logger.warning("세션에 ID가 없음")
        raise HTTPException(status_code=401, detail="Not Authorized")

    # 사용자를 user_id로 조회
    user_query = db.query(User)

    if user_id is not None:
        user_query = user_query.filter(User.id == user_id)

    user = user_query.first()

    if user is None:
        logger.error(f"사용자 찾기 실패: ID {user_id}에 대한 사용자가 존재하지 않음")
        raise HTTPException(status_code=404, detail="User를 찾을 수 없습니다")
    
    # 아이 조회
    baby = db.query(Baby).filter(Baby.id == id, Baby.user_id == user_id).first()

    if baby is None:
        logger.error(f"아이 정보 찾기 실패: ID {id}에 대한 아이가 존재하지 않음")
        raise HTTPException(status_code=404, detail="해당 아이 정보를 찾을 수 없습니다.")
    
    # 아이의 이름으로 작성된 모든 동화 삭제
    stories = db.query(Story).filter(Story.user_id == user_id).all()
    logger.info(f"{len(stories)}개의 동화를 삭제합니다.")
    for story in stories:
        db.delete(story)
    
    # 아이 정보 삭제
    db.delete(baby)

    try:
        db.commit()
        logger.info(f"{baby.baby_name} 아이 정보가 삭제되었습니다.")
    except Exception as e:
        db.rollback()
        logger.error(f"아이 정보 삭제 오류: {e}") # 탈퇴 에러 내용 출력
        raise HTTPException(status_code=500, detail="아이 정보 삭제에 실패하였습니다. 다시 시도해 주세요")
    
    # 세션 비우기
    request.session.clear()
    return {"message": "아이 정보가 성공적으로 삭제되었습니다."}
