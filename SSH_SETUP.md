# Настройка SSH для GitHub Actions

## На сервере:

# 1. Создай SSH ключ для GitHub Actions
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions -N ""

# 2. Добавь публичный ключ в authorized_keys
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# 3. Выведи приватный ключ (скопируй его полностью)
cat ~/.ssh/github_actions

# 4. Узнай свой порт SSH (обычно 22)
echo $SSH_CLIENT | awk '{print $3}'

## В GitHub:

1. Открой свой репозиторий на GitHub
2. Settings → Secrets and variables → Actions
3. Нажми "New repository secret"
4. Добавь следующие секреты:

   SERVER_HOST
   └─ IP адрес твоего сервера (например: 192.168.1.100)
   
   SERVER_USER
   └─ Имя пользователя на сервере (например: erik)
   
   SERVER_PORT
   └─ SSH порт (обычно: 22)
   
   SSH_PRIVATE_KEY
   └─ Полный текст приватного ключа из шага 3
      (должен начинаться с -----BEGIN OPENSSH PRIVATE KEY-----)

## Проверка:

# На сервере дай права пользователю на sudo systemctl без пароля
sudo visudo

# Добавь в конец файла (замени USERNAME на своё имя):
USERNAME ALL=(ALL) NOPASSWD: /bin/systemctl restart tg-shorts-bot
USERNAME ALL=(ALL) NOPASSWD: /bin/systemctl status tg-shorts-bot
USERNAME ALL=(ALL) NOPASSWD: /bin/systemctl stop tg-shorts-bot
USERNAME ALL=(ALL) NOPASSWD: /bin/systemctl start tg-shorts-bot
