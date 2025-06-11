import streamlit as st
import requests
from dotenv import load_dotenv
import os
from utils import navigate_to, generate_unique_key
import time
import logging

# .env 파일에서 환경변수 로드
load_dotenv()
API_URL = os.getenv('API_URL')

if not API_URL:
    st.error("API_URL 환경 변수가 설정되지 않았습니다!")
    st.stop()

# 로그 설정
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 현재 페이지 설정
st.session_state["current_page"] = "pages/_settings.py"

# 세션 상태 초기화
def reset_inputs():
    for key in ["username", "current_password", "new_password", "new_password_confirm"]:
        st.session_state[key] = ""

# 아이디 찾기
def find_id():
    st.subheader("🔎 아이디 찾기")
    
    with st.form("find_id_form"):
        email = st.text_input("이메일")
        submit_btn = st.form_submit_button("아이디 찾기")
        
        if submit_btn:
            logging.info(f"아이디 찾기 요청: email={email}")
            if not email:
                st.warning("모든 항목을 입력해주세요.")
                return
                
            find_id_data = {
                "email": email,
            }

            try:
                response = requests.post(f"{API_URL}/find_id", json=find_id_data, timeout=30)
                
                if response.status_code == 200:
                    user_name = response.json().get("username")
                    st.success(f'찾으신 아이디: {user_name}, 이메일을 확인해 주세요.')
                else:
                    error_message = response.json().get("detail", "아이디 찾기에 실패하였습니다.")
                    st.error(error_message)
            except Exception as e:
                st.error(f"요청 중 오류가 발생했습니다: {str(e)}")

# 임시 비밀번호 받기
def gen_temp_pw():
    st.subheader("🔐 임시 비밀번호 발급")
    
    with st.form("gen_temp_pw_form"):
        username = st.text_input("아이디")
        email = st.text_input("이메일")
        submit_btn = st.form_submit_button("비밀번호 찾기")
        
        if submit_btn:
            logging.info(f"임시 비밀번호 발급 요청: username={username}, email={email}")
            if not username or not email:
                st.warning("모든 항목을 입력해주세요.")
                return
                
            gen_temp_pw_data = {
                "username": username,
                "email": email,
            }

            try:
                response = requests.post(f"{API_URL}/reset_password", json=gen_temp_pw_data, timeout=30)
                
                if response.status_code == 200:
                    st.success('임시 비밀번호가 발송되었습니다. 이메일을 확인해 주세요.')
                else:
                    error_message = response.json().get("detail", "임시 비밀번호 생성에 실패하였습니다.")
                    st.error(error_message)
            except Exception as e:
                st.error(f"요청 중 오류가 발생했습니다: {str(e)}")

# 비밀번호 변경하기
def change_pw():
    st.subheader("🔄 비밀번호 변경")
    
    # # 로그인 체크
    # if not st.session_state.get("logged_in"):
    #     st.warning("⚠️ 비밀번호 변경은 로그인이 필요합니다.")
    #     if st.button("로그인하러 가기"):
    #         st.query_params["page"] = "_login"
    #         st.rerun()
    #     return
    
    with st.form("change_pw_form"):
        username = st.text_input("아이디", key=generate_unique_key("username"))
        current_password = st.text_input("현재 비밀번호", type="password", key=generate_unique_key("current_password"))
        new_password = st.text_input("새 비밀번호", type="password", key=generate_unique_key("new_password"))
        new_password_confirm = st.text_input("새 비밀번호 확인", type="password", key=generate_unique_key("new_password_confirm"))
        submit_btn = st.form_submit_button("비밀번호 변경")
        
        if submit_btn:
            if not username or not current_password or not new_password or not new_password_confirm:
                st.warning("모든 항목을 입력해주세요.")
                return
                
            if new_password != new_password_confirm:
                st.error("새 비밀번호가 일치하지 않습니다.")
                return
                
            change_pw_data = {
                "username": username,
                "current_password": current_password,
                "new_password": new_password,
                "new_password_confirm": new_password_confirm,
            }

            try:
                response = requests.put(f"{API_URL}/change_pw", json=change_pw_data, timeout=30)
                
                if response.status_code == 200:
                    st.success('비밀번호가 변경되었습니다.')
                    st.balloons()
                    time.sleep(3)  # 잠시 대기
                    st.session_state["signup_success"] = True
                    st.rerun()  # 페이지 새로고침
                else:
                    error_message = response.json().get("detail", "비밀번호 변경에 실패하였습니다.")
                    st.error(error_message)
            except Exception as e:
                st.error(f"요청 중 오류가 발생했습니다: {str(e)}")

def main():
    st.title("🔧 계정 설정")
    
    # 탭 선택
    selected_tab = st.selectbox(
        "원하는 작업을 선택하세요:",
        ["🔎 아이디 찾기", "🔐 임시 비밀번호 발급", "🔄 비밀번호 변경"],
        key="settings_main_tab"
    )
    
    st.markdown("---")
    
    # 선택된 탭에 따라 함수 실행
    if selected_tab == "🔎 아이디 찾기":
        find_id()
    elif selected_tab == "🔐 임시 비밀번호 발급":
        gen_temp_pw()
    elif selected_tab == "🔄 비밀번호 변경":
        change_pw()
    
    # st.markdown("---")
    
    # # 뒤로가기 버튼
    # col1, col2, col3 = st.columns([1, 2, 1])
    # with col2:
    #     if st.button("🔙 로그인 페이지로 돌아가기", use_container_width=True):
    #         logging.info("뒤로 버튼 클릭")
    #         # st.session_state["from_other_page"] = True  # 플래그 설정
    #         # navigate_to("_login")
    #         st.query_params["page"] = "_login"
    #         st.rerun()

if __name__ == "__main__":
    main()