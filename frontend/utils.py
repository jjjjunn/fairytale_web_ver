# 공통 함수 저장 파일
import streamlit as st
import os
import sys
import inspect
from datetime import datetime
from typing import Optional, List, Dict
import logging
import hashlib
import time
import urllib.parse
import base64
import zipfile
from io import BytesIO

# utils.py 상단에 추가
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# 그런 다음
from models_dir.models import Story


# 로그 설정
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# pages/ 디렉토리를 인식하도록 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "pages")))



# 고유 키 생성
def generate_unique_key(base_key=None):
    unique_string = f"{base_key or ''}{time.time()}"
    return hashlib.md5(unique_string.encode()).hexdigest()

# 대안 페이지 전환 함수 (더 안정적)
def navigate_to(page_name: str):
    """페이지 전환 함수"""
    logging.info(f"페이지 전환 시도: {page_name}")
    
    try:
        # 페이지 이름 정규화
        clean_page_name = page_name.replace("pages/", "").replace(".py", "")
        
        # 쿼리 파라미터 직접 설정
        st.query_params["page"] = clean_page_name
        
        # 세션 상태는 최소한으로 유지
        st.session_state["current_page"] = clean_page_name
        
        # 즉시 리로드
        st.rerun()
        
    except Exception as e:
        logging.error(f"페이지 전환 오류: {str(e)}")
        st.error(f"페이지 전환 중 오류가 발생했습니다: {str(e)}")

# 초기화 함수
def initialize_session_state():
    defaults = {
        "logged_in": False,
        "page": "_login",
        "current_page": "_login",
        "username": None,
        "user_id": None,
        "last_activity": None,
        "error_message": None,
        "target_page": None,
        "page_change_requested": False,
        "switching_page": False,
        "navigate_to": None,
        "navigation_requested": False
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# 페이지 전환 처리 함수
def handle_page_navigation():
    """페이지 전환 요청 처리"""
    if st.session_state.get("navigation_requested"):
        target = st.session_state.get("navigate_to")
        if target:
            logging.info(f"페이지 전환 처리: {target}")
            st.session_state["current_page"] = f"pages/{target}.py"
        
        # 플래그 리셋
        st.session_state["navigation_requested"] = False
        st.session_state["navigate_to"] = None

# 로그인 여부 확인
def check_login(allow_pages=None):
    """로그인 체크 함수 - 개선된 버전"""
    if allow_pages is None:
        allow_pages = ["_login", "_signup", "_settings", "home"]
    
    current_page = st.session_state.get("current_page", "")
    
    # 현재 페이지가 허용된 페이지 목록에 있는지 확인
    if any(allowed in current_page for allowed in allow_pages):
        return True
    
    # 로그인 상태가 아니고 허용되지 않은 페이지인 경우
    if not st.session_state.get("logged_in"):
        logging.warning(f"로그인 필요: {current_page}")
        st.warning("⚠️ 로그인이 필요한 페이지입니다.")
        
    # 로그인 상태가 아니고 허용되지 않은 페이지인 경우
    if not st.session_state.get("logged_in"):
        logging.warning(f"로그인 필요: {current_page}")
        st.warning("⚠️ 로그인이 필요한 페이지입니다.")
        navigate_to("_login")
        st.stop()
    
    return True

# 세션 상태 디버깅 함수
def debug_session_state():
    """개발 모드에서 세션 상태 확인"""
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        with st.expander("🔧 세션 상태 디버깅"):
            st.json({
                "current_page": st.session_state.get("current_page"),
                "logged_in": st.session_state.get("logged_in"),
                "username": st.session_state.get("username"),
                "target_page": st.session_state.get("target_page"),
                "page_change_requested": st.session_state.get("page_change_requested"),
                "switching_page": st.session_state.get("switching_page")
            })

# 페이지 상태 초기화
def reset_page_state():
    """페이지 전환 관련 상태 초기화"""
    keys_to_reset = [
        "target_page", 
        "page_change_requested", 
        "switching_page",
        "navigate_to",
        "navigation_requested",
        "should_redirect_to_login"
    ]
    
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

class ImageSharingUtils:
    """이미지 공유 및 다운로드 관련 유틸리티 클래스"""
    
    @staticmethod
    def get_image_download_link(image_path: str, filename: str) -> str:
        """이미지 다운로드 링크 생성"""
        try:
            if image_path.startswith('http'):
                # URL인 경우 직접 반환
                return image_path
            elif os.path.exists(image_path):
                # 로컬 파일인 경우 base64로 인코딩
                with open(image_path, "rb") as file:
                    contents = file.read()
                b64 = base64.b64encode(contents).decode()
                href = f'data:image/png;base64,{b64}'
                return href
            else:
                return None
        except Exception as e:
            logging.error(f"이미지 다운로드 링크 생성 실패: {e}")
            return None
    
    @staticmethod
    def create_download_button(image_path: str, filename: str, button_text: str = "📥 다운로드"):
        """스트림릿 다운로드 버튼 생성"""
        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as file:
                    btn = st.download_button(
                        label=button_text,
                        data=file.read(),
                        file_name=filename,
                        mime="image/png",
                        use_container_width=True
                    )
                    return btn
            else:
                st.error("이미지 파일을 찾을 수 없습니다.")
                return False
        except Exception as e:
            st.error(f"다운로드 버튼 생성 실패: {e}")
            return False
    
    @staticmethod
    def create_bulk_download(stories: List[Story], download_type: str = "all") -> Optional[bytes]:
        """여러 이미지를 ZIP으로 묶어서 다운로드"""
        try:
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for idx, story in enumerate(stories):
                    # 컬러 이미지 추가
                    if story.image and os.path.exists(story.image):
                        color_filename = f"story_{idx+1}_color_{story.theme}.png"
                        zip_file.write(story.image, color_filename)
                    
                    # 흑백 이미지 추가 (요청된 경우)
                    if download_type == "all" and story.bw_image and os.path.exists(story.bw_image):
                        bw_filename = f"story_{idx+1}_bw_{story.theme}.png"
                        zip_file.write(story.bw_image, bw_filename)
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
            
        except Exception as e:
            logging.error(f"ZIP 파일 생성 실패: {e}")
            return None
    
    @staticmethod
    def get_social_sharing_urls(image_url: str, story_theme: str) -> dict:
        """소셜 미디어 공유 URL 생성"""
        # 공유할 텍스트 및 URL 준비
        share_text = f"AI가 만든 동화 이미지: {story_theme}"
        encoded_text = urllib.parse.quote(share_text)
        encoded_url = urllib.parse.quote(image_url) if image_url else ""
        
        return {
            "kakao": f"https://story.kakao.com/s/share?url={encoded_url}&text={encoded_text}",
            "facebook": f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}",
            "twitter": f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_url}",
            "line": f"https://social-plugins.line.me/lineit/share?url={encoded_url}",
            "email": f"mailto:?subject={encoded_text}&body={encoded_text}%0A%0A{encoded_url}",
            "copy": image_url  # 링크 복사용
        }