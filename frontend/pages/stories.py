import streamlit as st
import sys
import os
from dotenv import load_dotenv
# 현재 파일의 상위 상위 폴더인 'fairytale'을 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from controllers.story_controller import generate_fairy_tale, generate_openai_voice, generate_image_from_fairy_tale, save_story_to_db, convert_bw_image, audio_to_base64
import requests
from utils import initialize_session_state, check_login
import logging

# 초기화 함수 호출
initialize_session_state()

# 로그 설정
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# .env 파일에서 환경변수 로드
load_dotenv()
API_URL = os.getenv('API_URL')

if not API_URL:
    st.error("API_URL 환경 변수가 설정되지 않았습니다!")
    st.stop()

# 현재 페이지 설정
st.session_state["current_page"] = "pages/stories.py"

# 초기 상태 설정
if 'fairy_tale_text' not in st.session_state:
    st.session_state.fairy_tale_text = ""

if 'image_url' not in st.session_state:
    st.session_state.image_url = None

def main():
    check_login()
    # Streamlit 앱 설정
    title = "태교 동화 생성봇"
    st.markdown("# 인공지능 동화작가 동글이입니다.")

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

    # 태아 또는 자녀 이름 입력 받기
    try:
        user_id = st.session_state.get("user_id")
        
        # 현재 사용자의 아이 목록 가져오기
        response = requests.get(f"{API_URL}/babies/list/{user_id}")
        
        if response.status_code == 200:
            babies = response.json()
            if not babies:
                st.info("등록된 아이가 없습니다.")
                st.write("👈 왼쪽 사이드바의 '프로필' 메뉴에서 아이를 추가해주세요!")
                return
                
            # 드롭다운으로 아이 선택
            baby_options = {baby['baby_name']: baby['id'] for baby in babies}
            
            selected_baby = st.selectbox(
                "아이를 선택하세요",
                options=list(baby_options.keys()),
                help="아이를 선택하세요."
            )
    except requests.exceptions.RequestException as e:
        st.error(f"서버와의 통신 중 오류가 발생했습니다: {e}")
    except (TypeError, ValueError):
        st.error("사용자 ID 오류가 발생했습니다.")

    # 아이 이름을 세션 상태에 저장
    if 'selected_baby' not in st.session_state:
        st.write(f"{selected_baby}을(를) 위한 동화를 생성해 드립니다.")

    # 속도 버튼
    speed = st.slider("속도를 선택해 주세요", 0, 2, 1) # 최소, 최대, 기본값
    st.write("선택한 속도:", speed)

    # 테마 버튼
    thema = st.selectbox("테마를 선택해 주세요", ["자연", "도전", "가족", "사랑", "우정", "용기"])
    st.write("선택한 테마:", thema)

    # 목소리 선택
    voice_choices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "ash", "coral", "sage"]
    # 음성 선택을 세션 상태로 관리
    if "selected_voice" not in st.session_state:
        st.session_state.selected_voice = "alloy"

    voice = st.selectbox(
        "목소리를 선택해 주세요", 
        voice_choices,
        index=voice_choices.index(st.session_state.selected_voice),
        key="voice_selector"
    )

    # 선택된 음성을 세션 상태에 저장
    st.session_state.selected_voice = voice
    st.write("선택한 목소리:", voice)

    # 동화 생성 버튼
    if st.button("동화 생성"):
        logging.info(f"동화 생성 요청: {thema}, 아이: {selected_baby}, 속도: {speed}, 목소리: {voice}")
        st.session_state.fairy_tale_text = generate_fairy_tale(selected_baby, thema)  # 동화 생성
        st.success("동화가 생성되었습니다!")  # 사용자 피드백

    # 동화 내용 표시
    st.text_area("생성된 동화:", st.session_state.fairy_tale_text, height=300)

    # 음성 재생 버튼
    if st.button("음성으로 듣기"):
        if st.session_state.get("fairy_tale_text"):
            with st.spinner(f"{voice} 목소리로 음성을 생성하는 중..."):
                audio_data = generate_openai_voice(
                        st.session_state.fairy_tale_text, 
                        voice=voice,
                        speed=speed
                    )
                    
                if audio_data:
                    st.success(f"{voice} 목소리로 생성 완료!")
                    
                    # Streamlit에서 바이너리 데이터 직접 재생
                    st.audio(audio_data, format='audio/mp3')
                    
                    # Base64 인코딩된 데이터도 표시 (모바일 앱 개발 참고용)
                    with st.expander("개발자용 - Base64 데이터"):
                        base64_audio = audio_to_base64(audio_data)
                        st.text_area("Base64 Audio Data (모바일 앱용)", 
                                    value=base64_audio[:200] + "...", 
                                    height=100)
                else:
                    st.error("음성 생성에 실패했습니다.")
        else:
            st.warning("먼저 동화를 생성하세요.")

    # 이미지 생성 버튼
    if st.button("동화 이미지 생성"):
        if st.session_state.fairy_tale_text.strip():
            image_url = generate_image_from_fairy_tale(st.session_state.fairy_tale_text)
            if image_url:
                st.session_state.image_url = image_url
                st.success("이미지가 생성되었습니다!")
            else:
                st.warning("이미지 생성에 실패했습니다. 입력을 다시 확인해주세요.")
        else:
            st.warning("먼저 동화 내용을 입력해주세요.")

    # 이미지 표시
    if st.session_state.image_url:
        st.image(st.session_state.image_url, caption="동화 이미지", use_container_width=True)

    # 흑백 이미지 변환 버튼
    image_url = st.session_state.get("image_url", "")   
    if st.button("흑백 이미지 변환"):
        logging.info("흑백 이미지 변환 요청")
        if not image_url:
            st.warning("이미지를 먼저 생성해주세요.")
            return
        else:
            bw_path = convert_bw_image(st.session_state.image_url)
            if bw_path:
                st.session_state.bw_image_path = bw_path
                st.success("흑백 이미지로 변환되었습니다.")
                    # 자동 저장
                try:
                    logging.info("동화 자동 저장 요청")
                    saved_story = save_story_to_db(
                        user_id=user_id,
                        theme=thema,
                        voice=voice,
                        content=st.session_state.fairy_tale_text,
                        voice_content="",  # 음성 저장 안 함
                        image=image_url,
                        bw_image=bw_path  # 흑백 이미지 저장
                    )
                    st.success(f"동화가 자동으로 저장되었습니다! (ID: {saved_story.id})")
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")

    else:
        st.error("흑백 이미지로 변환에 실패하였습니다.")

    # 흑백 이미지 표시
    if st.session_state.get("bw_image_path"):
        st.image(st.session_state.bw_image_path, caption="색칠용 라인 드로잉", use_container_width=True)

# 함수 실행
if __name__ == "__main__":
    main()