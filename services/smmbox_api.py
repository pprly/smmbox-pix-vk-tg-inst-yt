import requests
import logging
from typing import Optional, Dict, List
from config import SMMBOX_API_TOKEN, SMMBOX_API_URL

logger = logging.getLogger(__name__)


class SMMBoxAPI:
    def __init__(self):
        self.api_url = SMMBOX_API_URL
        self.headers = {
            'Authorization': f'Bearer {SMMBOX_API_TOKEN}',
            'Content-Type': 'application/json'
        }

    def get_groups(self) -> Optional[List[Dict]]:
        """
        Получить список всех подключенных групп
        """
        try:
            response = requests.get(
                f'{self.api_url}/groups',
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                return data.get('response', [])
            else:
                logger.error(f"Ошибка получения групп: {data.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при запросе к SMMBox API: {e}")
            return None

    def get_vk_group(self) -> Optional[Dict]:
        """
        Получить первую VK группу из списка
        """
        groups = self.get_groups()
        if not groups:
            return None
        
        # Ищем VK группу
        for group in groups:
            if group.get('social') == 'vk':
                return {
                    'id': group['id'],
                    'social': group['social'],
                    'type': group['type'],
                    'name': group.get('name', 'Неизвестно')
                }
        
        logger.error("VK группа не найдена в списке подключенных групп")
        return None

    def post_video_as_clip(
        self,
        video_url: str,
        title: str,
        scheduled_timestamp: int,
        preview_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Запостить видео как клип в VK группу
        
        Args:
            video_url: Прямая ссылка на видео-файл
            title: Название клипа
            scheduled_timestamp: Unix timestamp когда опубликовать
            preview_url: Ссылка на обложку (опционально)
        """
        # Получаем данные VK группы
        vk_group = self.get_vk_group()
        if not vk_group:
            logger.error("Не удалось получить данные VK группы")
            return None

        # Формируем вложение с видео
        video_attach = {
            'type': 'video',
            'url': video_url,
            'title': title
        }
        
        # Добавляем превью если есть
        if preview_url:
            video_attach['preview'] = preview_url
            video_attach['custom_preview'] = True

        # Формируем пост
        post_data = {
            'posts': [
                {
                    'group': {
                        'id': vk_group['id'],
                        'social': vk_group['social'],
                        'type': vk_group['type']
                    },
                    'date': scheduled_timestamp,  # Используем точное время из планировщика
                    'attachments': [video_attach],
                    'options': ['reels']  # Важно! Публикуем как клип
                }
            ]
        }

        try:
            logger.info(f"Отправка поста в VK группу: {vk_group['name']}")
            response = requests.post(
                f'{self.api_url}/posts/postpone',
                headers=self.headers,
                json=post_data
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                logger.info("Видео успешно опубликовано как клип")
                return data.get('response')
            else:
                error = data.get('error', {})
                logger.error(f"Ошибка публикации: {error.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при публикации видео: {e}")
            return None
    
    def post_text_to_wall(
        self,
        text: str,
        scheduled_timestamp: int
    ) -> Optional[Dict]:
        """
        Запостить текст на стену сообщества
        
        Args:
            text: Текст поста
            scheduled_timestamp: Unix timestamp когда опубликовать
        """
        # Получаем данные VK группы
        vk_group = self.get_vk_group()
        if not vk_group:
            logger.error("Не удалось получить данные VK группы")
            return None

        # Формируем текстовое вложение
        text_attach = {
            'type': 'text',
            'text': text
        }

        # Формируем пост
        post_data = {
            'posts': [
                {
                    'group': {
                        'id': vk_group['id'],
                        'social': vk_group['social'],
                        'type': vk_group['type']
                    },
                    'date': scheduled_timestamp,
                    'attachments': [text_attach]
                }
            ]
        }

        try:
            logger.info(f"Отправка текстового поста на стену: {vk_group['name']}")
            response = requests.post(
                f'{self.api_url}/posts/postpone',
                headers=self.headers,
                json=post_data
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                logger.info("Текст успешно опубликован на стену")
                return data.get('response')
            else:
                error = data.get('error', {})
                logger.error(f"Ошибка публикации текста: {error.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при публикации текста: {e}")
            return None