from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import date

# 아이 생성 시 데이터 검증
class CreateBaby(BaseModel):
    user_id: int # 사용자 ID
    baby_name: str
    baby_gender: str
    baby_bday: date  # 출생(예정)일, date 타입으로 변경

    class Config:
        from_attributes = True  # SQLAlchemy 모델과 호환 가능하게 설정
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "baby_name": "아기",
                "baby_gender": "M",
                "baby_bday": "2025-01-01"
            }
        }

# 아이 조회 시 데이터 검증
class BabyResponse(BaseModel):
    id: int
    user_id: int
    baby_name: str

# 아이 삭제 시 데이터 검증
class DeleteBaby(BaseModel):
    user_id: str
    baby_name: str