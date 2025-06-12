from fastapi import APIRouter, HTTPException, Response
from controllers.story_controller import generate_fairy_tale, generate_image_from_fairy_tale, generate_openai_voice, save_story_to_db, get_user_images
from controllers.music_controller import search_tracks_by_tag
from controllers.video_controller import search_videos
from scheme_files.stories_schemes import StoryRequest, TTSRequest, ImageRequest, MusicRequest, VideoRequest, SaveStoryRequest
from scheme_files.users_schemes import UserIdRequest
from datetime import datetime
import base64


# FastAPI 애플리케이션 생성
router = APIRouter()

# 헬스체크 엔드포인트
@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "fastapi",
        "timestamp": datetime.now().isoformat()
    }

# 동화 생성 라우터
@router.post("/generate/story")
def generate_story(req: StoryRequest):
    if not req.name or not req.theme:
        raise HTTPException(status_code=400, detail="이름과 테마는 필수 필드입니다.")
    result = generate_fairy_tale(req.name, req.theme)
    return {"story": result}

# 음성 파일 생성 라우터 (바이너리 반환)
@router.post("/generate/voice")
def generate_voice(req: TTSRequest):
    try:
        audio_data = generate_openai_voice(req.text, req.voice, req.speed)
        if audio_data is None:
            raise HTTPException(status_code=500, detail="음성 파일 생성 실패")
        
        # Base64로 인코딩하여 JSON으로 반환 (모바일 앱에서 쉽게 처리)
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "audio_base64": audio_base64,
            "voice": req.voice,
            "speed": req.speed,
            "format": "mp3"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"음성 생성 실패: {str(e)}")

# 음성 파일 직접 다운로드 (바이너리 반환)
@router.post("/generate/voice/binary")
def generate_voice_binary(req: TTSRequest):
    try:
        audio_data = generate_openai_voice(req.text, req.voice, req.speed)
        if audio_data is None:
            raise HTTPException(status_code=500, detail="음성 파일 생성 실패")
        
        # 바이너리 데이터 직접 반환
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=voice_{req.voice}.mp3"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"음성 생성 실패: {str(e)}")

# 이미지 생성 라우터
@router.post("/generate/image")
def generate_image(req: ImageRequest):
    image_url = generate_image_from_fairy_tale(req.text)
    return {"image_url": image_url}


# 이미지 저장 라우터
@router.post("/save/image")
def save_story(req: SaveStoryRequest):
    save_story_to_db(req)
    return {"status": "동화가 성공적으로 저장되었습니다."}

# 이미지 불러오는 라우터
@router.post("/gallery/images")
def get_bw_images(req: UserIdRequest):
    images = get_user_images(req.user_id)
    return {"images": images}

# 음악 검색 라우터
@router.post("/search/url")
def get_music(req: MusicRequest):
    results = search_tracks_by_tag(req.theme)
    return {"music_results": results}

# 영상 검색 라우터
@router.post("/search/video")
def get_video(req: VideoRequest):
    results = search_videos(req.theme)
    return {"video_results": results}