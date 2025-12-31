import logging
from .base import BasePlatform

logger = logging.getLogger(__name__)


class TikTokPlatform(BasePlatform):
    """
    Класс для работы с TikTok
    """
    
    def get_platform_name(self) -> str:
        return "TikTok"
    
    def is_valid_url(self, url: str) -> bool:
        """
        Проверка, что URL это TikTok видео
        """
        tiktok_patterns = [
            'tiktok.com',
            'vm.tiktok.com',  # Короткие ссылки TikTok
        ]
        return any(pattern in url for pattern in tiktok_patterns)
    
    def get_video_info(self, url: str):
        """
        Получить информацию о TikTok видео
        """
        logger.info(f"[TikTok] Обработка видео: {url}")
        return super().get_video_info(url)
