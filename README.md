# 📖 AI 동화 생성봇

아이를 위한 맞춤형 동화를 생성해주는 AI 기반 웹 애플리케이션입니다.  
**동화 생성, TTS 음성 읽기, 이미지 변환, 자장가 추천, 유튜브 영상 검색 등** 다양한 기능을 제공합니다.
<br>**Python** 으로만 만든 프로젝트 입니다.

> ⏱️ 프로젝트 기간: **2025년 5월 17일 ~ 2025년 6월 12일**  
> 🛠️ 주요 언어: `FastAPI`, `Python`, `PostgreSQL`

<br>

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red?logo=streamlit)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)
![OpenAI](https://img.shields.io/badge/OpenAI-API-4B0082?logo=openai)
![Jamendo](https://img.shields.io/badge/Jamendo-API-ff69b4?logo=musicbrainz)
![OpenCV](https://img.shields.io/badge/Image-OpenCV-5C3EE8?logo=opencv)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=PostgreSQL&logoColor=white)

---

## 🚀 주요 기능

| 기능 구분 | 상세 내용 |
|----------|-----------|
| 👶 **회원 & 아이 관리** | - 회원가입/로그인/탈퇴<br>- 아이 등록 및 생년월일 기반 출생일 계산 |
| 📘 **동화 생성** | - 테마를 선택하면 AI가 동화 생성<br>- GPT-4o-mini 사용 (max_tokens 16384) |
| 🔊 **TTS 음성 읽기** | - OpenAI TTS 사용<br>- 다양한 목소리 선택 (10종 이상)<br>- 재생 속도 조절 기능 |
| 🎨 **이미지 생성 & 변환** | - Stability AI 기반 이미지 생성<br>- 흑백 변환을 통한 컬러링북 스타일 제공 |
| 🖼 **갤러리** | - 사용자별 이미지 및 동화 확인<br>- 다운로드 및 공유 가능 |
| 🎵 **자장가 찾기** | - 테마별 무료 자장가 음원 추천 (Jamendo API 사용) |
| 📺 **유튜브 영상 추천** | - 테마 관련 유튜브 영상 5개 자동 검색 및 제공 |

---

## 🔧 사용 기술 스택

| 영역 | 기술 스택 |
|------|------------|
| **Frontend** | Streamlit |
| **Backend** | FastAPI |
| **Database** | PostgreSQL |
| **AI 모델** | OpenAI GPT-4o-mini, TTS API |
| **이미지 생성** | Stability AI (DALL·E 3 → 교체됨) |
| **음악 API** | Jamendo API |
| **영상 추천** | Google YouTube API |
| **이미지 처리** | OpenCV |
| **기타 기능** | 이메일 발송, 임시 비밀번호, 비밀번호 변경, 회원 탈퇴, 컨텐츠 삭제 등 |

---

## ERD
![ERD](assets/ERD.png)


---

## 🆕 v1.2 변경사항 (2025.06.12)

- 🎨 **이미지 생성 모델 변경:** DALL·E → Stability AI
- 🧠 **모델 교체:** gpt-3.5-turbo → gpt-4o-mini (max_tokens: 16384)
- 🗣 **TTS 업데이트:** 목소리 3종 추가, 임시 파일 없이 실시간 음성 재생 지원

---

## 📁 프로젝트 구조 예시

```bash
📦fairytale_web_ver
├── controllers/        # 앱 관련 주요 기능 구현
├── emails/             # 회원 활동 관련 email 발송 기능 구현
├── frontend/           # Streamlit 앱
├── img/                # 프론트엔드에 사용되는 이미지
├── models_dir/         # 데이터베이스 관련
├── scheme_files/       # 아이, 컨텐츠, 사용자 관련 클래스
├── ai_server.py        # ai 서버 (FastAPI)
├── main.py             # 앱의 진입점
├── requirements.txt    # 사용된 모듈, 라이브러리 버전 관리용
└── README.md           # 프로젝트 설명
```
---

## 📖 프로젝트 목표 및 학습 과정
- ✅ FastAPI + PostgreSQL을 활용한 CRUD 구현
- ✅ 사용자별 데이터 분리 및 보안 처리
- ✅ 백엔드와 프런트엔드 연동 경험
- ✅ BackgroundTasks를 이용한 비동기 이메일 전송
- ✅ 다양한 AI API 활용

---

## 📝 개발 기록 (블로그 제작기)
| 주제 | 링크 |
|------|------|
| 🔧 프로젝트 개요 | [바로가기](https://puppy-foot-it.tistory.com/909) |


---

## 🧭 향후 계획 (Roadmap)

-   [ ] **관리자 모드 도입:** 관리자 모드를 도입하여 관리자가 사용자의 모든 컨텐츠를 관리할 수 있도록 개선
-   [ ] **대시보드 적용:** 사용자의 활동을 기록하고 보여줄 수 있는 대시보드 도입
-   [ ] **소셜로그인 구현:** 사용자의 편의성을 극대화하기 위해 소셜로그인 구현
-   [ ] **게시판 도입**: 생성된 흑백 이미지를 사용자가 직접 색칠한 후 게시판에 업로드하여 좋아요 및 댓글 기능이 가능한 커뮤니티 기능 구현
-   [ ] **CI/CD**: 실제 사용자를 위한 클라우드 서버로의 배포 및 자동화된 배포 파이프라인 구축
---


## 📜 라이선스 (License)

이 프로젝트는 [MIT License](LICENSE) 를 따릅니다.
