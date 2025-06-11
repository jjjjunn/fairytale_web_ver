import os
import requests
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI

load_dotenv()  # .env 파일에서 환경변수 로드

# GOOGLE API 키 가져오기
google_api_key = os.getenv('GOOGLE_API_KEY')

## 1. 변수에 값 할당하기
# google_api_key = st.secrets["GOOGLE"]["GOOGLE_API_KEY"]

## 2. 값이 없으면 에러 처리
# if not google_api_key:
#     raise ValueError("환경변수 'GOOGLE_API_KEY'가 설정되지 않았습니다.")



# 테마 목록과 키워드 매칭
THEME_KEYWORDS = {
    "잔잔한 피아노": "piano",
    "기타 멜로디": "guitar",
    "자연의 소리": "nature",
    "달빛": "moon",
    "하늘": "sky",
    "클래식": "classical",
}

def search_videos(theme):
    keyword = THEME_KEYWORDS.get(theme, "")
    if not keyword:
        return []

    query = f"{keyword} baby lullabby"
    url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&maxResults=5&type=video&q={query}&key={google_api_key}"
    )

    response = requests.get(url)

    # 응답코드가 200이 아닐 때 (응답 실패)
    if response.status_code != 200:
        print(f"YouTube API 요청 실패: {response.status_code}")
        return []
    
    data = response.json()
    results = []

    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        thumbnail = item["snippet"]["thumbnails"]["medium"]["url"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        results.append({
            "title": title,
            "url": video_url,
            "thumbnail": thumbnail
        })

    return results
        




