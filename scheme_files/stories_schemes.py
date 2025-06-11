from pydantic import BaseModel, EmailStr
from typing import Optional

# Story 응답용
class StoryResponse(BaseModel):
    id: int
    theme: str
    voice: str
    content: str
    voice_content: str
    image: str
    bw_image: str
    created_at: str

    class Config:
        from_attributes: True # SQLAlchemy 모델을 자동으로 JSON 변환할 수 있게 함

# 동화 생성 클래스
class StoryRequest(BaseModel):
    name: str
    theme: str

# 동화 저장 클래스
class SaveStoryRequest(BaseModel):
    user_id: int
    theme: str
    voice: str
    content: str
    image: str
    bw_image: str

    class Config:
        orm_mode = True



# 음성 파일 생성 클래스
class TTSRequest(BaseModel):
    text: str

# 이미지 생성 클래스
class ImageRequest(BaseModel):
    text: str

# 음악 검색
class MusicRequest(BaseModel):
    theme: str

# 영상 검색
class VideoRequest(BaseModel):
    theme: str

