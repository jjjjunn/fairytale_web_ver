import os
import openai
import tempfile
from playsound import playsound
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
from models_dir.models import Story
from sqlalchemy.orm import Session
from models_dir.database import SessionLocal
from io import BytesIO
import requests
import cv2
import numpy as np
from PIL import Image
import logging
from uuid import uuid4
from models_dir.models import User
from controllers.storage_s3 import save_image_s3
from controllers.cache import CacheManager, Config
import sys
from functools import lru_cache
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from frontend.utils import ImageSharingUtils
import base64

# 현재 파일의 상위 폴더인 'fairytale'을 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# 로그 설정
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()  # .env 파일에서 환경변수 로드

# OpenAI API 키 가져오기
openai_api_key = os.getenv('OPENAI_API_KEY')

# 1. 변수에 값 할당하기
#openai_api_key = st.secrets["OpenAI"]["OPENAI_API_KEY"]

# 2. 값이 없으면 에러 처리
if not openai_api_key:
    raise ValueError("환경변수 'OPENAI_API_KEY'가 설정되지 않았습니다.")

# 3. openai에 API 키 등록
openai.api_key = openai_api_key

client = OpenAI(api_key=openai_api_key)

# 전역 캐시 매니저
cache_manager = CacheManager()


# 동화 생성 함수 (캐싱 적용)
@lru_cache(maxsize=50)
def generate_fairy_tale(name: str, thema: str) -> Optional[str]:

    # 캐시 확인
    content_key = f"{name}_{thema}"
    cached_story = cache_manager.get_cached_file(content_key, "story")

    if cached_story:
        try:
            with open(cached_story, 'r', encoding='utf-8') as f:
                logging.info("캐시된 동화를 사용합니다.")
                return f.read()
        except Exception as e:
            logging.warning(f"캐시된 동화 읽기 실패: {e}")

    prompt = (
        f"""
        너는 동화 작가야.
        '{thema}'를 주제로, '{name}'이 주인공인 길고 아름다운 동화를 써줘.
        엄마가 아이에게 읽어주듯 다정한 말투로 써줘.
        """
    )
    try:
        completion = client.chat.completions.create(
            # model=Config.OPENAI_MODEL,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            # max_tokens=Config.MAX_TOKENS,
            max_tokens=16384,
            temperature=0.5
        )
        fairy_tale_text = completion.choices[0].message.content

        # 스토리를 캐시에 저장
        temp_story_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
        temp_story_file.write(fairy_tale_text)
        temp_story_file.close()
        
        cache_manager.cache_file(content_key, "story", temp_story_file.name)
        os.unlink(temp_story_file.name)  # 임시 파일 삭제
        
        return fairy_tale_text

    except Exception as e:
        return f"동화 생성 중 오류 발생: {e}"


# OpenAI TTS를 사용하여 음성 데이터 생성 (파일 저장 없음)
def generate_openai_voice(text, voice="alloy", speed=1.0):
    try:
        # TTS 음성 생성
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=speed
        )
        
        # 바이너리 데이터 직접 반환
        return response.content
        
    except Exception as e:
        print(f"TTS 생성 오류: {e}")
        return None

def audio_to_base64(audio_data):
    """
    오디오 바이너리 데이터를 Base64로 인코딩
    모바일 앱에서 사용하기 위함
    """
    if audio_data:
        return base64.b64encode(audio_data).decode('utf-8')
    return None

# 프롬프트 생성 함수 (staility_sdxl는 영어만 처리 가능)
def generate_image_prompt_from_story(fairy_tale_text: str) -> Optional[str]:
    """
    동화 내용을 기반으로 이미지 생성용 영어 프롬프트 생성
    """
    try:
        system_prompt = (
            "You are a prompt generator for staility_sdxl. "
            f"From the given {fairy_tale_text}, choose one vivid, heartwarming scene. "
            "Describe it in English in a single short sentence suitable for generating a simple, child-friendly fairy tale illustration style. "
            "Use a soft, cute, minimal detail. "
            "No text, no words, no letters, no signs, no numbers."
        )

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음은 동화야:\n\n{fairy_tale_text}\n\n이 동화에 어울리는 그림을 그릴 수 있도록 프롬프트를 영어로 짧게 써줘."}
            ],
            temperature=0.5,
            max_tokens=150
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"이미지 프롬프트 생성 오류: {e}")
        return None



