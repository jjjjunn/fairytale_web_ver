
import streamlit as st
import requests
from dotenv import load_dotenv
import os
import time
from utils import initialize_session_state, handle_page_navigation, debug_session_state
import sys
import logging

# pages/ 디렉토리를 인식하도록 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "pages")))

# 로그 설정
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


# .env 파일에서 환경 변수 로드
load_dotenv()
API_URL = os.getenv("API_URL")

if not API_URL:
    st.error("API_URL 환경 변수가 설정되지 않았습니다!")
    logging.error("API_URL 환경 변수가 설정되지 않았습니다!")
    st.stop()

# 세션 상태 초기화
initialize_session_state()

# 페이지 전환 처리
handle_page_navigation()

# 현재 페이지 설정
st.session_state["current_page"] = "pages/_login.py"

# 로그인 페이지 함수
def main():
    if st.session_state.get("current_page") != "pages/_login.py":
        st.stop()  # 다른 페이지로 전환 중이면 실행 중단

    # 이미 로그인된 경우 안내 메시지 표시
    if st.session_state.get("logged_in", False):
        st.info("이미 로그인되어 있습니다. 👈 왼쪽 사이드바에서 원하는 메뉴를 선택해주세요.")
        logging.info(f"이미 로그인된 사용자: {st.session_state.get('username')}")
        time.sleep(1)
        return

    st.title("🔑 로그인")
    st.markdown("👋 반갑습니다! 아이디와 비밀번호를 입력하여 로그인하세요.")
    st.subheader("아이와 함께하는 세상에 하나뿐인 이야기 📖")

    # 로그인 폼
    with st.form("login_form"):
        username = st.text_input("아이디", placeholder="아이디를 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        
        submitted = st.form_submit_button("🚀 로그인", use_container_width=True)
        
        if submitted:
            logging.info(f"로그인 시도: {username}")
            if not username or not password:
                st.warning("⚠️ 아이디와 비밀번호를 모두 입력해주세요.")
                logging.warning("아이디 또는 비밀번호 미입력")
            else:
                with st.spinner("로그인 중..."):
                    login_data = {"username": username, "password": password}
                    try:
                        # 세션 설정 추가
                        session = requests.Session()
                        session.headers.update({
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        })

                        # FastAPI로 POST 요청 (로그인 확인)
                        response = session.post(
                            f"{API_URL}/login", 
                            json=login_data, 
                            timeout=(5, 30)  # (connect timeout, read timeout)
                        )
                        
                        if response.status_code == 200:
                            # 로그인 성공 처리
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = username
                            
                            # 서버 응답에서 추가 정보 가져오기
                            response_data = response.json()
                            
                             # 세션 상태 업데이트
                            st.session_state.update({
                                "logged_in": True,
                                "username": username,
                                "user_id": response_data.get("user_id"),
                                # "current_page": "pages/_login.py"
                            })
                            
                            st.success("✅ 로그인 성공! 환영합니다.")
                            st.balloons()
                            logging.info(f"로그인 성공: {username}, ID: {st.session_state['user_id']}")
                            
                            # 페이지 이동
                            # st.query_params["page"] = "gallery"
                            st.rerun()
                            
                        elif response.status_code == 401:
                            st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")
                            logging.warning(f"로그인 실패(401): {username}")
                        elif response.status_code == 404:
                            st.error("❌ 존재하지 않는 사용자입니다.")
                            logging.warning(f"로그인 실패(404): {username}")
                        else:
                            st.error(f"❌ 로그인 실패: {response.status_code}")
                            logging.error(f"로그인 실패({response.status_code}): {username}")
                            
                    except requests.exceptions.Timeout:
                        st.error("⏰ 요청 시간이 초과되었습니다. 다시 시도해주세요.")
                        logging.error("로그인 요청 타임아웃")
                    except requests.exceptions.ConnectionError:
                        st.error("🌐 서버에 연결할 수 없습니다. 네트워크를 확인해주세요.")
                        logging.error("서버 연결 오류")
                    except Exception as e:
                        st.error(f"❌ 로그인 요청 중 오류 발생: {e}")
                        logging.exception("로그인 요청 중 예외 발생")
                    finally:
                        session.close()

    # 구분선
    st.markdown("---")

    # 하단 버튼들
    # col1, col2, col3 = st.columns([1, 1, 1])

    # with col1:
    #     if st.button("📝 회원가입", use_container_width=True):
    #         logging.info("회원가입 버튼 클릭")
    #         # st.session_state["from_other_page"] = True  # 플래그 설정
    #         # navigate_to("_signup")
    #         st.query_params["page"] = "_signup"  # 직접 쿼리 파라미터 설정
    #         st.rerun()

    # with col2:
    #     if st.button("🔐 계정 정보 찾기", use_container_width=True):
    #         logging.info("계정 정보 찾기 버튼 클릭")
    #         # st.session_state["from_other_page"] = True  # 플래그 설정
    #         # navigate_to("_settings")
    #         st.query_params["page"] = "_settings"  # 직접 쿼리 파라미터 설정
    #         st.rerun()

    # with col3:
    #     if st.button("🏠 홈으로", use_container_width=True):
    #         logging.info("홈으로 버튼 클릭")
    #         # st.session_state["from_other_page"] = True  # 플래그 설정
    #         # navigate_to("home")
    #         st.query_params["page"] = "home"  # 직접 쿼리 파라미터 설정
    #         st.rerun()

    # 하단 안내 메시지
    st.markdown("### 💡 도움이 필요하신가요?")
    
    st.info("""
    **👈 왼쪽 사이드바를 이용해주세요:**
    - **회원가입**: 새 계정을 만들고 싶다면
    - **설정**: 계정 정보를 찾고 싶다면  
    - **홈**: 메인 페이지로 돌아가고 싶다면
    """)
    
    # 추가 도움말
    with st.expander("🔍 자주 묻는 질문"):
        st.markdown("""
        **Q: 비밀번호를 잊어버렸어요**  
        A: 왼쪽 사이드바의 '설정' 메뉴를 이용해주세요.
        
        **Q: 계정이 없어요**  
        A: 왼쪽 사이드바의 '회원가입' 메뉴를 이용해주세요.
        
        **Q: 로그인이 안 돼요**  
        A: 아이디와 비밀번호를 정확히 입력했는지 확인해주세요.
        """)

    # 디버깅 정보 (개발 모드)
    debug_session_state()

# 로그인 페이지 실행
if __name__ == "__main__":
    main()
