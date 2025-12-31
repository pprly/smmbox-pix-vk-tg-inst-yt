from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)


class Translator:
    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='ru')

    def translate_to_russian(self, text: str) -> str:
        """
        Перевести текст на русский язык
        """
        try:
            # Если текст уже на русском, вернём как есть
            if self._is_russian(text):
                logger.info("Текст уже на русском языке")
                return text
            
            logger.info(f"Перевод текста: {text[:50]}...")
            translated = self.translator.translate(text)
            logger.info(f"Переведено: {translated[:50]}...")
            return translated
            
        except Exception as e:
            logger.error(f"Ошибка перевода: {e}")
            return text  # Возвращаем оригинал если перевод не удался

    def _is_russian(self, text: str) -> bool:
        """
        Проверить, содержит ли текст русские буквы
        """
        russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        text_lower = text.lower()
        return any(char in russian_chars for char in text_lower)
