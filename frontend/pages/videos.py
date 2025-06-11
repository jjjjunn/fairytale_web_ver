import streamlit as st
import sys
import os
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 현재 파일의 상위 상위 폴더인 'fairytale'을 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from controllers.video_controller import search_videos, THEME_KEYWORDS
from utils import initialize_session_state, check_login

# 초기화 함수 호출
initialize_session_state()

# 현재 페이지 설정
st.session_state["current_page"] = "pages/videos.py"

st.title("🎵 우리 아가를 위한 자장가 재생기")
st.markdown("테마를 선택하면 아기를 위한 자장가 영상을 드려요")

def main():
    check_login()
    # 로그인 여부 확인
    if 'user_id' not in st.session_state:
        st.warning("먼저 로그인해 주세요")
        st.stop()  # 코드 실행 중단
    else:
        user_id = st.session_state.user_id

        # 사이드바에 로그아웃 버튼
        if st.sidebar.button("🔓 로그아웃"):
            logging.info(f"사용자 {st.session_state.get('username')}님이 로그아웃했습니다.")
            for key in ["logged_in", "username"]: # 로그아웃 시 세션 상태를 완전히 초기화
                st.session_state[key] = None
            st.rerun()

    # 테마 선택
    theme = st.selectbox("🎨 자장가 테마를 선택해 주세요", list(THEME_KEYWORDS.keys()))

    # 현재 재생 중인 track index를 세션 상태에 저장
    if "playing_index" not in st.session_state:
        st.session_state.playing_index = None

    if "youtube_url" not in st.session_state:
        st.session_state.youtube_url = None

    if "search_results" not in st.session_state:
        st.session_state.search_results = []

    if st.button("🔍 자장가 불러오기"):
        st.info(f"'{theme}' 테마에 맞는 자장가를 불러오는 중입니다.")
        results = search_videos(theme)

        if results:
            st.session_state.search_results = results if isinstance(results, list) else results.split('\n')

            for video in st.session_state.search_results:
                st.video(video["url"])
            
        else:
            st.warning("🔇 해당 테마에 맞는 자장가를 찾지 못했습니다.")

if __name__ == "__main__":
    main()