# 이미지 생성 함수 (캐싱 적용)
# def generate_image_from_prompt(image_prompt: str, image_key: str) -> Optional[str]:
#     cached_image = cache_manager.get_cached_file(image_key, "image")
    
#     if cached_image:
#         logging.info("캐시된 이미지를 사용합니다.")
#         return cached_image

#     try:
#         response = client.images.generate(
#             model="dall-e-3",
#             prompt=image_prompt,
#             size=Config.IMAGE_SIZE,
#             quality="standard",
#             n=1
#         )
        
#         if hasattr(response, "data") and response.data and len(response.data) > 0:
#             image_url = response.data[0].url
            
#             image_data = requests.get(image_url).content
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
#                 tmp_file.write(image_data)
#                 tmp_path = tmp_file.name
            
#             cached_path = cache_manager.cache_file(image_key, "image", tmp_path)
#             os.unlink(tmp_path)
            
#             return cached_path

#         else:
#             logging.error("이미지 생성 실패: 응답이 비어 있거나 형식이 잘못됨.")
#             return None

#     except Exception as e:
#         logging.error(f"이미지 생성 중 오류 발생: {e}")
#         return None

# 중복되지 않는 파일명 생성 함수
def get_available_filename(base_name: str, extension: str = ".png", folder: str = ".") -> str:
    """
    중복되지 않는 파일명을 자동으로 생성
    예: fairy_tale_image.png, fairy_tale_image_1.png, ...
    """
    counter = 0
    while True:
        filename = f"{base_name}{f'_{counter}' if counter > 0 else ''}{extension}"
        filepath = os.path.join(folder, filename)
        if not os.path.exists(filepath):
            return filepath
        counter += 1

# 이미지 생성 함수 (캐싱 적용)
def generate_image_from_prompt(fairy_tale_text: str, image_key: str) -> Optional[str]:
    cached_image = cache_manager.get_cached_file(image_key, "image")
    
    if cached_image:
        logging.info("캐시된 이미지를 사용합니다.")
        return cached_image
    
    try:
        endpoint = "https://api.stability.ai/v2beta/stable-image/generate/core"
        
        
        # 동화 프롬프트 처리
        base_prompt = generate_image_prompt_from_story(fairy_tale_text)
        if not base_prompt:
            st.error("이미지 프롬프트 생성에 실패했습니다.")
            return None

        prompt = (
            "no text in the image "
            "Minimul detail "
            f"Please create a single, simple illustration that matches the content about {base_prompt}, in a child-friendly style. "
        )

        headers = {
            "Authorization": f"Bearer {os.getenv('STABILITY_API_KEY')}",
            # "Authorization": f"Bearer {st.secrets['STABILITY_API_KEY']['STABILITY_API_KEY']}",
            "Accept": "image/*",
        }

        # multipart/form-data 형태로 데이터 전송
        files = {
            "prompt": (None, prompt),
            "model": (None, "stable-diffusion-xl-512-v1-0"),
            "output_format": (None, "png"),
            "height": (None, "512"),
            "width": (None, "512"),
            "seed": (None, "1234")
        }

        response = requests.post(endpoint, headers=headers, files=files)

        if response.status_code == 200:
            save_path = get_available_filename("fairy_tale_image", ".png", folder=".")
            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"이미지 저장 완료: {save_path}")
            return save_path
        else:
            print("이미지 생성 실패:", response.status_code)
            print("응답 내용:", response.text)
            return None

    except Exception as e:
        print(f"이미지 생성 중 오류 발생:\n{e}")
        return None


