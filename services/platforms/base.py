import yt_dlp
import logging
from typing import Optional, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BasePlatform(ABC):
    """
    Базовый класс для всех платформ
    """
    
    def __init__(self, cookies_file: Optional[str] = None):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        # Добавляем cookies если указан файл
        if cookies_file:
            self.ydl_opts['cookiefile'] = cookies_file
            logger.info(f"Используем cookies из файла: {cookies_file}")
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Название платформы"""
        pass
    
    @abstractmethod
    def is_valid_url(self, url: str) -> bool:
        """Проверка, что URL принадлежит этой платформе"""
        pass
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Получить информацию о видео без скачивания
        
        Returns:
            Dict с полями:
            - title: название видео
            - url: прямая ссылка на видео
            - thumbnail: ссылка на обложку
            - duration: длительность в секундах
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                logger.info(f"[{self.get_platform_name()}] Получение информации о видео: {url}")
                info = ydl.extract_info(url, download=False)
                
                # Получаем прямую ссылку на видео
                video_url = self._extract_video_url(info)
                
                if not video_url:
                    logger.error(f"[{self.get_platform_name()}] Не удалось получить прямую ссылку на видео")
                    return None
                
                result = {
                    'title': info.get('title', 'Без названия'),
                    'url': video_url,
                    'thumbnail': info.get('thumbnail'),
                    'duration': info.get('duration', 0),
                    'description': info.get('description', ''),
                    'uploader': info.get('uploader', ''),
                    'platform': self.get_platform_name()
                }
                
                logger.info(f"[{self.get_platform_name()}] Информация получена: {result['title']}")
                return result
                
        except Exception as e:
            logger.error(f"[{self.get_platform_name()}] Ошибка получения информации: {e}")
            return None
    
    def _extract_video_url(self, info: Dict) -> Optional[str]:
        """
        Извлечь прямую ссылку на видео из информации
        """
        # Ищем формат с видео и аудио
        if 'formats' in info:
            video_url = None
            for fmt in info['formats']:
                if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                    video_url = fmt.get('url')
                    break
            
            # Если не нашли комбинированный формат, берём просто видео
            if not video_url and info['formats']:
                video_url = info['formats'][-1].get('url')
            
            return video_url
        
        return info.get('url')
