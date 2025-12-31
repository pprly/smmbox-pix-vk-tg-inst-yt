import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class PostScheduler:
    """
    Планировщик постов с ограничением по количеству в день
    """
    
    def __init__(self, db_path: str = "scheduler.db", posts_per_day: int = 7):
        self.db_path = db_path
        self.posts_per_day = posts_per_day
        self.init_db()
    
    def init_db(self):
        """
        Инициализация базы данных
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_url TEXT NOT NULL,
                video_title TEXT NOT NULL,
                platform TEXT NOT NULL,
                scheduled_date INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"База данных инициализирована: {self.db_path}")
    
    def get_next_available_slot(self) -> int:
        """
        Получить следующий доступный временной слот для публикации
        
        Returns:
            Unix timestamp следующего свободного слота
        """
        now = datetime.now()
        
        # Начинаем с сегодняшней даты в 00:00
        current_date = datetime(now.year, now.month, now.day)
        
        # Если сейчас меньше 23:00, можем постить сегодня
        # Иначе начинаем с завтрашнего дня
        if now.hour >= 23:
            current_date += timedelta(days=1)
        
        # Ищем первый день с свободными слотами
        while True:
            # Начало и конец дня
            day_start = int(current_date.timestamp())
            day_end = int((current_date + timedelta(days=1)).timestamp())
            
            # Считаем сколько постов уже запланировано на этот день
            posts_count = self.count_posts_for_day(day_start, day_end)
            
            if posts_count < self.posts_per_day:
                # Есть свободные слоты в этот день
                # Проверяем каждый слот пока не найдём свободный
                for slot_number in range(self.posts_per_day):
                    slot_time = self._calculate_slot_time(current_date, slot_number)
                    slot_timestamp = int(slot_time.timestamp())
                    
                    # Проверяем, не занят ли этот конкретный timestamp
                    if not self._is_slot_taken(slot_timestamp):
                        # Если слот в прошлом, берём текущее время + 5 минут
                        now_timestamp = int(now.timestamp())
                        
                        if slot_timestamp < now_timestamp:
                            slot_timestamp = now_timestamp + 300  # +5 минут от текущего времени
                        
                        return slot_timestamp
            
            # Переходим к следующему дню
            current_date += timedelta(days=1)
    
    def _is_slot_taken(self, timestamp: int) -> bool:
        """
        Проверить, занят ли конкретный временной слот
        
        Args:
            timestamp: Unix timestamp для проверки
            
        Returns:
            True если слот занят, False если свободен
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем есть ли посты на это точное время
        cursor.execute('''
            SELECT COUNT(*) FROM scheduled_posts 
            WHERE scheduled_date = ?
            AND status = 'pending'
        ''', (timestamp,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def _calculate_slot_time(self, date: datetime, slot_number: int) -> datetime:
        """
        Рассчитать время для слота в конкретный день
        
        Args:
            date: Дата (год, месяц, день)
            slot_number: Номер слота (0-6 для 7 постов в день)
        """
        import random
        
        # Фиксированные минуты для каждого слота (избегаем :00 и :30)
        # Это гарантирует что один и тот же слот всегда даст одно и то же время
        slot_minutes = [17, 42, 13, 51, 24, 38, 56]  # Разные минуты для каждого слота
        
        # Распределяем посты с 8:00 до 22:00 (14 часов)
        # Минимальный интервал: 2 часа между постами
        start_hour = 8
        base_interval_hours = 2.0  # 2 часа минимум
        
        # Добавляем случайное смещение от 0 до +30 минут (в часах)
        # ВАЖНО: используем slot_number как seed для random, чтобы один слот всегда давал одно смещение
        random.seed(f"{date.year}{date.month}{date.day}{slot_number}")
        random_offset = random.uniform(0, 0.5)  # 0-30 минут дополнительно
        random.seed()  # Сбрасываем seed
        
        post_hour = start_hour + (slot_number * base_interval_hours) + random_offset
        
        # Ограничиваем диапазон 8:00 - 22:00
        post_hour = max(8.0, min(21.9, post_hour))
        
        hour = int(post_hour)
        minute = slot_minutes[slot_number % len(slot_minutes)]
        
        return datetime(date.year, date.month, date.day, hour, minute)
    
    def count_posts_for_day(self, day_start: int, day_end: int) -> int:
        """
        Подсчитать количество постов запланированных на определённый день
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM scheduled_posts 
            WHERE scheduled_date >= ? AND scheduled_date < ?
            AND status = 'pending'
        ''', (day_start, day_end))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def add_post(self, video_url: str, video_title: str, platform: str) -> Dict:
        """
        Добавить пост в расписание
        
        Returns:
            Dict с информацией о запланированном посте
        """
        # Получаем следующий свободный слот
        scheduled_timestamp = self.get_next_available_slot()
        scheduled_datetime = datetime.fromtimestamp(scheduled_timestamp)
        
        # Сохраняем в базу
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scheduled_posts (video_url, video_title, platform, scheduled_date, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (video_url, video_title, platform, scheduled_timestamp, int(datetime.now().timestamp())))
        
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Пост добавлен в расписание: ID={post_id}, дата={scheduled_datetime}")
        
        return {
            'id': post_id,
            'scheduled_timestamp': scheduled_timestamp,
            'scheduled_datetime': scheduled_datetime,
            'video_title': video_title,
            'platform': platform
        }
    
    def get_stats(self) -> Dict:
        """
        Получить статистику по запланированным постам
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Всего постов в очереди
        cursor.execute('SELECT COUNT(*) FROM scheduled_posts WHERE status = "pending"')
        total_pending = cursor.fetchone()[0]
        
        # Посты на сегодня
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        today_end = today_start + timedelta(days=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM scheduled_posts 
            WHERE scheduled_date >= ? AND scheduled_date < ?
            AND status = 'pending'
        ''', (int(today_start.timestamp()), int(today_end.timestamp())))
        today_count = cursor.fetchone()[0]
        
        # Посты на завтра
        tomorrow_start = today_end
        tomorrow_end = tomorrow_start + timedelta(days=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM scheduled_posts 
            WHERE scheduled_date >= ? AND scheduled_date < ?
            AND status = 'pending'
        ''', (int(tomorrow_start.timestamp()), int(tomorrow_end.timestamp())))
        tomorrow_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_pending': total_pending,
            'today': today_count,
            'tomorrow': tomorrow_count,
            'posts_per_day_limit': self.posts_per_day
        }
    
    def mark_as_posted(self, post_id: int):
        """
        Отметить пост как опубликованный
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE scheduled_posts 
            SET status = 'posted' 
            WHERE id = ?
        ''', (post_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Пост ID={post_id} отмечен как опубликованный")