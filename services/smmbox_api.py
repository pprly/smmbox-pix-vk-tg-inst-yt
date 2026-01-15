import requests
import logging
import time
from datetime import datetime
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

    def post_video_clip_to_wall(
        self,
        video_url: str,
        title: str,
        scheduled_timestamp: int,
        preview_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Запостить видео с текстом на стену ПО РАСПИСАНИЮ
        
        Args:
            video_url: Прямая ссылка на видео-файл
            title: Название видео и текст поста
            scheduled_timestamp: Unix timestamp когда опубликовать
            preview_url: Ссылка на обложку (опционально)
        """
        # Получаем данные VK группы
        vk_group = self.get_vk_group()
        if not vk_group:
            logger.error("Не удалось получить данные VK группы")
            return None

        # Формируем текстовое вложение
        text_attach = {
            'type': 'text',
            'text': title
        }

        # Формируем вложение с видео (БЕЗ опции reels - обычное видео)
        video_attach = {
            'type': 'video',
            'url': video_url,
            'title': title
        }
        
        # Добавляем превью если есть
        if preview_url:
            video_attach['preview'] = preview_url
            video_attach['custom_preview'] = True

        # Формируем пост с текстом И видео (БЕЗ опции reels)
        post_data = {
            'posts': [
                {
                    'group': {
                        'id': vk_group['id'],
                        'social': vk_group['social'],
                        'type': vk_group['type']
                    },
                    'date': scheduled_timestamp,
                    'attachments': [text_attach, video_attach]
                    # БЕЗ options: ['reels'] - публикуем как обычное видео
                }
            ]
        }

        try:
            logger.info(f"Отправка поста (текст + видео) на стену: {vk_group['name']}")
            logger.info(f"Запланировано на: {datetime.fromtimestamp(scheduled_timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            
            response = requests.post(
                f'{self.api_url}/posts/postpone',
                headers=self.headers,
                json=post_data,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                logger.info("Пост с видео успешно добавлен в отложенные")
                return data.get('response')
            else:
                error = data.get('error', {})
                logger.error(f"Ошибка публикации поста с видео: {error.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при публикации поста с видео: {e}")
            return None
    
    def post_video_as_clip(
        self,
        video_url: str,
        title: str,
        preview_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Запостить видео как клип в VK группу СРАЗУ (не отложенно)
        
        Args:
            video_url: Прямая ссылка на видео-файл
            title: Название клипа
            preview_url: Ссылка на обложку (опционально)
            
        Returns:
            Dict с информацией о созданном клипе (включая его ID для прикрепления к посту)
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

        # Формируем пост с минимальной задержкой (текущее время + 10 секунд)
        # VK требует параметр date, даже для быстрой публикации
        current_timestamp = int(time.time()) + 10
        
        post_data = {
            'posts': [
                {
                    'group': {
                        'id': vk_group['id'],
                        'social': vk_group['social'],
                        'type': vk_group['type']
                    },
                    'date': current_timestamp,  # Текущее время + 10 секунд
                    'attachments': [video_attach],
                    'options': ['reels']  # Важно! Публикуем как клип
                }
            ]
        }

        try:
            logger.info(f"Отправка клипа в VK группу (сразу): {vk_group['name']}")
            
            response = requests.post(
                f'{self.api_url}/posts/postpone',
                headers=self.headers,
                json=post_data,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                logger.info("Клип успешно опубликован")
                return data.get('response')
            else:
                error = data.get('error', {})
                logger.error(f"Ошибка публикации клипа: {error.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при публикации клипа: {e}")
            return None
    
    def post_clip_to_wall(
        self,
        text: str,
        clip_response: Dict,
        scheduled_timestamp: int,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """
        Запостить пост на стену с прикрепленным клипом
        
        Args:
            text: Текст поста
            clip_response: Ответ от post_video_as_clip (содержит информацию о клипе)
            scheduled_timestamp: Unix timestamp когда опубликовать
            max_retries: Максимум попыток при ошибках
        """
        # Получаем данные VK группы
        vk_group = self.get_vk_group()
        if not vk_group:
            logger.error("Не удалось получить данные VK группы")
            return None

        # Извлекаем ID клипа из ответа
        # Структура ответа: {'posts': [...], 'links': [...]}
        try:
            if not clip_response or 'posts' not in clip_response:
                logger.error("Некорректный ответ от API при создании клипа")
                return None
            
            # Берём первый пост из ответа
            clip_post = clip_response['posts'][0] if clip_response['posts'] else None
            if not clip_post:
                logger.error("Не найден пост клипа в ответе API")
                return None
            
            # Ищем video вложение и извлекаем его VK ID
            video_attachment = None
            video_id = None
            for attach in clip_post.get('attachments', []):
                if attach.get('type') == 'video':
                    # Получаем ID видео из VK (если оно уже загружено)
                    video_id = attach.get('id')
                    if video_id:
                        # Создаём вложение типа AttachSocialVideo (только ID, без файла)
                        video_attachment = {
                            'type': 'video',
                            'id': video_id,
                            'social': 'vk'
                        }
                        logger.info(f"Найден VK video ID для прикрепления: {video_id}")
                    break
            
            if not video_attachment:
                logger.warning("Не найден VK ID видео в ответе, публикую только текст")
                # Публикуем просто текст без клипа
                return self.post_text_to_wall(text, scheduled_timestamp, max_retries)
            
            logger.info(f"Создаю пост на стену с прикреплённым VK видео")
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных клипа: {e}")
            # Публикуем просто текст без клипа
            return self.post_text_to_wall(text, scheduled_timestamp, max_retries)

        # Формируем текстовое вложение
        text_attach = {
            'type': 'text',
            'text': text
        }

        # Формируем пост с текстом И клипом
        post_data = {
            'posts': [
                {
                    'group': {
                        'id': vk_group['id'],
                        'social': vk_group['social'],
                        'type': vk_group['type']
                    },
                    'date': scheduled_timestamp,
                    'attachments': [
                        text_attach,
                        video_attachment  # Прикрепляем клип
                    ]
                }
            ]
        }

        # Пробуем с retry
        for attempt in range(max_retries):
            try:
                logger.info(f"Отправка поста (текст + клип) на стену: {vk_group['name']} (попытка {attempt + 1}/{max_retries})")
                response = requests.post(
                    f'{self.api_url}/posts/postpone',
                    headers=self.headers,
                    json=post_data,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('success'):
                    logger.info("Пост с клипом успешно добавлен в отложенные")
                    return data.get('response')
                else:
                    error = data.get('error', {})
                    logger.error(f"Ошибка публикации поста с клипом: {error.get('message')}")
                    
                    # Если ошибка "на это время уже есть пост" - не ретраим
                    if 'время запланирован' in error.get('message', '').lower():
                        return None
                    
                    # Для других ошибок - ждём и пробуем еще раз
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при публикации поста с клипом (попытка {attempt + 1}): {e}")
                
                # Если это последняя попытка - возвращаем None
                if attempt == max_retries - 1:
                    return None
                
                # Иначе ждём и пробуем снова
                time.sleep(2)
        
        return None
    
    def post_text_to_wall(
        self,
        text: str,
        scheduled_timestamp: int,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """
        Запостить текст на стену сообщества
        
        Args:
            text: Текст поста
            scheduled_timestamp: Unix timestamp когда опубликовать
            max_retries: Максимум попыток при ошибках (по умолчанию 3)
        """
        import time
        
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

        # Пробуем с retry
        for attempt in range(max_retries):
            try:
                logger.info(f"Отправка текстового поста на стену: {vk_group['name']} (попытка {attempt + 1}/{max_retries})")
                response = requests.post(
                    f'{self.api_url}/posts/postpone',
                    headers=self.headers,
                    json=post_data,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('success'):
                    logger.info("Текст успешно опубликован на стену")
                    return data.get('response')
                else:
                    error = data.get('error', {})
                    logger.error(f"Ошибка публикации текста: {error.get('message')}")
                    
                    # Если ошибка "на это время уже есть пост" - не ретраим
                    if 'время запланирован' in error.get('message', '').lower():
                        return None
                    
                    # Для других ошибок - ждём и пробуем еще раз
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при публикации текста (попытка {attempt + 1}): {e}")
                
                # Если это последняя попытка - возвращаем None
                if attempt == max_retries - 1:
                    return None
                
                # Иначе ждём и пробуем снова
                time.sleep(2)
        
        return None