# 흑백 이미지 변환(캐싱 적용, staility_sdxl 이미지 용)
def convert_bw_image(image_path: str) -> Optional[str]:
    if not image_path or not os.path.exists(image_path):
        return None
    
    # 캐시 확인
    bw_key = f"bw_{os.path.basename(image_path)}"
    cached_bw = cache_manager.get_cached_file(bw_key, "image")
    
    if cached_bw:
        logging.info("캐시된 흑백 이미지를 사용합니다.")
        return cached_bw

    # URL인지 로컬 파일인지 판단
    if image_path.startswith(('http://', 'https://')):
        # URL에서 이미지 다운로드
        response = requests.get(image_path)
        image = Image.open(BytesIO(response.content)).convert("RGB")
    else:
        # 로컬 파일에서 이미지 로드
        image = Image.open(image_path).convert("RGB")

    try:
        # Numpy 배열로 변환
        np_image = np.array(image)

        # 흑백 변환
        gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)

        # 가우시안 블러로 노이즈 제거
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # 캐니 엣지 디텍션 (더 부드러운 선)
        edges = cv2.Canny(blurred, 50, 150)
        
        # 선 두께 조절
        kernel = np.ones((2,2), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=1)
        
        # 흰 배경에 검은 선
        line_drawing = 255 - dilated_edges
        
        # 이미지 저장
        pil_image = Image.fromarray(line_drawing)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            pil_image.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        cached_path = cache_manager.cache_file(bw_key, "image", tmp_path)
        os.unlink(tmp_path)  # 임시 파일 삭제
        
        return cached_path

    except Exception as e:
        logging.error(f"흑백 변환 오류: {e}")
        return None


# 통합 함수: 동화 텍스트로부터 이미지 생성
def generate_image_from_fairy_tale(fairy_tale_text: str) -> Optional[str]:
    """
    동화 텍스트를 받아서 이미지 생성용 프롬프트를 만들고, 
    그 프롬프트로 이미지를 생성하는 통합 함수
    """
    try:
        # 1단계: 동화에서 이미지 프롬프트 생성
        logging.info("동화에서 이미지 프롬프트 생성 중...")
        image_prompt = generate_image_prompt_from_story(fairy_tale_text)
        
        if not image_prompt:
            logging.error("이미지 프롬프트 생성 실패")
            return None
        
        logging.info(f"생성된 이미지 프롬프트: {image_prompt}")
        
        # 2단계: 생성된 프롬프트로 이미지 생성
        # 캐시 키 생성 (프롬프트 기반)
        image_key = f"img_{hash(image_prompt) % 1000000}"
        
        logging.info("프롬프트로 이미지 생성 중...")
        image_path = generate_image_from_prompt(image_prompt, image_key)
        
        if image_path:
            logging.info(f"이미지 생성 완료: {image_path}")
        else:
            logging.error("이미지 생성 실패")
        
        return image_path
        
    except Exception as e:
        logging.error(f"동화 이미지 생성 전체 과정 중 오류: {e}")
        return None


# 사용자 정보 받아오기
def get_username_by_id(user_id: int, db: Session) -> str:
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user.username if user else f"user_{user_id}"
    except Exception as e:
        print(f"사용자 정보 조회 중 오류 발생: {e}")
        return f"user_{user_id}"

# 이미지 저장 (S3/로컬 선택)
def save_image_locally(image_path: str, save_path: str) -> Optional[str]:
    try:
        if image_path.startswith("http"):
            image_data = requests.get(image_path).content
            with open(save_path, "wb") as f:
                f.write(image_data)
        else:
            img = Image.open(image_path)
            img.save(save_path)
        return save_path
    except Exception as e:
        logging.error(f"이미지 저장 중 오류 발생: {e}")
        return None


# 사용자 이미지 저장 함수 
def download_and_save_image_with_custom_name(
    user_id: int, 
    image_source: str, 
    is_bw: bool, 
    db: Session,
    save_dir: str = Config.STATIC_DIR
) -> Optional[str]:
    
    try:
        os.makedirs(save_dir, exist_ok=True)
        
        username = get_username_by_id(db, user_id)
        image_type = "wb" if is_bw else "color"
        
        # 해당 유저가 만든 동일 타입 이미지 파일 개수 세기
        existing_files = [f for f in os.listdir(save_dir) if f.startswith(f"{username}_{image_type}_")]
        next_index = len(existing_files) + 1
        
        filename = f"{username}_{image_type}_{next_index}.png"
        
        # S3 사용 여부에 따라 분기
        if Config.USE_S3:
            try:
                # S3에 저장
                s3_path = save_image_s3(
                    image_source, 
                    bucket_name=Config.S3_BUCKET, 
                    object_name=filename
                )
                return s3_path
            except Exception as e:
                logging.warning(f"S3 저장 실패, 로컬 저장으로 전환: {e}")
                # S3 실패시 로컬로 폴백
        
        # 로컬에 저장
        file_path = os.path.join(save_dir, filename)
        return save_image_locally(image_source, file_path)
        
    except Exception as e:
        logging.error(f"이미지 저장 중 오류 발생: {e}")
        return None

