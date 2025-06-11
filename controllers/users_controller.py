from fastapi import Request, Depends, HTTPException, APIRouter, BackgroundTasks, status
from sqlalchemy.orm import Session
from models_dir.models import User, Article, Story, Role # 모델 import
from scheme_files.users_schemes import UserCreate, UserLogin, UserResponse, UserUpdate
from controllers.dependencies import get_db, get_password_hash, verify_password # 의존성 import
import re
import logging
from passlib.context import CryptContext
from emails.email_class import EmailRequest, UsernameEmailRequest
from emails.email_service import send_bye_email, send_welcome_email, send_username_email, generate_temp_pw, send_temp_pw_email, update_user_password, send_changed_pw_email

router = APIRouter()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 비밀번호 규칙 확인
password_regex = re.compile(r"""
    (?=.*[a-z])          # 적어도 하나의 소문자
    (?=.*[A-Z])          # 적어도 하나의 대문자
    (?=.*\d)             # 적어도 하나의 숫자
    (?=.*[@$!%*?&\-_+=<>]) # 적어도 하나의 특수문자
    .{10,}               # 길이는 10자 이상
""", re.VERBOSE)

# 회원가입
@router.post("/signup")
async def signup(signup_data: UserCreate, background_tasks: BackgroundTasks, db:Session=Depends(get_db)):
    logger.info(f"회원 가입 요청: 사용자 이름 {signup_data.username}, 이메일: {signup_data.email}")

    # ID 규칙 확인
    if not re.fullmatch(r"[a-z0-9]+", signup_data.username):
        logger.warning("회원 가입 실패: 사용자 규칙 위반")
        raise HTTPException(status_code=400, detail="사용자 이름은 영어 소문자와 숫자로만 구성되어야 합니다.")
    
    # 비밀번호 규칙 확인
    if not password_regex.match(signup_data.password):
        logger.warning("회원 가입 실패: 비밀번호 규칙 위반")
        raise HTTPException(status_code=400, detail="비밀번호는 최소 10자 이상이며, 대문자, 소문자, 숫자 및 특수문자가 포함돼야 합니다.")
    
    # 비밀번호 확인 일치 검사
    if signup_data.password != signup_data.password_confirm:
        logger.warning("비밀번호가 일치하지 않습니다.")
        raise HTTPException(status_code=400, detail="비밀번호가 서로 일치하지 않습니다.")
    
    # username 중복 확인
    existing_user = db.query(User).filter(User.username == signup_data.username).first()
    if existing_user:
        logger.warning(f"회원 가입 실패: 이미 존재하는 사용자 이름 - {signup_data.username}")
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자 이름입니다.")
    
    # nickname 중복 확인
    existing_nick = db.query(User).filter(User.nickname == signup_data.nickname).first()
    if existing_nick:
        logger.warning(f"회원 가입 실패: 이미 존재하는 닉네임 - {signup_data.nickname}")
        raise HTTPException(status_code=400, detail="이미 존재하는 닉네임입니다.")

    # 모든 조건 만족 시
    hashed_password = get_password_hash(signup_data.password) # 비밀번호 해시
    # 기본 role_id 설정 (예: 일반 사용자)
    DEFAULT_ROLE_ID = 1
    new_user = User(username=signup_data.username,
                    nickname=signup_data.nickname,
                    email = signup_data.email, 
                    hashed_password=hashed_password,
                    role_id=DEFAULT_ROLE_ID
                    )
    db.add(new_user)
    logger.info(f"{new_user.username} 사용자가 데이터베이스에 추가 되었습니다.")

    try:
        db.commit()
        logger.info("데이터베이스에 새로운 사용자가 추가되었습니다.")
    except Exception as e:
        db.rollback() # 에러 발생 시 롤백
        logger.error(f"회원 가입 오류: {e}") # 에러 내용 출력
        raise HTTPException(status_code=500, detail="회원 가입 실패. 다시 시도해 주세요")
    db.refresh(new_user)

    # 백그라운드 작업 등록
    background_tasks.add_task(send_welcome_email, new_user.email)
    logger.info(f"회원 가입 후 사용자 {new_user.username}에게 환영 이메일 발송")

    return {"message": "회원가입을 성공하였습니다. 이메일을 확인해 주세요."}

