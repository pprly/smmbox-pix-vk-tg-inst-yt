from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from config import POSTS_PER_DAY
from services.video_downloader import VideoDownloader
from services.translator import Translator
from services.smmbox_api import SMMBoxAPI
from services.scheduler import PostScheduler
from utils.keyboards import get_title_confirmation_keyboard, get_cancel_keyboard

logger = logging.getLogger(__name__)
router = Router()

# Инициализация сервисов
video_downloader = VideoDownloader()
translator = Translator()
smmbox_api = SMMBoxAPI()
scheduler = PostScheduler(posts_per_day=POSTS_PER_DAY)


class VideoUploadStates(StatesGroup):
    waiting_for_url = State()
    waiting_for_title_confirmation = State()
    waiting_for_custom_title = State()
    uploading = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start
    """
    await state.clear()
    await message.answer(
        "👋 Привет! Я бот для загрузки Shorts/Reels в VK как клипов.\n\n"
        "Отправь мне ссылку на:\n"
        "• YouTube Shorts\n"
        "• TikTok видео\n"
        "• Instagram Reels\n\n"
        "Я переведу название и загружу видео в твою VK группу!\n\n"
        "📊 Команды:\n"
        "/stats - статистика очереди постов\n"
        "/cancel - отменить текущую операцию"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """
    Показать статистику очереди постов
    """
    stats = scheduler.get_stats()
    
    await message.answer(
        f"📊 <b>Статистика очереди постов</b>\n\n"
        f"📅 Сегодня: {stats['today']}/{stats['posts_per_day_limit']}\n"
        f"📅 Завтра: {stats['tomorrow']}/{stats['posts_per_day_limit']}\n"
        f"📦 Всего в очереди: {stats['total_pending']}\n\n"
        f"⚙️ Лимит: {stats['posts_per_day_limit']} постов в день",
        parse_mode="HTML"
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """
    Отмена текущей операции
    """
    await state.clear()
    await message.answer("❌ Операция отменена. Отправь новую ссылку для загрузки.")


@router.message(StateFilter(None))
async def handle_video_url(message: Message, state: FSMContext):
    """
    Обработка ссылки на видео
    """
    url = message.text.strip()
    
    # Проверяем, что это ссылка
    if not url.startswith('http'):
        await message.answer(
            "❌ Пожалуйста, отправь ссылку на видео.\n\n"
            "Поддерживаются: YouTube Shorts, TikTok, Instagram Reels"
        )
        return
    
    # Проверяем, поддерживается ли платформа
    if not video_downloader.is_valid_url(url):
        await message.answer(
            "❌ Неподдерживаемая платформа.\n\n"
            "Поддерживаются: YouTube Shorts, TikTok, Instagram Reels"
        )
        return
    
    # Отправляем сообщение о загрузке
    processing_msg = await message.answer("⏳ Получаю информацию о видео...")
    
    # Получаем информацию о видео
    video_info = video_downloader.get_video_info(url)
    
    if not video_info:
        await processing_msg.edit_text(
            "❌ Не удалось получить информацию о видео.\n"
            "Проверь ссылку и попробуй снова."
        )
        return
    
    # Переводим название
    original_title = video_info['title']
    await processing_msg.edit_text(f"📝 Оригинальное название: {original_title}\n\n⏳ Перевожу...")
    
    translated_title = translator.translate_to_russian(original_title)
    
    # Сохраняем данные в состояние
    await state.update_data(
        video_url=url,
        video_info=video_info,
        original_title=original_title,
        translated_title=translated_title
    )
    
    # Спрашиваем подтверждение названия
    await processing_msg.edit_text(
        f"🎬 <b>Платформа:</b> {video_info.get('platform', 'Неизвестно')}\n\n"
        f"📝 Оригинальное название:\n<b>{original_title}</b>\n\n"
        f"🇷🇺 Переведённое название:\n<b>{translated_title}</b>\n\n"
        f"Название правильное?",
        reply_markup=get_title_confirmation_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(VideoUploadStates.waiting_for_title_confirmation)


@router.callback_query(F.data == "title_confirm", VideoUploadStates.waiting_for_title_confirmation)
async def confirm_title(callback: CallbackQuery, state: FSMContext):
    """
    Подтверждение названия и загрузка видео
    """
    await callback.answer()
    await callback.message.edit_text("📅 Планирую публикацию...")
    
    # Получаем данные из состояния
    data = await state.get_data()
    video_info = data['video_info']
    title = data['translated_title']
    
    # Добавляем в планировщик
    schedule_info = scheduler.add_post(
        video_url=video_info['url'],
        video_title=title,
        platform=video_info.get('platform', 'Unknown')
    )
    
    # Публикуем видео с текстом на стену (VK конвертирует в клип)
    # Пробуем до 3 раз если время занято
    result = None
    for attempt in range(3):
        result = smmbox_api.post_video_clip_to_wall(
            video_url=video_info['url'],
            title=title,
            scheduled_timestamp=schedule_info['scheduled_timestamp'],
            preview_url=video_info.get('thumbnail')
        )
        
        if result:
            break  # Успех!
        
        # Если не успех, помечаем слот как занятый и пробуем следующий
        scheduler.mark_as_failed(schedule_info['id'])
        logger.info(f"Попытка {attempt + 1}/3: время занято, пробую следующий слот...")
        
        # Получаем новый слот
        schedule_info = scheduler.add_post(
            video_url=video_info['url'],
            video_title=title,
            platform=video_info.get('platform', 'Unknown')
        )
    
    # Получаем статистику
    stats = scheduler.get_stats()
    scheduled_dt = schedule_info['scheduled_datetime']
    
    if result:
        # Отмечаем как опубликованное
        scheduler.mark_as_posted(schedule_info['id'])
        
        await callback.message.edit_text(
            f"✅ Видео добавлено в отложенные!\n\n"
            f"📝 Название: <b>{title}</b>\n"
            f"🎬 Платформа: {video_info.get('platform', 'Unknown')}\n"
            f"📅 Запланировано на: <b>{scheduled_dt.strftime('%d.%m.%Y в %H:%M')}</b>\n"
            f"📌 Запись с клипом на стене\n\n"
            f"📊 Статистика очереди:\n"
            f"• Сегодня: {stats['today']}/{stats['posts_per_day_limit']}\n"
            f"• Завтра: {stats['tomorrow']}/{stats['posts_per_day_limit']}\n"
            f"• Всего в очереди: {stats['total_pending']}",
            parse_mode="HTML"
        )
    else:
        # Помечаем последний слот как занятый
        scheduler.mark_as_failed(schedule_info['id'])
        
        await callback.message.edit_text(
            "❌ Все слоты на сегодня заняты.\n"
            "Попробуй позже или очисти отложенные посты в SMMBox."
        )
    
    await state.clear()


@router.callback_query(F.data == "title_edit", VideoUploadStates.waiting_for_title_confirmation)
async def edit_title(callback: CallbackQuery, state: FSMContext):
    """
    Запрос на ввод нового названия
    """
    await callback.answer()
    await callback.message.edit_text(
        "✍️ Введи новое название для видео:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(VideoUploadStates.waiting_for_custom_title)


@router.message(VideoUploadStates.waiting_for_custom_title)
async def process_custom_title(message: Message, state: FSMContext):
    """
    Обработка пользовательского названия
    """
    custom_title = message.text.strip()
    
    if not custom_title:
        await message.answer("❌ Название не может быть пустым. Попробуй ещё раз:")
        return
    
    # Обновляем название
    await state.update_data(translated_title=custom_title)
    
    # Загружаем видео
    processing_msg = await message.answer("📅 Планирую публикацию...")
    
    data = await state.get_data()
    video_info = data['video_info']
    
    # Добавляем в планировщик
    schedule_info = scheduler.add_post(
        video_url=video_info['url'],
        video_title=custom_title,
        platform=video_info.get('platform', 'Unknown')
    )
    
    # Публикуем видео с текстом на стену (VK конвертирует в клип)
    # Пробуем до 3 раз если время занято
    result = None
    for attempt in range(3):
        result = smmbox_api.post_video_clip_to_wall(
            video_url=video_info['url'],
            title=custom_title,
            scheduled_timestamp=schedule_info['scheduled_timestamp'],
            preview_url=video_info.get('thumbnail')
        )
        
        if result:
            break  # Успех!
        
        # Если не успех, помечаем слот как занятый и пробуем следующий
        scheduler.mark_as_failed(schedule_info['id'])
        logger.info(f"Попытка {attempt + 1}/3: время занято, пробую следующий слот...")
        
        # Получаем новый слот
        schedule_info = scheduler.add_post(
            video_url=video_info['url'],
            video_title=custom_title,
            platform=video_info.get('platform', 'Unknown')
        )
    
    # Получаем статистику
    stats = scheduler.get_stats()
    scheduled_dt = schedule_info['scheduled_datetime']
    
    if result:
        # Отмечаем как опубликованное
        scheduler.mark_as_posted(schedule_info['id'])
        
        await processing_msg.edit_text(
            f"✅ Видео добавлено в отложенные!\n\n"
            f"📝 Название: <b>{custom_title}</b>\n"
            f"🎬 Платформа: {video_info.get('platform', 'Unknown')}\n"
            f"📅 Запланировано на: <b>{scheduled_dt.strftime('%d.%m.%Y в %H:%M')}</b>\n"
            f"📌 Запись с клипом на стене\n\n"
            f"📊 Статистика очереди:\n"
            f"• Сегодня: {stats['today']}/{stats['posts_per_day_limit']}\n"
            f"• Завтра: {stats['tomorrow']}/{stats['posts_per_day_limit']}\n"
            f"• Всего в очереди: {stats['total_pending']}",
            parse_mode="HTML"
        )
    else:
        # Помечаем последний слот как занятый
        scheduler.mark_as_failed(schedule_info['id'])
        
        await processing_msg.edit_text(
            "❌ Все слоты на сегодня заняты.\n"
            "Попробуй позже или очисти отложенные посты в SMMBox."
        )
    
    await state.clear()


@router.callback_query(F.data == "cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """
    Отмена операции через кнопку
    """
    await state.clear()
    await callback.answer("Операция отменена")
    await callback.message.edit_text("❌ Операция отменена. Отправь новую ссылку для загрузки.")
