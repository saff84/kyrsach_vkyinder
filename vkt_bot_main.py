from random import randrange
from vk_api.vk_api import VkApiGroup
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from pprint import pprint
from vkt_bot_candidates import VkRequest
from vkt_bot_config import token, token_bot, vk_version
import re

# club_url = 'https://vk.com/club214720213'
vk_item_main = VkRequest(token, vk_version)
pattern = r'^([мж]|муж[.скойчина]{0,4}|жен[.скийщна]{0,4})[\s,]{1,2}' \
          '(\d{2,3})[ ,-]+' \
          '(\d{2,3})[ ,]+' \
          '([а-яё]{2,}(?:[ -]*\w+){2})\s*$'
inviting_text = 'Предлагаю поискать варианты для новых отношений (нажмите на кнопку)'


search_button_text = 'Поиск'
search_query_text = 'Ввведите через пробел данные того, о ком грезите:\n' \
                    'пол (м/ж)\n' \
                    'желаемый диапазон возраста в годах (от и до)\n' \
                    'и город, в котором искать. Например:\nж 20 25 Нижний Новгород'
help_text = "'Поиск' - новый поиск\n"\
            "'Следующий' - перейти к следующему\n" \
            "'В избранное' - добавить в избранное\n" \
            "'Список' - вывести список избранных"
quit_button_text = 'Выйти'



vk = VkApiGroup(token=token_bot)
longpoll = VkLongPoll(vk)
print('<Бот стартовал>')


def send_msg(user_id, message, keyboard=None, attachment=None):
    params = {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7)}
    if keyboard:
        params['keyboard'] = keyboard.get_keyboard()
    if attachment:
        params['attachment'] = attachment
        print('attachment', params['attachment'])

    vk.method('messages.send', params)
    pprint(params)
    print(f'< to user_id = {user_id} отправлено сообщение> {message}')

def get_user_info(user_id):
    return vk.method('users.get', {'user_ids': user_id, 'fields': 'sex, city, bdate'})[0]

def create_button(text, color=VkKeyboardColor.SECONDARY):
    colors = {'green': VkKeyboardColor.POSITIVE,
              'red': VkKeyboardColor.NEGATIVE,
              'blue': VkKeyboardColor.PRIMARY,
              'white': VkKeyboardColor.SECONDARY}
    kb.add_button(text, colors[color])

def get_query_data(request):
    """Обработка поступивших поисковых данных от пользователя для формирования запроса на поиск"""
    sex_, age_from_, age_to_, city = re.search(pattern, request, re.I).groups()
    sex = 2 if sex_[:1] == 'м' else 1
    age_from, age_to = list(map(int, [age_from_, age_to_]))
    if age_from > age_to:
        age_from, age_to = age_to, age_from
    print('query_data', {'sex': sex, 'age_from': age_from, 'age_to': age_to, 'hometown': city})
    return {'sex': sex, 'age_from': age_from, 'age_to': age_to, 'hometown': city}

def get_skip_id(user_id, users_in_db):
    if user_id in users_in_db:
        # TODO если user_id есть в БД, получить всех id_candidates этого user в переменную skip_id (формат set)
        skip_id = set()  # сюда из БД добавляем кандидатов, которых нужно будет пропускать при поиске
    else:
        skip_id = set()  # оставляем пустым для тех, кто юзеров, кто еще не в БД
    return skip_id

def next_candidate(cand):
    """Формирует и отправлет информацию о кандидате в БД и пользователю"""
    # TODO Записать в БД, что кандидат просмотрен
    cand_data = next(cand)
    msg = f"{cand_data['first_name']} {cand_data['last_name']}\n" \
          f"{cand_data['bdate']}\n" \
          f"https://vk.com/id{cand_data['vk_id']}\n"
    send_msg(user_id, msg, kb, cand_data['attach'])



# TODO Select из БД списка юзеров в переменную users_in_db -->set
users_in_db = set() # должны быть подгружены данные из БД

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        request = event.text
        user_id = event.user_id
        print(f'<from user_id = {user_id} Получено сообщение>', request)
        user_name = get_user_info(user_id)['first_name']

        if request == search_button_text:
            kb = VkKeyboard(inline=True)
            send_msg(user_id, search_query_text)
            continue
        # получили поисковые данные и ищем по ним
        if re.search(pattern, request, re.I):
            query_data = get_query_data(request)
            skip_id = get_skip_id(user_id, users_in_db)
            candidates = vk_item_main.users_search(skip_id, **query_data)
            print('-->candidates - 1', candidates[:1])
            if candidates:
                if user_id not in users_in_db:
                    users_in_db.add(user_id)

                kb = VkKeyboard(inline=True)
                create_button(search_button_text, 'blue')
                create_button('Следующий', 'white')
                create_button('В избранное', 'green')
                create_button('Список', 'green')
                create_button(quit_button_text, 'red')

                cand = iter(candidates)
                next_candidate(cand)
                continue
            else:
                send_msg(user_id, 'По указанным данным ничего не найдено.\n'
                                  'Попробуйте снова. Пример формата ввода:\nж 25 30 Киров')
                continue
        if request == 'Следующий':
            try:
                next_candidate(cand)
            except NameError:
                send_msg(user_id, "Нужно поискать. Нажмите 'Поиск'")
            except StopIteration:
                send_msg(user_id, "А ведь больше нет. Нажмите 'Поиск', если хотите еще кого-нибудь поискать")
            continue
        if request == 'В избранное':
            # TODO Записать в БД из переменной cand_data
            try:
                if cand:
                    send_msg(user_id, "Кнопка сломана. Пока не получится добавить. Работаем над этим.")
            except NameError:
                send_msg(user_id, "Пока некого заносить в избранное. Нажмите 'Поиск'")
            continue
        if request == 'Список':
            # TODO Выдать из БД список в переменную
            # TODO Заменить if (т.к. пока затычка) на : if переменная с данными от этого пользователь
            if user_id in users_in_db:
                print('<Список будет позже>')
                send_msg(user_id, "Список избранных разработчиком пока не реализован. Довольствуйтесь тем, что еть.'")
            else:
                send_msg(user_id, "К огромному сожалению, у вас пока нет никого в избранном.'")
            continue
        if request == quit_button_text:
            send_msg(user_id, f'Всего доброго, {user_name}!\nЕсли захотите вернуться, просто что-нибудь напишите')

        else:
            if user_id not in users_in_db:
                kb = VkKeyboard(inline=True)
                create_button(search_button_text, 'blue')
                create_button(quit_button_text, 'red')
                send_msg(event.user_id, f'Привет, {user_name}!\n{inviting_text}', kb)
            else:
                kb = VkKeyboard(inline=True)
                create_button(search_button_text, 'blue')
                create_button('Следующий', 'white')
                create_button('В избранное', 'green')
                create_button('Список', 'green')
                create_button(quit_button_text, 'red')
                send_msg(event.user_id, f'Привет, {user_name}!\n{help_text}', kb)
