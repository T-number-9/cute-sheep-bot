import logging
import sqlite3
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
import sheep
from config import TOKEN


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

conn = sqlite3.connect('sheeps.db')
cursor = conn.cursor()


def first_message(user_id, user_name):
    # проверяем есть ли информация о пользователе в БД
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    # если информации нет, добавляем новую запись
    if result is None:
        cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (user_id, user_name, 1, 0, 0, 100, 'Подстричь', True, 180, 0, 1, True, 0, True))
        conn.commit()
        return True
    return False


async def start(update, context):
    # получаем уникальный id пользователя и отправляем на проверку
    user_id, first_name = update.message.from_user.id, update.message.from_user.first_name
    if first_message(user_id, first_name):
        # если пользователь новый присылаем сообщение с данными о питомце
        await sheep.my_sheep(update, context)
    else:
        await update.message.reply_text('🐑 Твоя любимая овечка уже ждет тебя по команде /sheep')


async def help(update, context):
    # получаем уникальный id пользователя и отправляем на проверку
    await update.message.reply_text('/sheep - 🐑 Твоя любимая овечка уже ждет тебя по команде \n'
                                    '/walk - 🏔 Гулять можно по команде \n'
                                    '/trade - 🔁 Обмен предметов на купюры')


def main():
    application = Application.builder().token(TOKEN).build()
    # text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, text_check)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sheep", sheep.my_sheep))
    application.add_handler(CommandHandler("walk", sheep.walk))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("trade", sheep.trade))
    application.add_handler(CommandHandler("market", sheep.market))
    application.add_handler(CommandHandler("bazar", sheep.bazar))
    application.add_handler(CallbackQueryHandler(sheep.button))
    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
