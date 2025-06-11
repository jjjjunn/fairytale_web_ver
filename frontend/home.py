import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="엄빠, 읽어도!",
    page_icon="📖",
    # layout="wide"
)

from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from utils import initialize_session_state
import logging
from PIL import Image
from datetime import datetime, date

# home.py 기준 fairytale 폴더 절대경로
fairytale_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(fairytale_path)

from models_dir.models import User, Baby  # User, Baby 모델 추가 import
from controllers.dependencies import get_db


# 로그 설정
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 홈페이지 콘텐츠 함수
def show_home_content():
    """홈페이지 콘텐츠 표시"""
    if not st.session_state.get("logged_in"):
        show_login_home()
    else:
        show_main_home()

def show_login_home():
    """로그인하지 않은 사용자용 홈페이지"""
    st.title("📖 엄빠, 읽어도! 📖")
    st.markdown("### 아이와 함께 쓰는 세상에 단 하나뿐인 이야기")
    
    st.info("로그인 후 모든 기능을 이용하실 수 있습니다.")
    
    # 미리보기 이미지
    img_path = Path(__file__).parent / "img" / "readwith2.png"
    if img_path.exists():
        st.image(str(img_path), use_container_width=True)
    else:
        st.info("이미지를 찾을 수 없습니다.")

    # st.image("./img/readwith2.png") # 배포용

    # img_path = Path("G:\my_fastapi\fairytale\img\readwith2.png")
    
    # if img_path.exists():
    #     image = Image.open(img_path)
    #     st.image(image, use_container_width=True)
    # else:
    #     st.info("이미지를 찾을 수 없습니다.")
        
    st.markdown("""
    ### 🌟 우리 서비스의 특징
    
    - 📚 **개인화된 동화**: 아이의 이름과 특성을 반영한 맞춤 동화
    - 🎵 **자장가 음악**: 아이를 위한 특별한 자장가 생성
    - 🎥 **영상 콘텐츠**: 동화와 음악이 결합된 영상 제작
    - 🖼️ **갤러리**: 만든 콘텐츠를 한 곳에서 관리
    
    ### 🎯 지금 시작해보세요!
    """)
    st.write("👈 왼쪽 사이드바의 '로그인' 메뉴를 클릭해주세요!")

# 아이 출생일 가져오기
def get_baby_birthdate(user_id):
    """사용자의 아이 출생일을 가져오는 함수"""
    db = next(get_db())  # Streamlit 용
    baby = db.query(Baby).filter(Baby.user_id == user_id).first()
    if baby:
        return baby.baby_bday, baby.baby_name
    else:
        logging.warning(f"사용자 {user_id}의 아이 정보가 없습니다.")
        st.error("아이 정보를 찾을 수 없습니다. 먼저 프로필에서 아이를 추가해주세요.")
        st.stop()

def show_main_home():
    """로그인한 사용자용 홈페이지"""
    # 헤더
    st.title("Read With Mom 🧡 Dad")
    st.markdown("### 📖 아이와 함께 쓰는 세상에 단 하나뿐인 이야기 📖")
    
    # 로그인 상태 표시
    username = st.session_state.get("username", "사용자")
    st.success(f"✅ {username}님 환영합니다!")
    
    # 사이드바에 로그아웃 버튼
    if st.sidebar.button("🔓 로그아웃"):
        logging.info(f"사용자 {st.session_state.get('username')}님이 로그아웃했습니다.")
        for key in ["logged_in", "username"]: # 로그아웃 시 세션 상태를 완전히 초기화
            st.session_state[key] = None
        st.rerun()

    # 아이 출생일 가져오기
    user_id = st.session_state.get("user_id")
    baby_birth_date, baby_name = get_baby_birthdate(user_id)

    # 출생일 표시
    if baby_birth_date:
        if isinstance(baby_birth_date, str):
            try:
                baby_birth_date = datetime.strptime(baby_birth_date, "%Y-%m-%d").date()
            except Exception:
                st.warning("출생일 정보를 불러오는 데 문제가 발생했습니다.")
        today = date.today()
        days_until_birth = (baby_birth_date - today).days
        if days_until_birth > 0:
            st.info(f"🍼 {baby_name} 출생 예정일: {baby_birth_date.strftime('%Y년 %m월 %d일')} (D-{days_until_birth})")
        elif days_until_birth == 0:
            st.success(f"🎉 오늘은 {baby_name}의 출생 예정일입니다! 축하합니다! 🎉")
            st.balloons()
        else:
            st.info(f"👶 {baby_name} 출생일: {baby_birth_date.strftime('%Y년 %m월 %d일')} (출생한 지 {-days_until_birth}일 지났어요)")
    else:
        st.warning("아이의 출생일 정보가 없습니다. 설정 페이지에서 입력해주세요.")


    st.markdown(f"""
    ## 🎉 환영합니다, {st.session_state.get('username', '사용자')}님!
    
    ### 🌟 오늘 뭘 해볼까요?
    """)
    
    # 빠른 액세스 메뉴 - 사이드바 네비게이션 가이드
    st.info("👈 왼쪽 사이드바에서 원하는 기능을 선택해주세요!")

# 메인 함수
def main():
    initialize_session_state()
    
    # .env 파일에서 환경 변수 로드
    load_dotenv()
    API_URL = os.getenv("API_URL")

    if not API_URL:
        st.error("환경 변수 API_URL이 설정되지 않았습니다!")
        st.stop()

    # 네비게이션 설정
    from streamlit import navigation, Page

    # 페이지 정의
    if st.session_state.get("logged_in"):
        pages = [
            Page(show_home_content, title="홈", icon="🏠"),
            Page("pages/stories.py", title="동화 만들기", icon="📚"),
            Page("pages/gallery.py", title="갤러리", icon="🖼️"),
            Page("pages/musics.py", title="자장가 음악", icon="🎵"),
            Page("pages/videos.py", title="자장가 유튜브", icon="🎥"),
            Page("pages/profiles.py", title="프로필", icon="👤")
        ]
    else:
        pages = [
            Page(show_home_content, title="홈", icon="🏠"),
            Page("pages/_login.py", title="로그인", icon="🔑"),
            Page("pages/_signup.py", title="회원가입", icon="📝"),
            Page("pages/_settings.py", title="설정", icon="⚙️")
        ]

    # 네비게이션 실행
    nav = navigation(pages)
    nav.run()

# 앱 실행
if __name__ == "__main__":
    main()