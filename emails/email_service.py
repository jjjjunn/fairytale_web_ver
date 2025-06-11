from emails.email_class import EmailServiceBye, EmailServiceFindId, EmailServiceWelcome, EmailServiceSendTempPW, EmailServiceSendNewPW
import logging
from faker import Faker
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import text
from models_dir.models import User

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 임시비밀번호 생성
fake = Faker()

# 환영 이메일 전송
def send_welcome_email(email: str):
    # 이메일 전송
    email_service = EmailServiceWelcome() # EmailServiceWelcome 클래스 인스턴스 생성
    try:
        email_service.send_email(receiver_email=email) # 이메일 전송
        logger.info(f"환영 이메일을 {email}로 전송")
    except Exception as e:
        # 전송 실패 시 에러 메시지 반환
        logger.error(f"이메일 전송 실패: {e}")

# 탈퇴 이메일 전송
def send_bye_email(email: str):
    # 이메일 전송
    email_service = EmailServiceBye() # EmailServiceBye 클래스 인스턴스 생성
    try:
        email_service.send_email(receiver_email=email) # 이메일 전송
        logger.info(f"탈퇴 이메일을 {email}로 전송")
    except Exception as e:
        # 전송 실패 시 에러 메시지 반환
        logger.error(f"이메일 전송 실패: {e}")

# 사용자 이름 이메일 전송 (사용자 찾기)
def send_username_email(email: str, username: str):
    email_service = EmailServiceFindId() # EmailServiceFindId 클래스 인스턴스 생성
    try:
        email_service.send_email(receiver_email=email, username=username)
        logger.infor(f"사용자 이름 정보를 {email}로 전송")
    except Exception as e:
        logger.error(f"이메일 전송 실패: {e}")

# 임시 비밀번호 생성 함수
def generate_temp_pw() -> str:
    return fake.password()

# 비밀번호 업데이트 함수
def update_user_password(db: Session, user: User, new_password: str):
    # 비밀번호 해시 설정
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user.hashed_password = pwd_context.hash(new_password) # 비밀번호 해싱

    try:
        # SQL 문을 text() 함수로 감싸기
        db.execute(
            text("UPDATE users SET hashed_password = :hashed_password WHERE username = :username"),
            {"hashed_password": user.hashed_password, "username": user.username}
        )
        db.commit() # DB 커밋
        logger.info(f"사용자 ID {user.username}의 비밀번호가 업데이트 되었습니다.")
    except Exception as e:
        db.rollback() # DB 롤백
        logger.error(f"비밀번호 업데이트 실패: {e}")
        raise

# 임시 비밀번호 이메일 전송
def send_temp_pw_email(email: str, username: str, temp_password: str):
    email_service = EmailServiceSendTempPW() # EmailServiceSendTempPW 클래스 인스턴스 생성
    try:
        email_service.send_email(receiver_email=email, username=username, temp_password=temp_password)
        logger.info(f"사용자 {username}의 임시 비밀번호를 {email}로 전송했습니다.")
    except Exception as e:
        logger.error(f"이메일 전송 실패: {e}") # 에러 로깅

# 비밀번호 변경 안내 이메일 전송
def send_changed_pw_email(email: str, username: str):
    # 이메일 전송
    email_service = EmailServiceSendNewPW() # EmailServiceSendNewPW 클래스 인스턴스 생성
    try:
        email_service.send_email(receiver_email=email, username=username) # 이메일 전송
        logger.info(f"비밀번호 변경 안내 이메일을 {email}로 전송했습니다.")
    except Exception as e:
        # 이메일 전송 실패 시 에러 메시지 반환
        logger.error(f"이메일 전송 실패: {e}") # 에러 로깅