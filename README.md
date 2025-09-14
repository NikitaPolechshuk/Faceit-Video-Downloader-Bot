# Faceit-Video-Downloader-Bot

Бот для скачивания видео повторов с Faceit.сom

Скидываете боту ссылку на повтор, а в ответ получите видео файл *.mp4

***

<details>
<summary> ⚠️ Чтобы бот мог работать с большими видео файлами необходим свой сервер Telegram API ⚠️ </summary>

```
# Подготовка системы
sudo apt update && sudo apt upgrade -y
sudo apt install git build-essential cmake zlib1g-dev libssl-dev libevent-dev

# Клонирование с рекурсивными подмодулями
git clone --recursive https://github.com/tdlib/telegram-bot-api.git
cd telegram-bot-api

# Сборка
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=.. ..
cmake --build . --target install

# Разрешения файрвола
sudo ufw allow 8081/tcp
```

### 🔧 Запуск сервера

Запуск вручную:
```
cd ~/telegram-bot-api/bin
./telegram-bot-api --api-id=YOUR_API_ID --api-hash=YOUR_API_HASH --http-port=8081 --local
```
Автозапуск через systemd:

Создайте файл службы /etc/systemd/system/telegram-bot-api.service
```
[Unit]
Description=Telegram Bot API Server
After=network.target

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/home/your_username/telegram-bot-api/bin
ExecStart=/home/your_username/telegram-bot-api/bin/telegram-bot-api \
    --api-id=YOUR_API_ID \
    --api-hash=YOUR_API_HASH \
    --http-port=8081 \
    --local
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Активируйте службу:

```
sudo systemctl daemon-reload
sudo systemctl start telegram-bot-api
sudo systemctl enable telegram-bot-api
```
</details>

***

## 🚀 Запуск Бота

Клонируйте репозиторий
```
git clone https://github.com/NikitaPolechshuk/Faceit-Video-Downloader-Bot.git
```

Разверните виртуальное окружение и установите зависимости:
```
cd Faceit-Video-Downloader-Bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Создайте файл .env
```
TELEGRAM_BOT_TOKEN="токен_вашего_бота"
API_SERVER="http://localhost:8081"
```

Запуск:
```
python3 faceitvideodownloader_bot.py
```

Для проверки работоспособности вашего сервера API:
```
python3 test_api_server.py
# и отправьте вашему боту сообщение /start
```