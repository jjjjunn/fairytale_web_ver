from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import date

# 회원 가입 시 데이터 검증
class UserCreate(BaseModel):
    username: str
    nickname: str
    email: EmailStr # 이메일 형식 검증 
    password: str # 해시 전 패스워드
    password_confirm: str # 비밀번호 확인
    

# 로그인 시 데이터 검증
class UserLogin(BaseModel):
    username: str # 선택적 필드
    password: str


# 비밀번호 변경 시 데이터 검증
class UserUpdate(BaseModel):
    username: str
    current_password: str # 해시 전 패스워드
    new_password: str
    new_password_confirm: str

# 회원 조회용
class UserResponse(BaseModel):
    id: int
    username: str
    nickname: str
    email: EmailStr

    class Config:
        from_attributes: True

# 회원 조회용
class UserIdRequest(BaseModel):
    id: int