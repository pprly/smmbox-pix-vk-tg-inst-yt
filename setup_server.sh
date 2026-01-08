#!/bin/bash

# Скрипт для первой настройки бота на сервере
# Запускать на сервере от имени пользователя (не root)

set -e  # Остановить при ошибке

echo "🚀 Настройка Telegram Shorts Bot"
echo "=================================="

# 1. Проверяем Python
echo ""
echo "1️⃣ Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установи его:"
    echo "   sudo apt update && sudo apt install python3 python3-pip python3-venv -y"
    exit 1
fi
echo "✅ Python найден: $(python3 --version)"

# 2. Создаём папку для бота
echo ""
echo "2️⃣ Создание директории..."
BOT_DIR="$HOME/tg_shorts_bot"
if [ -d "$BOT_DIR" ]; then
    echo "⚠️  Папка $BOT_DIR уже существует"
    read -p "Удалить и создать заново? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$BOT_DIR"
        echo "✅ Старая папка удалена"
    fi
fi

if [ ! -d "$BOT_DIR" ]; then
    mkdir -p "$BOT_DIR"
    echo "✅ Папка создана: $BOT_DIR"
fi

cd "$BOT_DIR"

# 3. Клонируем репозиторий
echo ""
echo "3️⃣ Клонирование репозитория..."
read -p "Введи URL твоего GitHub репозитория (например: https://github.com/username/repo.git): " REPO_URL

if [ -z "$(ls -A $BOT_DIR)" ]; then
    git clone "$REPO_URL" .
    echo "✅ Репозиторий склонирован"
else
    echo "⚠️  Папка не пустая, пропускаю клонирование"
fi

# 4. Создаём виртуальное окружение
echo ""
echo "4️⃣ Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Виртуальное окружение создано"
else
    echo "⚠️  Виртуальное окружение уже существует"
fi

# 5. Активируем venv и устанавливаем зависимости
echo ""
echo "5️⃣ Установка зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Зависимости установлены"

# 6. Настройка .env файла
echo ""
echo "6️⃣ Настройка .env файла..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Файл .env создан из .env.example"
    echo ""
    echo "⚠️  ВАЖНО: Отредактируй файл .env и добавь свои токены:"
    echo "   nano .env"
    echo ""
    read -p "Нажми Enter когда отредактируешь .env..."
else
    echo "⚠️  Файл .env уже существует"
fi

# 7. Настройка systemd сервиса
echo ""
echo "7️⃣ Настройка systemd сервиса..."

# Создаём service файл с правильными путями
SERVICE_FILE="/tmp/tg-shorts-bot.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Telegram Shorts Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin"
ExecStart=$BOT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Копирую service файл в /etc/systemd/system/..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/tg-shorts-bot.service
sudo systemctl daemon-reload
echo "✅ Systemd сервис настроен"

# 8. Запуск бота
echo ""
echo "8️⃣ Запуск бота..."
sudo systemctl enable tg-shorts-bot
sudo systemctl start tg-shorts-bot
echo "✅ Бот запущен"

# 9. Проверка статуса
echo ""
echo "9️⃣ Проверка статуса..."
sudo systemctl status tg-shorts-bot --no-pager

echo ""
echo "=================================="
echo "✅ Настройка завершена!"
echo ""
echo "📝 Полезные команды:"
echo "   sudo systemctl status tg-shorts-bot   # Статус бота"
echo "   sudo systemctl restart tg-shorts-bot  # Перезапуск"
echo "   sudo systemctl stop tg-shorts-bot     # Остановка"
echo "   sudo journalctl -u tg-shorts-bot -f   # Логи в реальном времени"
echo ""
echo "🔄 Автообновление через GitHub Actions настроено!"
echo "   При пуше в main ветку бот автоматически обновится"
