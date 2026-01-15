import logging
from .base import BasePlatform

logger = logging.getLogger(__name__)


class YouTubePlatform(BasePlatform):
    """
    Класс для работы с YouTube Shorts
    """
    
    def __init__(self):
        super().__init__()
    
    def get_platform_name(self) -> str:
        return "YouTube"
    
    def is_valid_url(self, url: str) -> bool:
        """
        Проверка, что URL это YouTube Shorts
        """
        youtube_patterns = [
            'youtube.com/shorts/',
            'youtu.be/',
            'youtube.com/watch?v=',  # На случай если обычное видео
        ]
        return any(pattern in url for pattern in youtube_patterns)
    
    def get_video_info(self, url: str):
        """
        Получить информацию о YouTube видео
        """
        logger.info(f"[YouTube] Обработка Shorts: {url}")
        return super().get_video_info(url)
