import logging
from .base import BasePlatform

logger = logging.getLogger(__name__)


class InstagramPlatform(BasePlatform):
    """
    Класс для работы с Instagram Reels
    """
    
    def get_platform_name(self) -> str:
        return "Instagram"
    
    def is_valid_url(self, url: str) -> bool:
        """
        Проверка, что URL это Instagram Reels
        """
        instagram_patterns = [
            'instagram.com/reel/',
            'instagram.com/p/',  # Обычные посты тоже можем обрабатывать
        ]
        return any(pattern in url for pattern in instagram_patterns)
    
    def get_video_info(self, url: str):
        """
        Получить информацию о Instagram Reels
        """
        logger.info(f"[Instagram] Обработка Reels: {url}")
        info = super().get_video_info(url)
        
        # Для Instagram используем описание вместо названия
        # Потому что title часто содержит имя автора, а не описание видео
        if info and info.get('description'):
            # Берём первую строку описания или полное описание если оно короткое
            description = info['description'].strip()
            if description:
                # Если описание длинное, берём первую строку
                first_line = description.split('\n')[0]
                info['title'] = first_line if len(first_line) <= 200 else first_line[:197] + '...'
                logger.info(f"[Instagram] Использую описание как название: {info['title']}")
        
        return info