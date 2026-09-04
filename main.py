# main.py
import logging

from telegram import Update
# ИЗМЕНЕНИЕ: Добавьте MessageHandler и Filters
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# ВАЖНО: Убедитесь, что все эти файлы находятся в той же папке
# ИЗМЕНЕНИЕ: Импортируйте handle_text_input
from telegram_handler import start, button_callback, handle_text_input
from database import init_db

# ======================================================================
# ВАШ ТОКЕН БОТА УЖЕ ВСТАВЛЕН НИЖЕ
BOT_TOKEN = "8116761325:AAELu8HGlsqckKv3t4PhrUvt8_b5T8Sk3Gk"
# ======================================================================

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING # Установлен уровень WARNING, чтобы не было спама в терминале
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)


async def universal_callback_handler(update: Update, context):
    """
    Универсальный обработчик, который просто перенаправляет все нажатия
    в основной обработчик в telegram_handler.
    """
    await button_callback(update, context)


def main():
    """
    Основная функция для запуска бота.
    """
    init_db()
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(universal_callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    print("Бот успешно запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()


if __name__ == '__main__':
    main()