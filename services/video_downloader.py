import logging
import os
from typing import Optional, Dict, List
from .platforms import YouTubePlatform, TikTokPlatform, InstagramPlatform

logger = logging.getLogger(__name__)


class VideoDownloader:
    """
    Главный класс для работы с видео из разных платформ
    """
    
    def __init__(self, instagram_cookies: Optional[str] = None):
        """
        Args:
            instagram_cookies: Путь к файлу cookies для Instagram (опционально)
        """
        # Проверяем существует ли файл cookies для Instagram
        cookies_path = instagram_cookies or os.path.join(os.path.dirname(__file__), '..', 'instagram_cookies.txt')
        
        if os.path.exists(cookies_path):
            logger.info(f"Найден файл cookies для Instagram: {cookies_path}")
            instagram_platform = InstagramPlatform(cookies_file=cookies_path)
        else:
            logger.warning("Файл cookies для Instagram не найден, Instagram может не работать")
            instagram_platform = InstagramPlatform()
        
        # Инициализируем все платформы
        self.platforms = [
            YouTubePlatform(),
            TikTokPlatform(),
            instagram_platform
        ]
    
    def get_platform_for_url(self, url: str):
        """
        Определить платформу по URL
        """
        for platform in self.platforms:
            if platform.is_valid_url(url):
                return platform
        return None
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Получить информацию о видео (автоматически определяет платформу)
        """
        platform = self.get_platform_for_url(url)
        
        if not platform:
            logger.error(f"Неподдерживаемая платформа для URL: {url}")
            return None
        
        logger.info(f"Определена платформа: {platform.get_platform_name()}")
        return platform.get_video_info(url)
    
    def is_valid_url(self, url: str) -> bool:
        """
        Проверить, поддерживается ли URL
        """
        return self.get_platform_for_url(url) is not None
    
    def get_supported_platforms(self) -> List[str]:
        """
        Получить список поддерживаемых платформ
        """
        return [platform.get_platform_name() for platform in self.platforms]
