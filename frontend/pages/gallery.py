import sys
import os
# 현재 파일의 상위 상위 폴더인 'fairytale'을 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from sqlalchemy.orm import Session
from controllers.dependencies import get_db
from models_dir.models import Story, User  # User 모델 추가 import
from controllers.story_controller import get_user_images, display_gallery, display_story_list
from utils import initialize_session_state, check_login, ImageSharingUtils
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 초기화 함수 호출
initialize_session_state()

# 현재 페이지 설정
st.session_state["current_page"] = "pages/gallery.py"


def main():
    # 로그인 확인
    check_login()
    
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.warning("로그인 후 이용 가능합니다. 로그인을 먼저 해주세요.")
        st.stop()
    
    # 사이드바에 로그아웃 버튼
    if st.sidebar.button("🔓 로그아웃"):
        logging.info(f"사용자 {st.session_state.get('username')}님이 로그아웃했습니다.")
        for key in ["logged_in", "username"]: # 로그아웃 시 세션 상태를 완전히 초기화
            st.session_state[key] = None
        st.rerun()

    try:
        db: Session = next(get_db())
    except Exception as e:
        st.error(f"DB 연결에 실패했습니다: {e}")
        return
    
    user_id = st.session_state.get("user_id")
    
    if not user_id:
        st.warning("로그인 후 이용 가능합니다.")
        st.stop()
    
    # 사용자 정보 조회
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            st.error("사용자 정보를 찾을 수 없습니다.")
            st.stop()
    except Exception as e:
        st.error(f"사용자 정보를 조회하는 중 오류가 발생했습니다: {e}")
        return
    
    st.title("🎨 이미지 갤러리")
    st.markdown(f"**{user.username}**님의 이미지 갤러리입니다.")
    
    # 사용자별 스토리 조회
    try:
        stories = get_user_images(db, user_id)
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return
    finally:
        db.close()
    
    # 스토리 데이터가 없는 경우
    if not stories:
        st.info("생성된 이미지가 없습니다.")
        st.info("👈 왼쪽 사이드바에서 동화 만들기를 선택해 주세요.")
        # col1, col2, col3 = st.columns([1, 1, 1])
        # with col2:
        #     if st.button("🎨 새 이미지 생성하기", use_container_width=True):
        #         logging.info("새 이미지 생성 페이지로 이동")
        #         st.query_params["page"] = "stories"
        #         st.rerun()
        st.stop()
    
    # 스토리 개수 표시
    st.info(f"총 {len(stories)}개의 이미지가 있습니다.")
    
    # 일괄 다운로드 옵션
    with st.expander("📦 일괄 다운로드"):
        col1, col2 = st.columns(2)
        
        sharing_utils = ImageSharingUtils()
        
        with col1:
            if st.button("🎨 모든 컬러 이미지 다운로드", use_container_width=True):
                zip_data = sharing_utils.create_bulk_download(stories, "color")
                if zip_data:
                    st.download_button(
                        label="📥 ZIP 파일 다운로드",
                        data=zip_data,
                        file_name=f"{user.username}_컬러이미지모음.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
        
        with col2:
            if st.button("📦 모든 이미지 다운로드", use_container_width=True):
                zip_data = sharing_utils.create_bulk_download(stories, "all")
                if zip_data:
                    st.download_button(
                        label="📥 ZIP 파일 다운로드",
                        data=zip_data,
                        file_name=f"{user.username}_전체이미지모음.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
    
    # 표시 모드 선택
    view_mode = st.radio("보기 모드:", ["그리드", "목록"], horizontal=True)
    
    # 페이지네이션 설정
    if "gallery_current_page" not in st.session_state:
        st.session_state.gallery_current_page = 0
    
    per_page = 9 if view_mode == "그리드" else 5
    current_page = st.session_state.gallery_current_page
    total_pages = (len(stories) + per_page - 1) // per_page
    
    # 현재 페이지 데이터
    start_idx = current_page * per_page
    end_idx = start_idx + per_page
    current_stories = stories[start_idx:end_idx]
    
    st.markdown(f"**페이지: {current_page + 1} / {total_pages}** (총 {len(stories)}개)")
    
    # 갤러리 표시
    if view_mode == "그리드":
        display_gallery(current_stories, current_page, per_page)
    elif view_mode == "목록":
        display_story_list(current_stories, current_page, per_page)
    
    # 페이지 전환 버튼
    if total_pages > 1:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if current_page > 0:
                if st.button("⬅️ 이전", use_container_width=True):
                    st.session_state.gallery_current_page -= 1
                    st.rerun()
        
        with col2:
            page_info = f"페이지 {current_page + 1} / {total_pages}"
            st.markdown(f"<div style='text-align: center; padding: 10px;'>{page_info}</div>", 
                       unsafe_allow_html=True)
        
        with col3:
            if current_page < total_pages - 1:
                if st.button("다음 ➡️", use_container_width=True):
                    st.session_state.gallery_current_page += 1
                    st.rerun()


if __name__ == "__main__":
    main()