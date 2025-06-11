import streamlit as st
import requests
from dotenv import load_dotenv
import sys
import os
# 현재 파일의 상위 상위 폴더인 'fairytale'을 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from utils import initialize_session_state, check_login, navigate_to, generate_unique_key
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 초기화 함수 호출
initialize_session_state()

load_dotenv()  # .env 파일에서 환경변수 로드
API_URL = os.getenv('API_URL')

# 현재 페이지 설정
st.session_state["current_page"] = "pages/profiles.py"

# Streamlit 앱 설정
title = "사용자 정보 페이지"
st.markdown("# 사용자 정보 페이지입니다.")

# 로그인 상태 확인
if not st.session_state.get("logged_in"):
    st.warning("먼저 로그인해 주세요.")
    st.query_params["page"] = "_login"
    st.rerun()
else:
    # 사이드바에 로그아웃 버튼
    if st.sidebar.button("🔓 로그아웃"):
        logging.info(f"사용자 {st.session_state.get('username')}님이 로그아웃했습니다.")
        for key in ["logged_in", "username"]: # 로그아웃 시 세션 상태를 완전히 초기화
            st.session_state[key] = None
        st.rerun()

# 아기 추가하기 설정
def add_baby():
    st.title("아이 이름 설정")

    # user_id를 정수형으로 변환
    try:
        user_id = st.session_state.get("user_id")
        if not user_id:
            st.error("사용자 ID를 찾을 수 없습니다.")
            return
    except (TypeError, ValueError):
        st.error("잘못된 사용자 ID입니다.")
        return

    # 사용자 입력
    baby_name = st.text_input("아이 이름을 입력하세요")
    baby_gender = st.radio("아이 성별을 선택해 주세요.", options=["남아", "여아", "모름"])
    baby_bday = st.date_input("출생 날짜를 선택하세요")

    # 성별 매핑 추가
    gender_mapping = {
        "남아": "M",
        "여아": "F",
        "모름": "U"
    }

    if st.button("아이 추가 하기"):
        # 입력값 검증
        if not baby_name.strip():
            st.error("아이 이름을 입력해 주세요.")
            return
        if baby_gender not in ["남아", "여아", "모름"]:
            st.error("아이 성별을 선택해 주세요.")
            return

        # 사용자 입력 데이터 준비
        baby_data = {
            "user_id": user_id,
            "baby_name": baby_name.strip(),
            "baby_gender": gender_mapping[baby_gender],
            "baby_bday": str(baby_bday)
        }

        with st.spinner('아기 정보를 저장 중입니다...'):
            # FastAPI에 데이터 전송
            try:
                response = requests.post(f"{API_URL}/babies/create_baby", json=baby_data)

                # 응답 처리
                if response.status_code == 200:
                    baby_info = response.json()
                    logging.info(f"아기 정보 추가 성공: {baby_info}")
                    st.success(f'아기 정보가 성공적으로 추가되었습니다. (ID: {baby_info["baby"]["id"]})')
                else:
                    error_message = response.json().get("detail", "오류가 발생했습니다. 다시 시도해 주세요.")
                    st.error(error_message)

            except requests.exceptions.RequestException as e:
                st.error(f"서버와의 통신 중 오류가 발생했습니다: {e}")
    
    if st.button("뒤로 가기", key=generate_unique_key("back_button")):
        st.query_params["page"] = "home"
        st.rerun()


# 아이 삭제하기
def delete_baby():
    st.title("아이 삭제하기 👶")

    try:
        user_id = st.session_state.get("user_id")
        
        # 현재 사용자의 아이 목록 가져오기
        response = requests.get(f"{API_URL}/babies/list/{user_id}")
        
        if response.status_code == 200:
            babies = response.json()
            if not babies:
                st.info("등록된 아이가 없습니다.")
                return
                
            # 드롭다운으로 아이 선택
            baby_options = {baby['baby_name']: baby['id'] for baby in babies}
            
            selected_baby = st.selectbox(
                "삭제할 아이를 선택하세요",
                options=list(baby_options.keys()),
                help="삭제할 아이를 선택하세요."
            )
            
            # 삭제 버튼
            if st.button("아이 삭제", type="primary"):
                baby_info = baby_options[selected_baby]
                if selected_baby:
                    delete_data = {
                        "user_id": user_id,
                        "baby_id": baby_options[selected_baby]
                    }
                    
                    with st.spinner("삭제 요청을 처리 중입니다..."):
                        response = requests.delete(
                            f"{API_URL}/babies/delete/{delete_data['baby_id']}",
                            headers={"Content-Type": "application/json"}
                        )
                    
                    if response.status_code == 200:
                        st.success(f"{baby_info['name']} 정보가 삭제되었습니다.")
                        st.rerun()  # 목록 새로고침
                    else:
                        error_message = response.json().get("detail", "알 수 없는 오류가 발생했습니다.")
                        st.error(f"아이 삭제 실패: {error_message}")
                        
        else:
            st.error("아이 목록을 가져오는데 실패했습니다.")
                
    except requests.exceptions.RequestException as e:
        st.error(f"서버와의 통신 중 오류가 발생했습니다: {e}")
    except (TypeError, ValueError):
        st.error("사용자 ID 오류가 발생했습니다.")

    # 뒤로 가기 버튼
    if st.button("뒤로 가기", key=generate_unique_key("back_button_delete_baby")):
        st.query_params["page"] = "profiles"
        st.rerun()  # "프로필" 페이지로 이동


# 회원 탈퇴하기
def delete_user():
    st.title("회원 탈퇴하기 🗑️")
    st.warning("⚠️ 회원 탈퇴를 진행하면 계정과 연결된 모든 정보가 삭제됩니다. 신중히 결정해 주세요!")

    # 탈퇴 확인 단계 (추가 확인 메시지)
    confirm = st.checkbox("회원 탈퇴에 동의합니다.")

    if confirm and st.button("탈퇴 진행"):
        # 회원 탈퇴 요청 데이터
        delete_data = {
            "user_id": st.session_state.get("user_id")
        }

        try:
            # FastAPI 회원 탈퇴 요청
            with st.spinner("회원 탈퇴를 처리 중입니다..."):
                response = requests.delete(f"{API_URL}/delete_user", json=delete_data)

            # 응답 처리
            if response.status_code == 200:
                st.success("회원 탈퇴가 성공적으로 처리되었습니다. 이용해 주셔서 감사합니다.")
                
                # 세션 초기화
                st.session_state.clear()
                st.query_params["page"] = "_login"
                st.rerun()  # 로그인 페이지로 이동
            else:
                error_message = response.json().get("detail", "회원 탈퇴 처리에 실패했습니다. 다시 시도해 주세요.")
                st.error(f"회원 탈퇴 실패: {error_message}")

        except requests.exceptions.RequestException as e:
            st.error(f"서버와의 통신 중 오류가 발생했습니다: {e}")

    # 뒤로 가기 버튼
    if st.button("뒤로 가기", key=generate_unique_key("back_button_delete_user")):
        st.query_params["page"] = "profiles"
        st.rerun()  # "프로필" 페이지로 이동

def main():
    check_login()  # 로그인 확인
    
    # 탭 추가로 UI 개선
    tab1, tab2, tab3 = st.tabs(["아이 추가", "아이 삭제", "회원 탈퇴"])
    
    with tab1:
        add_baby()
    with tab2:
        delete_baby()
    with tab3:
        delete_user()

if __name__ == "__main__":
    main()

