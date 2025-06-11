import streamlit as st
import requests
from dotenv import load_dotenv
import os
from utils import navigate_to
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
st.session_state["current_page"] = "pages/_signup.py"

# # 세션 상태 초기화
# if "logged_in" not in st.session_state:
#     st.session_state["logged_in"] = False

# # 이미 로그인된 경우 stories 페이지로 리다이렉트 (강제 접근이 아닌 경우에만)
#     if st.session_state.get("logged_in", False) and not st.session_state.get("force_login_page", False):
#         st.info("이미 로그인되어 있습니다. Stories 페이지로 이동합니다...")
#         logging.info(f"이미 로그인된 사용자: {st.session_state.get('username')}")
#         time.sleep(1)
#         st.query_params["page"] = "stories"
#         st.rerun()

# 세션 상태 초기화
def reset_inputs():
    for key in ["username", "nickname", "email", "password", "password_confirm"]:
        st.session_state[key] = ""


def main():
    st.title("📝 회원가입")
    st.markdown("새로운 계정을 만들어보세요!")

    if "signup_success" not in st.session_state:
        st.session_state["signup_success"] = False

    if st.session_state["signup_success"]:
        reset_inputs()
        st.session_state["signup_success"] = False
    
    # 회원가입 폼
    with st.form("signup_form"):
        st.subheader("회원 정보 입력")
        
        username = st.text_input("아이디", placeholder="아이디를 입력하세요", key="username")
        nickname = st.text_input("닉네임", placeholder="닉네임을 입력하세요", key="nickname")
        email = st.text_input("이메일", placeholder="이메일을 입력하세요", key="email")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key="password")
        password_confirm = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호를 다시 입력하세요", key="password_confirm")
        
        submitted = st.form_submit_button("🚀 회원가입", use_container_width=True)
        
        if submitted:
            logging.info("회원가입 폼 제출됨")
            # 입력 검증
            if not username or not nickname or not email or not password or not password_confirm:
                st.warning("⚠️ 모든 항목을 입력해주세요.")
            elif password != password_confirm:
                st.error("❌ 비밀번호가 일치하지 않습니다.")
            else:
                # 회원가입 처리
                with st.spinner("회원가입 처리 중..."):
                    signup_data = {
                        "username": username,
                        "nickname": nickname,
                        "email": email,
                        "password": password,
                        "password_confirm": password_confirm,
                    }

                    try:
                        # FastAPI 백엔드 API 호출
                        response = requests.post(f"{API_URL}/signup", json=signup_data, timeout=30)
                        
                        if response.status_code == 200:
                            st.success('🎉 회원가입이 완료되었습니다! 이메일을 확인해 주세요.')
                            logging.info(f"회원가입 성공: {username}")
                            st.balloons()
                            time.sleep(3)  # 잠시 대기
                            st.session_state["signup_success"] = True
                            st.rerun()  # 페이지 새로고침
                            
                        else:
                            # 에러 메시지 처리
                            try:
                                error_data = response.json()
                                error_message = error_data.get("detail", "회원가입에 실패했습니다.")
                            except:
                                error_message = "서버 응답을 처리할 수 없습니다."
                            
                            st.error(f"❌ {error_message}")
                            
                    except requests.exceptions.Timeout:
                        st.error("⏰ 요청 시간이 초과되었습니다. 다시 시도해주세요.")
                    except requests.exceptions.ConnectionError:
                        st.error("🌐 서버에 연결할 수 없습니다. 네트워크를 확인해주세요.")
                    except Exception as e:
                        st.error(f"❌ 회원가입 중 오류가 발생했습니다: {str(e)}")

    # # 구분선
    # st.markdown("---")
    
    # # 하단 버튼들
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