# 로그인
@router.post("/login")
async def login(request:Request, signin_data: UserLogin, db: Session=Depends(get_db)):
    logger.info(f"로그인 시도: 사용자 이름 {signin_data.username}")

    user = db.query(User).filter(User.username ==  signin_data.username).first()

    if not user:
        logger.warning(f"로그인 실패: 사용자 {signin_data.username}이 존재하지 않음.")
        raise HTTPException(status_code=404, detail="존재하지 않는 사용자입니다.")
    
    if user and verify_password(signin_data.password, user.hashed_password):
        request.session["username"] = user.username
        request.session["id"] = user.id
        logger.info(f"사용자 {user.username} 로그인 성공")
        return {
            "message": "로그인 성공!",
            "user_id": user.id,  # 명시적으로 user_id 포함
            "username": user.username
        }
    else:
        logger.warning(f"로그인 실패: 사용자 {signin_data.username}에 대한 인증 정보가 잘못되었습니다.")
        raise HTTPException(status_code=401, detail="로그인이 실패하였습니다.")

# 아이디 찾기 (이메일 발송)
@router.post("/find_id")
async def find_id(req: EmailRequest, db:Session=Depends(get_db)):
    email = req.email
    logger.info(f"사용자 이름 요청: 이메일 {email}")

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        logger.warning(f"사용자 이름 요청 실패: 해당 이메일로 등록된 사용자가 없습니다. 이메일: {email}")
        raise HTTPException(status_code=404, detail="해당 이메일로 등록된 사용자가 없습니다.")
    
    # 사용자 이름 이메일 발송
    try:
        send_username_email(email=email, username=user.username)
        logger.info(f"사용자 이름: {user.username}을 {email}로 성공적으로 발송하였습니다.")
    except Exception as e:
        logger.error(f"이메일 전송 실패: {e}")
        raise HTTPException(status_code=500, detail="이메일 전송에 실패하였습니다. 다시 시도해 주세요")
    
    return {"success": True, "message": "사용자 이름이 이메일로 발송되었습니다.",
            "username": user.username}


# 임시 비밀번호 이메일 발송
@router.post("/reset_password")
async def reset_password(req: UsernameEmailRequest, db: Session = Depends(get_db)):
    username = req.username
    email = req.email
    logger.info(f"비밀번호 재설정 아이디: 아이디 {username}, 이메일 {email}")

    user = db.query(User).filter(User.username == username, User.email == email).first()

    if user is None:
        logger.warning(f"비밀번호 재설정 실패; 일치하는 정보가 없습니다. 아이디: {username}, 이메일: {email}")
        raise HTTPException(status_code=404, detail="일치하는 정보가 없습니다.")
    
    # 임시비밀번호 생성 및 DB 업데이트
    temp_password = generate_temp_pw() # 임시 비밀번호 생성

    # 비밀번호 DB 업데이트
    try:
        update_user_password(db, user, temp_password)
    except:
        logger.error(f"사용자 ID {user.username}에 대한 비밀번호 업데이트가 실패하였습니다.")
        raise HTTPException(status_code=500, detail="비밀번호 업데이트에 실패하였습니다.")
    
    # 임시비밀번호 이메일 발송
    try:
        send_temp_pw_email(email=email, username=username, temp_password=temp_password)
        logger.info(f"임시 비밀번호를 {email}로 성공적으로 전송했습니다.")
    except Exception as e:
        logger.error(f"이메일 전송 실패: {e}")
        raise HTTPException(status_code=500, detail="이메일 전송에 실패하였습니다. 다시 시도해 주세요")
    
    return {"succes": True, "message": "임시비밀번호가 이메일로 발송되었습니다."}

