import sqlite3
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from aiogram import Bot
from config import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import time, datetime, timedelta

bot = Bot(token=TOKEN, parse_mode='HTML')
conn = sqlite3.connect('sheeps.db')  # создаем подключение к БД
cursor = conn.cursor()


def db_check(user_id):  # получаем данные из БД
    return cursor.execute('SELECT level, money, diamonds, food, cut, walk, user_name, timer, end_timer, power,'
                          ' cut_uncut'
                          ' FROM users WHERE user_id = ?', (user_id,)).fetchall()[0]


def db_check_bag(user_id):  # получаем данные из БД
    return cursor.execute('SELECT wool FROM items WHERE user_id = ?', (user_id,)).fetchall()[0]


def delta_time(update):  # функция для подсчета оставшегося времени
    query = update.callback_query
    end = db_check(query.message.chat_id)[8]  # получаем время окончания
    delta_t = datetime(year=int(end[:4]), month=int(end[5:7]), day=int(end[8:10]), hour=int(end[11:13]),
                       minute=int(end[14:16]), second=int(end[17:19])) - datetime.now()  # считаем остаток времени

    if str(delta_t)[0] == '-':  # если время ожидания истекло возвращаем кнопке первоначальное значение
        cursor.execute(f'UPDATE users SET cut = "Подстричь", cut_uncut = True, end_timer = 0 WHERE user_id = ?',
                       (query.message.chat_id,))
        conn.commit()
        return True
    else:  # иначе вводим корректное время
        cursor.execute(f'UPDATE users SET cut = ? WHERE user_id = ?', (str(delta_t), query.message.chat_id,))
        conn.commit()
        return False


def delta_time_for_sheep(update):  # функция для подсчета оставшегося времени
    end = db_check(update.message.chat_id)[8]
    delta_t = datetime(year=int(end[:4]), month=int(end[5:7]), day=int(end[8:10]), hour=int(end[11:13]),
                       minute=int(end[14:16]), second=int(end[17:19])) - datetime.now()

    if str(delta_t)[0] == '-':  # если время ожидания истекло возвращаем кнопке первоначальное значение
        cursor.execute(f'UPDATE users SET cut = "Подстричь", cut_uncut = True, end_timer = 0 WHERE user_id = ?',
                       (update.message.chat_id,))
        conn.commit()
        return True
    else:  # иначе получаем корректное время
        cursor.execute(f'UPDATE users SET cut = ? WHERE user_id = ?', (str(delta_t), update.message.chat_id,))
        conn.commit()
        return False


