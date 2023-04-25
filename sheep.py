import sqlite3
from aiogram import Bot
from config import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from random import choice, randint

bot = Bot(token=TOKEN, parse_mode='HTML')
conn = sqlite3.connect('sheeps.db')  # создаем подключение к БД
cursor = conn.cursor()


def users_check(user_id):  # получаем данные из БД
    return cursor.execute('SELECT level, money, diamonds, food, cut, walk, user_name, timer, end_timer, power,'
                          ' cut_uncut, end_walk, walk_unwalk'
                          ' FROM users WHERE user_id = ?', (user_id,)).fetchall()[0]


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def hungry(user_id):
    minus = randint(4, 11)
    cursor.execute(f'UPDATE users SET food = food - ? WHERE user_id = ?', (minus, user_id,))
    conn.commit()


def delta_time(update):  # функция для подсчета оставшегося времени
    query = update.callback_query
    end = users_check(query.message.chat_id)[8]  # получаем время окончания
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


def delta_walk(update):
    query = update.callback_query
    end = users_check(query.message.chat_id)[11]  # получаем время окончания
    delta_w = datetime(year=int(end[:4]), month=int(end[5:7]), day=int(end[8:10]), hour=int(end[11:13]),
                       minute=int(end[14:16]), second=int(end[17:19])) - datetime.now()  # считаем остаток времени

    if str(delta_w)[0] == '-':  # если время ожидания истекло возвращаем кнопке первоначальное значение
        cursor.execute(f'UPDATE users SET walk = "Гулять", walk_unwalk = True, end_walk = 0 WHERE user_id = ?',
                       (query.message.chat_id,))
        conn.commit()
        return True
    else:  # иначе вводим корректное время
        cursor.execute(f'UPDATE users SET walk = ? WHERE user_id = ?', (str(delta_w), query.message.chat_id,))
        conn.commit()
        return False


def delta_time_for_sheep(update):  # функция для подсчета оставшегося времени
    end = users_check(update.message.chat_id)[8]
    if end != 0:
        delta_t = datetime(year=int(end[:4]), month=int(end[5:7]), day=int(end[8:10]), hour=int(end[11:13]),
                           minute=int(end[14:16]), second=int(end[17:19])) - datetime.now()
    else:
        delta_t = '-'

    if str(delta_t)[0] == '-':  # если время ожидания истекло возвращаем кнопке первоначальное значение
        cursor.execute(f'UPDATE users SET cut = "Подстричь", cut_uncut = True, end_timer = 0 WHERE user_id = ?',
                       (update.message.chat_id,))
        conn.commit()
        return True
    else:  # иначе получаем корректное время
        cursor.execute(f'UPDATE users SET cut = ? WHERE user_id = ?', (str(delta_t), update.message.chat_id,))
        conn.commit()
        return False


def delta_walk_for_walk(update):
    end = users_check(update.message.chat_id)[11]  # получаем время окончания
    if end != 0:
        delta_w = datetime(year=int(end[:4]), month=int(end[5:7]), day=int(end[8:10]), hour=int(end[11:13]),
                           minute=int(end[14:16]), second=int(end[17:19])) - datetime.now()  # считаем остаток времени
    else:
        delta_w = '-'

    if str(delta_w)[0] == '-':  # если время ожидания истекло возвращаем кнопке первоначальное значение
        cursor.execute(f'UPDATE users SET walk = "Гулять", walk_unwalk = True, end_walk = 0 WHERE user_id = ?',
                       (update.message.chat_id,))
        conn.commit()
        return True
    else:  # иначе вводим корректное время
        cursor.execute(f'UPDATE users SET walk = ? WHERE user_id = ?', (str(delta_w), update.message.chat_id,))
        conn.commit()
        return False