# 비밀번호 변경
@router.put("/change_pw")
async def update_password(req: UserUpdate, db: Session = Depends(get_db)):
    username = req.username
    current_password = req.current_password # 현재 비밀번호
    new_password = req.new_password # 새 비밀번호
    new_password_confirm = req.new_password_confirm # 새 비밀번호 확인

    logger.info(f"비밀번호 변경 요청: 아이디 {username}")

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        logger.warning(f"비밀번호 변경 실패: 사용자 ID {username}이 존재하지 않습니다.")
        raise HTTPException(status_code=404, detail="사용자가 존재하지 않습니다")
    
    # 현재 비밀번호 확인
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    if not pwd_context.verify(current_password, user.hashed_password):
        logger.warning(f"비밀번호 변경 실패: 현재 비밀번호가 일치하지 않습니다.")
        raise HTTPException(status_code=403, detail="현재 비밀버호가 일치하지 않습니다.")
    
    # 현재 비밀번호와 새 비밀번호가 같은지 확인
    if current_password == new_password:
        logger.warning("비밀번호 변경 실패: 현재 비밀번호와 새로운 비밀번호가 같습니다.")
        raise HTTPException(status_code=400, detail="새로운 비밀번호는 현재 비밀번호와 달라야 합니다.")
    
    # 새로운 비밀번호와 확인 비밀번호가 같은지 확인
    if new_password != new_password_confirm:
        logger.warning("비밀번호 변경 실패: 새로운 비밀번호와 확인 비밀번호가 같지 않습니다.")
        raise HTTPException(status_code=400, detail="새로운 비밀번호와 비밀번호 확인이 일치하지 않습니다")
    
    # 비밀번호 규칙 확인
    if not password_regex.match(new_password):
        logger.warning("비밀번호 변경 실패: 비밀번호 규칙 위반")
        raise HTTPException(status_code=400, detail="비밀번호는 최소 10자 이상이며, 대문자, 소문자, 숫자 및 특수문자가 포함돼야 합니다.")
    
    # 비밀번호 업데이트 처리
    update_user_password(db, user, new_password) # 기존 함수 호출하여 비밀번호 업데이트

    # 비밀번호 변경 안내 이메일 발송
    try:
        send_changed_pw_email(email=user.email, username=username)
        logger.info(f"비밀번호 변경 안내 이메일을 {user.email}로 성공적으로 전송했습니다.")
    except Exception as e:
        logger.error(f"이메일 전송 실패: {e}")
        raise HTTPException(status_code=500, detail="이메일 전송에 실패했습니다. 다시 시도해 주세요")
    
    return {"success": True, "message": "비밀번호가 성공적으로 변경되었습니다."}

# 회원 탈퇴
@router.delete("/users/{id}")
async def delete_user(request: Request, id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    logger.info(f"회원 탈퇴 요청: {id}")

    user_id = request.session.get("id") # 사용자 ID
    
    if user_id is None:
        logger.warning("세션에 ID가 없음")
        raise HTTPException(status_code=401, detail="Not Authorized")

    # 사용자를 user_id로 조회
    user_query = db.query(User)

    if user_id is not None:
        user_query = user_query.filter(User.id == user_id)

    user = user_query.first()

    if user is None:
        logger.error(f"사용자 찾기 실패: ID {user_id}에 대한 사용자가 존재하지 않음")
        raise HTTPException(status_code=404, detail="User를 찾을 수 없습니다")
    
    # 사용자가 작성한 모든 동화 삭제
    stories = db.query(Story).filter(Story.user_id == user_id).all()
    logger.info(f"{len(stories)}개의 동화를 삭제합니다.")
    for story in stories:
        db.delete(story)
    
    # 사용자가 작성한 모든 게시글 삭제
    articles = db.query(Article).filter(Article.user_id == user_id).all()
    logger.info(f"{len(articles)}개의 게시글을 삭제합니다.")
    for article in articles:
        db.delete(article)

    # 사용자 정보 삭제
    db.delete(user)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"회원 탈퇴 오류: {e}") # 탈퇴 에러 내용 출력
        raise HTTPException(status_code=500, detail="회원 탈퇴에 실패하였습니다. 다시 시도해 주세요")
    
    # 세션 비우기
    request.session.clear()

    # 탈퇴 안내 이메일 발송
    background_tasks.add_task(send_bye_email, user.email)

    # 탈퇴 성공 응답 리턴
    logger.info(f"회원 탈퇴 완료: 사용자 ID {user_id}에게 탈퇴 안내 이메일 발송")
    return {"success": True, "message": "회원 탈퇴가 완료되었습니다."}

