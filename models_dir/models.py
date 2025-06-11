from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func, DATE, Text
from sqlalchemy.orm import declarative_base, relationship
from models_dir.database import Base

# index: 열에 대한 검색 기능
# primary_key: PK(주요 키)
# ForeignKey: 외래키
# nullable: Null 값 가능 여부(True: 가능)
# unique: 중복 가능 여부(True: 중복 불가)
# default: 새로운 레코드 삽입 시 해당 열에 값이 제공되지 않을 경우 자동으로 설정할 기본값 저장
# relationship: 데이터 모델 간의 관계 명확화

# 사용자 모델 정의
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True) # 정수형 PK
    username = Column(String(100), index=True, nullable=False, unique=True) # 사용자 이름
    nickname = Column(String(100), unique=True, index=True, nullable=False) # 닉네임
    email = Column(String(200), unique=True, index=True, nullable=False) # 이메일 주소
    hashed_password = Column(String(512), nullable=False)  # 비밀번호
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False, default=1) # 사용자 역할 (역할 테이블 참조)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 관계 설정
    stories = relationship("Story", back_populates="user") # 사용자와 동화 간 관계 (일대다) : 하나의 사용자 여러 개 동화
    articles = relationship("Article", back_populates="user") # 사용자와 게시물 간의 관계 (일대다): 하나의 사용자 여러 개 게시글
    babies = relationship("Baby", back_populates="user") # 사용자와 아기 간의 관계 (일대다): 하나의 사용자 여러 명 아기
    likes = relationship("Like", back_populates="user") # 사용자와 좋아요 간의 관계 (일대다): 하나의 사용자 여러 개의 좋아요
    role = relationship("Role", back_populates="users") # 사용자와 역할 간의 관계 (다대일): 여러 사용자, 각 사용자당 하나의 역할
    
# 게시판 모델 정의
class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True) # 정수형 PK
    user_id = Column(Integer, ForeignKey('users.id')) # 사용자 참조 추가
    image = Column(String(255), nullable=False) # 업로드한 이미지 파일 경로
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 관계 설정
    user = relationship("User", back_populates="articles") # 게시물과 사용자간 관계 (다대일): 하나의 사용자 여러 개 게시글
    likes = relationship("Like", back_populates="article") # 게시물과 사용자간 관계 (일대다): 하나의 게시글 여러 개 좋아요

# 좋아요 기록용 모델 정의
class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True) # 정수형 PK
    user_id = Column(Integer, ForeignKey('users.id')) # 사용자 ID
    article_id = Column(Integer, ForeignKey('articles.id')) # 게시글 ID
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 관계 설정
    user = relationship("User", back_populates="likes") # 좋아요와 사용자간 관계 (다대일): 하나의 사용자, 여러 개의 좋아요
    article = relationship("Article", back_populates="likes") # 좋아요와 게시글 간 관계 (다대일): 하나의 게시글, 여러 개의 좋아요

# 역할 모델 정의
class Role(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True, index=True) # 정수형 PK
    role_name = Column(String(100), nullable=False, unique=True) # null 불가, 중복 불가

    # 관계 설정
    users = relationship("User", back_populates="role") # 역할과 사용자 간의 관계 (일대다): 사용자 당 하나의 역할

# 태아, 아이 모델 정의
class Baby(Base):
    __tablename__ = "babies"
    id = Column(Integer, primary_key=True, index=True) # 정수형 PK
    user_id = Column(Integer, ForeignKey('users.id')) # 사용자 ID
    baby_name = Column(String(100), nullable=False, index=True) # null 값 불가
    baby_gender = Column(String(20), nullable=False) # 성별 null 값 불가
    baby_bday = Column(DATE, nullable=False, index=True) # 출생(예정)일, Null 값 불가
    created_at = Column(TIMESTAMP, server_default=func.now()) # 생성일

    # 관계 설정
    user = relationship("User", back_populates="babies") # 아기와 사용자 간 관계(다대일): 한 명의 사용자, 여러 명의 아기

    def as_dict(self):
        return {
            "id": self.id,
            "baby_name": self.baby_name,
            "baby_gender": self.baby_gender,
            "baby_bday": str(self.baby_bday),
            "user_id": self.user_id
        }

# 동화 모델 정의
class Story(Base):
    __tablename__ = "story"
    id = Column(Integer, primary_key=True, index=True) # 정수형 PK
    user_id = Column(Integer, ForeignKey('users.id')) # 사용자 ID
    theme = Column(String(100), nullable=False, index=True) # 동화 테마
    voice = Column(String(100), nullable=False, index=True) # 동화 목소리
    content = Column(Text, nullable=False) # 내용
    voice_content=Column(Text, nullable=False) # 생성된 음성 파일 경로
    image = Column(Text, nullable=False) # 생성된 이미지 파일 경로
    bw_image = Column(String, nullable=False) # 흑백 이미지 파일 경로
    created_at = Column(TIMESTAMP, server_default=func.now()) # 생성일

    # 관계 설정
    user = relationship("User", back_populates="stories") # 사용자와 동화 간 관계(다대일): 한 명의 사용자, 여러 개의 동화