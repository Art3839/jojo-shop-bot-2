# Конфигурационный файл JoJo Shop Bot

# ОБЯЗАТЕЛЬНО ЗАПОЛНИТЕ ЭТИ ПОЛЯ:
TELEGRAM_TOKEN = 'ВАШ_ТОКЕН_ЗДЕСЬ'  # Получите у @BotFather
ADMIN_USER_IDS = [123456789, 987654321]  # Список ID админов в Telegram

# Chat ID для уведомлений (обычно совпадает с первым админом)
ADMIN_CHAT_ID = ADMIN_USER_IDS[0]

# Платежи ЮKassa (опционально)
YOOKASSA_SHOP_ID = ''      # Оставьте пустым если не используете
YOOKASSA_SECRET_KEY = ''   # Оставьте пустым если не используете

# Пути к файлам
DATABASE_PATH = 'data/products.db'
IMAGES_PATH = 'data/images/'

# Другие настройки
BOT_NAME = "JoJo Shop"

# Функция для проверки, является ли пользователь админом
def is_admin(user_id):
    return user_id in ADMIN_USER_IDS