async def button(update, context):
    query = update.callback_query
    user_id = query.message.chat_id
    context.user_data['message_id'] = query.message.message_id

    if 'need' in query.data:
        if query.data == 'need_cut':
            t = db_check(query.message.chat_id)  # получаем данные

            if t[10]:  # если питомца можно подстричь
                end_time = datetime.now() + timedelta(minutes=t[7])  # считаем время окончания таймера
                delta_t = end_time - datetime.now()  # высчитаем время до конца таймера

                # сохраняем время начала таймера в базе данных
                cursor.execute('UPDATE users SET end_timer = ?, cut_uncut = False, cut = ? WHERE user_id = ?',
                               (str(end_time), str(delta_t)[:4], query.message.chat_id))
                conn.commit()

                user_info = db_check(query.message.chat_id)  # получаем обновленные данные

                cursor.execute('UPDATE items SET wool = wool + ? WHERE user_id = ?', (user_info[9], user_id,))
                conn.commit()

                # обновляем таймер на кнопке
                sheep_keyboard = [[InlineKeyboardButton(f'⏱ {user_info[4][:1]} ч. {user_info[4][2:4]} м.',
                                                        callback_data='need_cut')],
                                  [InlineKeyboardButton('🎒', callback_data='need_bag'),
                                   InlineKeyboardButton("🌱", callback_data='need_food')],
                                  [InlineKeyboardButton('👨‍🌾 Показатели', callback_data='need_info')]]

                markup = InlineKeyboardMarkup(sheep_keyboard)  # добавляем кнопки в сообщение

                await context.bot.edit_message_reply_markup(chat_id=user_id, message_id=context.user_data['message_id'],
                                                            reply_markup=markup)
                await bot.answer_callback_query(query.id, f'🧶 +{user_info[9]} шерсти')
            else:
                user_info1 = db_check(query.message.chat_id)
                if not delta_time(update):
                    user_info = db_check(query.message.chat_id)  # получаем обновленные данные

                    if user_info[4][:1] == user_info1[4][:1] and user_info[4][2:4] == user_info1[4][2:4]:
                        await bot.answer_callback_query(query.id, '⏱ Нужно подождать')

                    else:
                        # обновляем таймер на кнопке
                        sheep_keyboard = [[InlineKeyboardButton(f'⏱ {user_info[4][:1]} ч. {user_info[4][2:4]} м.',
                                                                callback_data='need_cut')],
                                          [InlineKeyboardButton('🎒', callback_data='need_bag'),
                                           InlineKeyboardButton("🌱", callback_data='need_food')],
                                          [InlineKeyboardButton('👨‍🌾 Показатели', callback_data='need_info')]]

                        markup = InlineKeyboardMarkup(sheep_keyboard)  # добавляем кнопки в сообщение

                        await context.bot.edit_message_reply_markup(chat_id=user_id,
                                                                    message_id=context.user_data['message_id'],
                                                                    reply_markup=markup)
                        await bot.answer_callback_query(query.id, '⏱ Нужно подождать')
                else:
                    user_info = db_check(query.message.from_user.id)
                    sheep_keyboard = [[InlineKeyboardButton(f'✂ {user_info[4]}', callback_data='need_cut')],
                                      [InlineKeyboardButton('🎒', callback_data='need_bag'),
                                       InlineKeyboardButton("🌱", callback_data='need_food')],
                                      [InlineKeyboardButton('👨‍🌾 Показатели', callback_data='need_info')]]

                    markup = InlineKeyboardMarkup(sheep_keyboard)  # добавляем кнопки в сообщение

                    await context.bot.edit_message_text(chat_id=user_id, message_id=context.user_data['message_id'],
                                                        text=f'🐑 {user_info[0]} уровень \n'
                                                             f'💵 {user_info[1]} 💎 {user_info[2]} \n'
                                                             f'🍽 {user_info[3]} % сытости')
                    await context.bot.edit_message_reply_markup(chat_id=user_id,
                                                                message_id=context.user_data['message_id'],
                                                                reply_markup=markup)

        elif query.data == 'need_bag':
            bag_info = db_check_bag(query.message.chat_id)  # получаем обновленные данные

            sheep_keyboard = [[InlineKeyboardButton(f'↩ Назад', callback_data='back')]]  # обновляем кнопки
            markup = InlineKeyboardMarkup(sheep_keyboard)  # добавляем кнопки в сообщение

            await context.bot.edit_message_text(chat_id=user_id, message_id=context.user_data['message_id'],
                                                text=f'Рюкзак \n'
                                                     f'------------------- \n'
                                                     f'🧶Шерсть: {bag_info[0]}')
            await context.bot.edit_message_reply_markup(chat_id=user_id, message_id=context.user_data['message_id'],
                                                        reply_markup=markup)

        elif query.data == 'need_food':
            user_info = db_check(query.message.chat_id)  # получаем обновленные данные

            sheep_keyboard = [[InlineKeyboardButton(f'↩ Назад', callback_data='back')]]  # обновляем кнопки

            markup = InlineKeyboardMarkup(sheep_keyboard)  # добавляем кнопки в сообщение

            await context.bot.edit_message_text(chat_id=user_id, message_id=context.user_data['message_id'],
                                                text=f'Еда \n'
                                                     f'------------------- \n')
            await context.bot.edit_message_reply_markup(chat_id=user_id,
                                                        message_id=context.user_data['message_id'],
                                                        reply_markup=markup)

        elif query.data == 'need_info':
            user_info = db_check(query.message.chat_id)  # получаем обновленные данные

            sheep_keyboard = [[InlineKeyboardButton(f'↩ Назад', callback_data='back')]]  # обновляем кнопки

            markup = InlineKeyboardMarkup(sheep_keyboard)  # добавляем кнопки в сообщение

            await context.bot.edit_message_text(chat_id=user_id, message_id=context.user_data['message_id'],
                                                text=f'Паспорт \n'
                                                     f'------------------- \n'
                                                     f'👨‍🌾Имя: {user_info[6]} \n'
                                                     f'⭐Прогресс: пупупу \n'
                                                     f'⏱Тайм: {user_info[7]} \n'
                                                     f'⚡Производительность: {user_info[9]} \n')
            await context.bot.edit_message_reply_markup(chat_id=user_id,
                                                        message_id=context.user_data['message_id'],
                                                        reply_markup=markup)

    elif query.data == 'back':
        user_info = db_check(query.message.chat_id)

        if not user_info[10]:  # создаем кнопки
            delta_time(update)
            sheep_keyboard = [[InlineKeyboardButton(f'⏱ {user_info[4][:1]} ч. {user_info[4][2:4]} м.',
                                                    callback_data='need_cut')],
                              [InlineKeyboardButton('🎒', callback_data='need_bag'),
                               InlineKeyboardButton("🌱", callback_data='need_food')],
                              [InlineKeyboardButton('👨‍🌾 Показатели', callback_data='need_info')]]
        else:
            sheep_keyboard = [[InlineKeyboardButton(f'✂ {user_info[4]}', callback_data='need_cut')],
                              [InlineKeyboardButton('🎒', callback_data='need_bag'),
                               InlineKeyboardButton("🌱", callback_data='need_food')],
                              [InlineKeyboardButton('👨‍🌾 Показатели', callback_data='need_info')]]

        markup = InlineKeyboardMarkup(sheep_keyboard)  # добавляем кнопки в сообщение

        await context.bot.edit_message_text(chat_id=user_id, message_id=context.user_data['message_id'],
                                            text=f'🐑 {user_info[0]} уровень \n'
                                                 f'💵 {user_info[1]} 💎 {user_info[2]} \n'
                                                 f'🍽 {user_info[3]} % сытости')
        await context.bot.edit_message_reply_markup(chat_id=user_id,
                                                    message_id=context.user_data['message_id'],
                                                    reply_markup=markup)

    elif 'trade' in query.data:
        if query.data == 'trade_wool-money':
            cursor.execute('UPDATE items SET wool = wool - 1 WHERE user_id = ?', (query.message.chat_id,))
            cursor.execute('UPDATE users SET money = money + 35 WHERE user_id = ?', (query.message.chat_id,))
            conn.commit()

            await bot.answer_callback_query(query.id, 'Операция успешна')


