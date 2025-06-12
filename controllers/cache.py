import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import threading
import json
import hashlib
import pandas as pd

# 설정 클래스
class Config:
    OPENAI_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 16384
    IMAGE_SIZE = "1024x1024"
    STATIC_DIR = "static/images"
    CACHE_DIR = "cache"
    USE_S3 = os.getenv('USE_S3', 'false').lower() == 'true'
    S3_BUCKET = os.getenv('S3_BUCKET', 'my-fairytale-bucket')
    MAX_CACHE_SIZE = 100  # 캐시할 최대 파일 수

# 캐시 관리 클래스
class CacheManager:
    def __init__(self, cache_dir: str = Config.CACHE_DIR):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
        self._lock = threading.Lock()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """캐시 메타데이터 로드"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"캐시 메타데이터 로드 실패: {e}")
        return {}
    
    def _save_metadata(self):
        """캐시 메타데이터 저장"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"캐시 메타데이터 저장 실패: {e}")
    
    def _generate_cache_key(self, content: str, cache_type: str) -> str:
        """캐시 키 생성"""
        return hashlib.md5(f"{cache_type}_{content}".encode()).hexdigest()
    
    def get_cached_file(self, content: str, cache_type: str) -> Optional[str]:
        """캐시된 파일 경로 반환"""
        with self._lock:
            cache_key = self._generate_cache_key(content, cache_type)
            if cache_key in self.metadata:
                file_path = self.cache_dir / self.metadata[cache_key]['filename']
                if file_path.exists():
                    # 접근 시간 업데이트
                    self.metadata[cache_key]['last_accessed'] = pd.Timestamp.now().isoformat()
                    self._save_metadata()
                    return str(file_path)
                else:
                    # 파일이 없으면 메타데이터에서 제거
                    del self.metadata[cache_key]
                    self._save_metadata()
        return None
    
    def cache_file(self, content: str, cache_type: str, file_path: str) -> str:
        """파일을 캐시에 저장"""
        with self._lock:
            cache_key = self._generate_cache_key(content, cache_type)
            
            # 확장자 결정
            if cache_type == "image":
                ext = ".png"
            elif cache_type == "audio":
                ext = ".mp3"
            else:
                ext = ".bin"
            
            cached_filename = f"{cache_key}{ext}"
            cached_path = self.cache_dir / cached_filename
            
            try:
                # 파일 복사
                if os.path.exists(file_path):
                    import shutil
                    shutil.copy2(file_path, cached_path)
                    
                    # 메타데이터 업데이트
                    self.metadata[cache_key] = {
                        'filename': cached_filename,
                        'content_hash': cache_key,
                        'cache_type': cache_type,
                        'created_at': pd.Timestamp.now().isoformat(),
                        'last_accessed': pd.Timestamp.now().isoformat()
                    }
                    
                    # 캐시 크기 관리
                    self._manage_cache_size()
                    self._save_metadata()
                    
                    return str(cached_path)
            except Exception as e:
                logging.error(f"파일 캐싱 실패: {e}")
        
        return file_path  # 캐싱 실패시 원본 경로 반환
    
    def _manage_cache_size(self):
        """캐시 크기 관리 - LRU 방식으로 오래된 파일 삭제"""
        if len(self.metadata) <= Config.MAX_CACHE_SIZE:
            return
        
        # 마지막 접근 시간 기준으로 정렬
        sorted_items = sorted(
            self.metadata.items(),
            key=lambda x: x[1]['last_accessed']
        )
        
        # 오래된 파일들 삭제
        items_to_remove = sorted_items[:len(self.metadata) - Config.MAX_CACHE_SIZE]
        
        for cache_key, metadata in items_to_remove:
            try:
                file_path = self.cache_dir / metadata['filename']
                if file_path.exists():
                    file_path.unlink()
                del self.metadata[cache_key]
            except Exception as e:
                logging.error(f"캐시 파일 삭제 실패: {e}")