# 병렬로 이미지 및 음성 생성 후 저장
def generate_and_save_images_parallel(
    user_id: int, 
    fairy_tale_text: str, 
    voice: str, 
    theme: str, 
    voice_content: str
) -> Optional[Story]:
    db: Session = SessionLocal()
    try:
        # ThreadPoolExecutor를 사용한 병렬 처리
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 비동기 작업 제출
            future_color_image = executor.submit(generate_image_from_fairy_tale, fairy_tale_text)
            future_voice = executor.submit(generate_openai_voice, voice_content, voice)
            
            # 결과 수집
            results = {}
            for future in as_completed([future_color_image, future_voice]):
                try:
                    if future == future_color_image:
                        results['color_image'] = future.result()
                    elif future == future_voice:
                        results['voice_file'] = future.result()
                except Exception as e:
                    logging.error(f"병렬 처리 중 오류: {e}")
            
            # 이미지 처리
            color_image_path = results.get('color_image')
            if not color_image_path:
                raise Exception("컬러 이미지 생성 실패")
            
            # 흑백 이미지 생성 (컬러 이미지 완료 후)
            bw_image_path = convert_bw_image(color_image_path)
            
            # 이미지 저장
            color_path = download_and_save_image_with_custom_name(user_id, color_image_path, False, db)
            bw_path = download_and_save_image_with_custom_name(user_id, bw_image_path, True, db) if bw_image_path else None
            
            # DB에 저장
            return save_story_to_db(
                user_id=user_id,
                theme=theme,
                voice=voice,
                content=fairy_tale_text,
                voice_content=voice_content,
                image=color_path,
                bw_image=bw_path
            )
            
    except Exception as e:
        logging.error(f"전체 동화 저장 과정 중 오류: {e}")
        raise e
    finally:
        db.close()


# 동화 저장 함수
def save_story_to_db(user_id: int, theme: str, voice: str, 
                     content: str, voice_content: str, image: str, bw_image: str):
    db: Session = SessionLocal()
    try:
        story = Story(
            user_id=user_id,
            theme=theme,
            voice=voice,
            content=content,
            voice_content=voice_content,
            image=image,
            bw_image=bw_image,
        )
        db.add(story)
        db.commit()
        db.refresh(story)
        return story
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
    

# 이미지 불러오는 함수
def get_user_images(db: Session, user_id: int):
    return (
        db.query(Story)
        .filter(Story.user_id == user_id)
        .order_by(Story.created_at.desc())
        .all()
    )