async def my_sheep(update, context):
    user_info = db_check(update.message.chat_id)

    if not user_info[10]:  # создаем кнопки
        delta_time_for_sheep(update)
        sheep_keyboard = [[InlineKeyboardButton(f'⏱ {user_info[4][:1]} ч. {user_info[4][2:4]} м.',
                                                callback_data='need_cut')],
                          [InlineKeyboardButton('🎒', callback_data='need_bag'),
                           InlineKeyboardButton("🌱", callback_data='need_food')],
                          [InlineKeyboardButton('👨‍🌾 Показатели', callback_data='need_info')]]
    else:
        sheep_keyboard = [[InlineKeyboardButton(f'✂ {user_info[4]}', callback_data='need_cut')],
                          [InlineKeyboardButton('🎒', callback_data='need_bag'),
                           InlineKeyboardButton("🌱", callback_data='need_food')],
                          [InlineKeyboardButton('👨‍🌾 Показатели', callback_data='need_info')]]

    markup = InlineKeyboardMarkup(sheep_keyboard)  # добавляем кнопки в сообщение

    await bot.send_sticker(update.message.chat_id,
                           'CAACAgIAAxkBAANfZDctaXmyF4wxVTvQnUqzOmIHhJQAAl4AA-SgzgddUrisymDHZC8E')
    await update.message.reply_text(f'🐑 {user_info[0]} уровень \n'
                                    f'💵 {user_info[1]} 💎 {user_info[2]} \n'
                                    f'🍽 {user_info[3]} % сытости', reply_markup=markup)


async def walk(update, context):
    cursor.execute('UPDATE users SET walk = False WHERE user_id = ?', (update.message.chat_id,))
    conn.commit()
    await update.message.reply_text('🏔 Овечка ушла скакать по горам')


async def trade(update, context):
    user_info = db_check(update.message.chat_id)

    # создаем кнопки
    trade_keyboard = [[InlineKeyboardButton('1 🧶 🔁 35 💵', callback_data='trade_wool-money')]]
    # добавляем кнопки в сообщение
    markup = InlineKeyboardMarkup(trade_keyboard)

    await update.message.reply_text(f'Добро пожаловать в обмен', reply_markup=markup)