async def button(update, context):
    query = update.callback_query
    user_id = query.message.chat_id
    context.user_data['message_id'] = query.message.message_id

    if 'need' in query.data:
        if query.data == 'need_cut':
            t = users_check(query.message.chat_id)  # получаем данные

            if t[10]:  # если питомца можно подстричь
                end_time = datetime.now() + timedelta(minutes=t[7])  # считаем время окончания таймера
                delta_t = end_time - datetime.now()  # высчитаем время до конца таймера

                # сохраняем время начала таймера в базе данных
                cursor.execute('UPDATE users SET end_timer = ?, cut_uncut = False, cut = ? WHERE user_id = ?',
                               (str(end_time), str(delta_t)[:4], query.message.chat_id))
                conn.commit()

                user_info = users_check(query.message.chat_id)  # получаем обновленные данные
                try:
                    cursor.execute(f'UPDATE all_users_items SET item_count = '
                                   f'item_count + ? WHERE user_id = ? AND item_id = ?',
                                   (user_info[9], query.message.chat_id, 'I01'))
                    conn.commit()
                except Exception:
                    cursor.execute('INSERT INTO all_users_items VALUES (?, ?, ?)',
                                   (query.message.chat_id, 'I01', user_info[9]))
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
                hungry(user_id)
            else:
                user_info1 = users_check(query.message.chat_id)
                if not delta_time(update):
                    user_info = users_check(query.message.chat_id)  # получаем обновленные данные

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
                    user_info = users_check(query.message.from_user.id)
                    sheep_keyboard = [[InlineKeyboardButton(f'✂ {user_info[4]}', callback_data='need_cut')],
                                      [InlineKeyboardButton('🎒', callback_data='need_bag'),
                                       InlineKeyboardButton("🌱", callback_data='need_food')],
                                      [InlineKeyboardButton('👨‍🌾 Показатели', callback_data='need_info')]]

                    markup = InlineKeyboardMarkup(sheep_keyboard)  # добавляем кнопки в сообщение

                    """await context.bot.edit_message_text(chat_id=user_id, message_id=context.user_data['message_id'],
                                                        text=f'🐑 {user_info[0]} уровень \n'
                                                             f'💵 {user_info[1]} 💎 {user_info[2]} \n'
                                                             f'🍽 {user_info[3]} % сытости')"""
                    await context.bot.edit_message_reply_markup(chat_id=user_id,
                                                                message_id=context.user_data['message_id'],
                                                                reply_markup=markup)

        elif query.data == 'need_bag':

            sheep_keyboard = [[InlineKeyboardButton(f'↩ Назад', callback_data='back')]]  # обновляем кнопки
            markup = InlineKeyboardMarkup(sheep_keyboard)  # добавляем кнопки в сообщение
            text = ''

            items = cursor.execute('SELECT item_id, item_count FROM all_users_items WHERE user_id = ? '
                                   'AND item_count != 0',
                                   (user_id,)).fetchall()

            for i in range(len(items)):
                sticker = cursor.execute("SELECT item_stick FROM items WHERE item_id = ?", (items[i][0],)).fetchone()[0]
                if i % 2 != 0:
                    text += f' {sticker} {items[i][1]} \n'
                else:
                    text += f'{sticker} {items[i][1]}'

            await context.bot.edit_message_text(chat_id=user_id, message_id=context.user_data['message_id'],
                                                text=f'Рюкзак \n'
                                                     f'------------------- \n'
                                                     f'{text}')
            await context.bot.edit_message_reply_markup(chat_id=user_id, message_id=context.user_data['message_id'],
                                                        reply_markup=markup)

        elif query.data == 'need_food':
            keyboard = []
            foods = cursor.execute('SELECT food_id, food_count FROM all_users_foods WHERE user_id = ?',
                                   (user_id,)).fetchall()

            for i in range(len(foods)):
                if foods[i][1] < 1:
                    pass
                else:
                    sticker = cursor.execute("SELECT food_stick FROM foods WHERE food_id = ?",
                                             (foods[i][0],)).fetchone()[0]
                    keyboard.append(InlineKeyboardButton(f'{sticker} {foods[i][1]}',
                                                         callback_data=f'eat_{foods[i][0]}'))
            keyboard.append(InlineKeyboardButton(f'↩ Назад', callback_data='back'))
            markup = InlineKeyboardMarkup(build_menu(keyboard, n_cols=2))

            await context.bot.edit_message_text(chat_id=user_id, message_id=context.user_data['message_id'],
                                                text=f'Еда \n')
            await context.bot.edit_message_reply_markup(chat_id=user_id,
                                                        message_id=context.user_data['message_id'],
                                                        reply_markup=markup)

        elif query.data == 'need_info':
            user_info = users_check(query.message.chat_id)  # получаем обновленные данные

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

    elif 'eat' in query.data:
        energy = cursor.execute('SELECT energy FROM foods WHERE food_id = ?', (query.data[4:7],)).fetchone()[0]
        food = cursor.execute('SELECT food FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]
        if (food + energy) > 100:
            new_food = (food + energy) - ((food + energy) % 100)
        else:
            new_food = food + energy
        cursor.execute('UPDATE all_users_foods SET food_count = food_count - 1 WHERE user_id = ? AND food_id = ?',
                       (user_id, query.data[4:7],))
        cursor.execute('UPDATE users SET food = ? WHERE user_id = ?', (new_food, user_id,))
        conn.commit()

        keyboard = []
        foods = cursor.execute('SELECT food_id, food_count FROM all_users_foods WHERE user_id = ?',
                               (user_id,)).fetchall()

        for i in range(len(foods)):
            if foods[i][1] < 1:
                pass
            else:
                sticker = cursor.execute("SELECT food_stick FROM foods WHERE food_id = ?",
                                         (foods[i][0],)).fetchone()[0]
                keyboard.append(InlineKeyboardButton(f'{sticker} {foods[i][1]}',
                                                     callback_data=f'eat_{foods[i][0]}'))
        keyboard.append(InlineKeyboardButton(f'↩ Назад', callback_data='back'))
        markup = InlineKeyboardMarkup(build_menu(keyboard, n_cols=2))

        await bot.answer_callback_query(query.id, f'🍽 + {energy} к еде')
        await context.bot.edit_message_reply_markup(chat_id=user_id,
                                                    message_id=context.user_data['message_id'],
                                                    reply_markup=markup)

    elif query.data == 'back':
        user_info = users_check(query.message.chat_id)

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

    elif query.data == 'walk':
        w = users_check(query.message.chat_id)  # получаем данные

        if w[12]:  # если питомца можно подстричь
            choice_list = cursor.execute('SELECT item_id FROM items WHERE req_level = ?', (w[0],)).fetchall()
            end_walk = datetime.now() + timedelta(minutes=180)  # считаем время окончания таймера
            delta_w = end_walk - datetime.now()  # высчитаем время до конца таймера

            # сохраняем время начала таймера в базе данных
            cursor.execute('UPDATE users SET end_walk = ?, walk_unwalk = False, walk = ? WHERE user_id = ?',
                           (str(end_walk), str(delta_w)[:4], query.message.chat_id))
            conn.commit()

            user_info = users_check(query.message.chat_id)  # получаем обновленные данные
            item_id = choice(choice_list)[0]
            plus = randint(1, 5)

            try:
                cursor.execute(f'UPDATE all_users_items SET item_count = '
                               f'item_count + ? WHERE user_id = ? AND item_id = ?',
                               (plus, query.message.chat_id, item_id))
                conn.commit()
            except Exception:
                cursor.execute('INSERT INTO all_users_items VALUES (?, ?, ?)',
                               (query.message.chat_id, item_id, plus))
                conn.commit()

            new_item = cursor.execute('SELECT item_stick FROM items WHERE item_id = ?', (item_id,)).fetchone()[0]
            # обновляем таймер на кнопке
            keyboard = [[InlineKeyboardButton(f'⏱ {user_info[5][:1]} ч. {user_info[5][2:4]} м.',
                                              callback_data='walk')]]

            markup = InlineKeyboardMarkup(keyboard)  # добавляем кнопки в сообщение

            await context.bot.edit_message_reply_markup(chat_id=user_id, message_id=context.user_data['message_id'],
                                                        reply_markup=markup)
            await bot.answer_callback_query(query.id, f'+{plus} {new_item}')
            hungry(user_id)
        else:
            user_info1 = users_check(query.message.chat_id)
            if not delta_walk(update):
                user_info = users_check(query.message.chat_id)  # получаем обновленные данные

                if user_info[5][:1] == user_info1[5][:1] and user_info[5][2:4] == user_info1[5][2:4]:
                    await bot.answer_callback_query(query.id, '⏱ Нужно подождать')

                else:
                    # обновляем таймер на кнопке
                    keyboard = [[InlineKeyboardButton(f'⏱ {user_info[5][:1]} ч. {user_info[5][2:4]} м.',
                                                      callback_data='walk')]]

                    markup = InlineKeyboardMarkup(keyboard)  # добавляем кнопки в сообщение

                    await context.bot.edit_message_reply_markup(chat_id=user_id,
                                                                message_id=context.user_data['message_id'],
                                                                reply_markup=markup)
                    await bot.answer_callback_query(query.id, '⏱ Нужно подождать')
            else:
                user_info = users_check(query.message.from_user.id)
                keyboard = [[InlineKeyboardButton(f'🏔 {user_info[5]}', callback_data='walk')]]

                markup = InlineKeyboardMarkup(keyboard)  # добавляем кнопки в сообщение

                await context.bot.edit_message_reply_markup(chat_id=user_id,
                                                            message_id=context.user_data['message_id'],
                                                            reply_markup=markup)

    elif 'trade' in query.data:
        info = query.data.split('_')
        if 'I' in info[1]:
            try:
                count = cursor.execute('SELECT item_count FROM all_users_items WHERE user_id = ? AND item_id = ?',
                                       (query.message.chat_id, info[1])).fetchone()[0]
            except Exception:
                cursor.execute('INSERT INTO all_users_items VALUES (?, ?, ?)',
                               (query.message.chat_id, info[1], 0))
                conn.commit()
                count = cursor.execute('SELECT item_count FROM all_users_items WHERE user_id = ? AND item_id = ?',
                                       (query.message.chat_id, info[1])).fetchone()[0]
            if count > 0:
                try:
                    cursor.execute('UPDATE users SET money = money + ? WHERE user_id = ?',
                                   (info[2], query.message.chat_id))
                    cursor.execute('UPDATE all_users_items SET item_count = '
                                   'item_count - 1 WHERE user_id = ? AND item_id = ?',
                                   (query.message.chat_id, info[1]))
                    conn.commit()
                except Exception:
                    cursor.execute('UPDATE users SET money = money + ? WHERE user_id = ?',
                                   (info[2], query.message.chat_id))
                    cursor.execute('INSERT INTO all_users_items VALUES (?, ?, ?)',
                                   (query.message.chat_id, info[1], 1))
                    conn.commit()
                await bot.answer_callback_query(query.id, f'💵 +{info[2]}')

        elif 'I' in info[2]:
            money = cursor.execute('SELECT money FROM users WHERE user_id = ?',
                                   (query.message.chat_id,)).fetchone()[0]
            if money >= int(info[1]):
                try:
                    sticker = cursor.execute("SELECT item_stick FROM items WHERE item_id = ?",
                                             (info[2],)).fetchone()[0]
                    cursor.execute('UPDATE all_users_items SET item_count = '
                                   'item_count + 1 WHERE user_id = ? AND item_id = ?',
                                   (query.message.chat_id, info[2]))
                    cursor.execute('UPDATE users SET money = money - ? WHERE user_id = ?',
                                (info[1], query.message.chat_id))
                    conn.commit()
                except Exception:
                    sticker = cursor.execute("SELECT item_stick FROM items WHERE item_id = ?",
                                             (info[2],)).fetchone()[0]
                    cursor.execute('UPDATE users SET money = money - ? WHERE user_id = ?',
                                   (info[1], query.message.chat_id))
                    cursor.execute('INSERT INTO all_users_items VALUES (?, ?, ?)',
                                   (query.message.chat_id, info[2], 1))
                    conn.commit()
                await bot.answer_callback_query(query.id, f'{sticker} +1')

        elif 'F' in info[1]:
            try:
                count = cursor.execute('SELECT food_count FROM all_users_foods WHERE user_id = ? AND food_id = ?',
                                       (query.message.chat_id, info[1])).fetchone()[0]
            except Exception:
                cursor.execute('INSERT INTO all_users_foods VALUES (?, ?, ?)',
                               (query.message.chat_id, info[1], 0))
                conn.commit()
                count = cursor.execute('SELECT food_count FROM all_users_foods WHERE user_id = ? AND food_id = ?',
                                       (query.message.chat_id, info[1])).fetchone()[0]
            if count > 0:
                try:
                    cursor.execute('UPDATE users SET money = money + ? WHERE user_id = ?',
                                   (info[2], query.message.chat_id))
                    cursor.execute('UPDATE all_users_foods SET food_count = '
                                   'food_count - 1 WHERE user_id = ? AND food_id = ?',
                                   (query.message.chat_id, info[1]))
                    conn.commit()
                except Exception:
                    cursor.execute('UPDATE users SET money = money + ? WHERE user_id = ?',
                                   (info[2], query.message.chat_id))
                    cursor.execute('INSERT INTO all_users_foods VALUES (?, ?, ?)',
                                   (query.message.chat_id, info[1], 1))
                    conn.commit()
                await bot.answer_callback_query(query.id, f'💵 +{info[2]}')

        elif 'F' in info[2]:
            money = cursor.execute('SELECT money FROM users WHERE user_id = ?',
                                   (query.message.chat_id,)).fetchone()[0]
            if money >= int(info[1]):
                try:
                    sticker = cursor.execute("SELECT food_stick FROM foods WHERE food_id = ?",
                                             (info[2],)).fetchone()[0]
                    cursor.execute('UPDATE all_users_foods SET food_count = '
                                   'food_count + 1 WHERE user_id = ? AND food_id = ?',
                                   (query.message.chat_id, info[2]))
                    cursor.execute('UPDATE users SET money = money - ? WHERE user_id = ?',
                                   (info[1], query.message.chat_id))
                    conn.commit()
                except Exception:
                    sticker = cursor.execute("SELECT food_stick FROM foods WHERE food_id = ?",
                                             (info[2],)).fetchone()[0]
                    cursor.execute('UPDATE users SET money = money - ? WHERE user_id = ?',
                                   (info[1], query.message.chat_id))
                    cursor.execute('INSERT INTO all_users_foods VALUES (?, ?, ?)',
                                   (query.message.chat_id, info[2], 1))
                    conn.commit()
                await bot.answer_callback_query(query.id, f'{sticker} +1')


async def my_sheep(update, context):
    delta_time_for_sheep(update)
    user_info = users_check(update.message.chat_id)

    if not user_info[10]:  # создаем кнопки
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
    delta_walk_for_walk(update)
    user_info = users_check(update.message.chat_id)
    if not user_info[12]:  # создаем кнопки
        walk_keyboard = [[InlineKeyboardButton(f'⏱ {user_info[5][:1]} ч. {user_info[5][2:4]} м.',
                                               callback_data='walk')]]
    else:
        walk_keyboard = [[InlineKeyboardButton(f'🏔 {user_info[5]}', callback_data='walk')]]

    markup = InlineKeyboardMarkup(walk_keyboard)
    await update.message.reply_text('Хочешь отправить овечку на прогулку?', reply_markup=markup)


async def trade(update, context):
    # создаем кнопки
    trade_keyboard = [[InlineKeyboardButton('1 🧶 🔁 40 💵', callback_data='trade_I01_40'),
                       InlineKeyboardButton('50 💵 🔁 1 🧶', callback_data='trade_50_I01')],
                      [InlineKeyboardButton('1 🧤 🔁 95 💵', callback_data='trade_I02_95'),
                       InlineKeyboardButton('110 💵 🔁 1 🧤', callback_data='trade_110_I02')],
                      [InlineKeyboardButton('1 🧦 🔁 95 💵', callback_data='trade_I03_95'),
                       InlineKeyboardButton('110 💵 🔁 1 🧦', callback_data='trade_110_I03')],
                      [InlineKeyboardButton('1 🧣 🔁 180 💵', callback_data='trade_I04_180'),
                       InlineKeyboardButton('200 💵 🔁 1 🧣', callback_data='trade_200_I04')],
                      [InlineKeyboardButton('1 🌱 🔁 15 💵', callback_data='trade_F01_15'),
                       InlineKeyboardButton('20 💵 🔁 1 🌱', callback_data='trade_20_F01')],
                      [InlineKeyboardButton('1 🌿 🔁 25 💵', callback_data='trade_F02_25'),
                       InlineKeyboardButton('30 💵 🔁 1 🌿', callback_data='trade_30_F02')],
                      [InlineKeyboardButton('1 🌾 🔁 35 💵', callback_data='trade_F03_35'),
                       InlineKeyboardButton('40 💵 🔁 1 🌾', callback_data='trade_40_F03')],
                      [InlineKeyboardButton('1 🫘 🔁 45 💵', callback_data='trade_F04_45'),
                       InlineKeyboardButton('50 💵 🔁 1 🫘', callback_data='trade_50_F04')]]
    # добавляем кнопки в сообщение
    markup = InlineKeyboardMarkup(trade_keyboard)

    await update.message.reply_text(f'Добро пожаловать в обмен', reply_markup=markup)


async def bazar(update, context):
    pass


async def market(update, context):
    pass