def display_image_with_actions(story: Story, col_index: int, view_mode: str = "grid"):
    """이미지와 액션 버튼들을 표시하는 함수"""
    sharing_utils = ImageSharingUtils()
    
    if view_mode == "grid":
        # 그리드 모드: 이미지들을 세로로 배치
        if story.image:
            st.image(story.image, caption="컬러 이미지", use_container_width=True)
        if story.bw_image:
            st.image(story.bw_image, caption="흑백 이미지", use_container_width=True)
    else:
        # 목록 모드: 이미지들을 가로로 배치
        img_cols = st.columns(2) if story.bw_image else st.columns(1)
        
        with img_cols[0]:
            if story.image:
                st.image(story.image, caption="컬러 이미지", use_container_width=True)
        
        if story.bw_image and len(img_cols) > 1:
            with img_cols[1]:
                st.image(story.bw_image, caption="흑백 이미지", use_container_width=True)
    
    # 기본 정보 표시
    st.caption(f"**테마:** {story.theme}")
    st.caption(f"**생성일:** {story.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    # 액션 버튼들
    st.markdown("---")
    
    # 다운로드 섹션
    st.markdown("**📥 다운로드**")
    download_cols = st.columns(2)
    
    with download_cols[0]:
        if story.image:
            sharing_utils.create_download_button(
                story.image, 
                f"{story.theme}_컬러.png", 
                "🎨 컬러"
            )
    
    with download_cols[1]:
        if story.bw_image:
            sharing_utils.create_download_button(
                story.bw_image, 
                f"{story.theme}_흑백.png", 
                "⚫ 흑백"
            )
    
    # 공유 섹션
    st.markdown("**📤 공유하기**")
    
    # 이미지 URL 준비 (실제 환경에서는 공개 URL이 필요)
    image_url = story.image if story.image and story.image.startswith('http') else None
    
    if image_url:
        share_urls = sharing_utils.get_social_sharing_urls(image_url, story.theme)
        
        # 소셜 미디어 버튼들
        share_cols = st.columns(3)
        
        with share_cols[0]:
            if st.button("💬 카카오톡", key=f"kakao_{story.id}_{col_index}", use_container_width=True):
                st.markdown(f'<meta http-equiv="refresh" content="0; url={share_urls["kakao"]}">', 
                           unsafe_allow_html=True)
                st.success("카카오톡 공유 페이지로 이동합니다!")
        
        # with share_cols[1]:
        #     if st.button("📘 페이스북", key=f"facebook_{story.id}_{col_index}", use_container_width=True):
        #         st.markdown(f'<meta http-equiv="refresh" content="0; url={share_urls["facebook"]}">', 
        #                    unsafe_allow_html=True)
        #         st.success("페이스북 공유 페이지로 이동합니다!")
        
        # with share_cols[2]:
        #     if st.button("🐦 트위터", key=f"twitter_{story.id}_{col_index}", use_container_width=True):
        #         st.markdown(f'<meta http-equiv="refresh" content="0; url={share_urls["twitter"]}">', 
        #                    unsafe_allow_html=True)
        #         st.success("트위터 공유 페이지로 이동합니다!")
        
        # 추가 공유 옵션
        share_cols2 = st.columns(2)
        
        with share_cols2[0]:
            if st.button("📧 이메일", key=f"email_{story.id}_{col_index}", use_container_width=True):
                st.markdown(f'<a href="{share_urls["email"]}" target="_blank">이메일로 공유하기</a>', 
                           unsafe_allow_html=True)
        
        with share_cols2[1]:
            if st.button("🔗 링크복사", key=f"copy_{story.id}_{col_index}", use_container_width=True):
                # JavaScript를 사용한 클립보드 복사 (제한적으로 작동)
                st.code(image_url, language=None)
                st.success("링크가 표시되었습니다. 복사해서 사용하세요!")
    else:
        st.info("공유하려면 이미지가 웹에서 접근 가능한 URL이어야 합니다.")
    
    # 삭제 섹션
    st.markdown("---")
    delete_checked = st.checkbox(
        f"❌ 삭제 선택", 
        key=f"delete_check_{story.id}_{col_index}"
    )
    
    if delete_checked:
        if st.button(f"🗑️ 삭제 실행", key=f"delete_btn_{story.id}_{col_index}", type="secondary"):
            if delete_story_from_db(story.id):
                st.success("✅ 스토리가 삭제되었습니다.")
                st.rerun()
            else:
                st.error("삭제 실패. 다시 시도해주세요.")

# 갤러리 표시 함수
def display_gallery(stories: List[Story], current_page: int, per_page: int = 9):

    cols = st.columns(3)  # 3열 구성

    for i, story in enumerate(stories):
        with cols[i % 3]:
            with st.container():
                display_image_with_actions(story, i, "grid")

# 갤러리 목록 함수
def display_story_list(stories: List[Story], current_page: int, per_page: int = 5):
    for idx, story in enumerate(stories):
        with st.container():
            st.markdown("---")
            # col1, col2 = st.columns([1, 2])
            
            # with col1:
            #     # 이미지 표시
            #     if story.image:
            #         st.image(story.image, use_container_width=True)
            #     if story.bw_image:
            #         st.image(story.bw_image, caption="흑백 이미지", use_container_width=True)
            #     else:
            #         st.info("흑백 이미지 없음")
            
            # with col2:
            st.subheader(f"스토리 #{current_page * per_page + idx + 1}")
            display_image_with_actions(story, idx, "list")
            
            # 스토리 내용 표시
            if hasattr(story, 'content') and story.content:
                with st.expander("📖 스토리 내용 보기"):
                    st.write(story.content)

# 스토리 삭제 함수
def delete_story_from_db(story_id: int) -> bool:
    db: Session = SessionLocal()
    try:
        story = db.query(Story).filter(Story.id == story_id).first()
        if story:
            db.delete(story)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
