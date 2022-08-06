from random import randrange
from vk_api.vk_api import VkApiGroup
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vkt_bot_candidates import VkRequest
import re
from db import db_main
import configparser

config_db = configparser.ConfigParser()
config_db.read("config.ini")
token = config_db["VK"]["token"]
token_bot = config_db["VK"]["token_bot"]
vk_version = config_db["VK"]["vk_version"]

# club_url = 'https://vk.com/club214720213'
vk_search = VkRequest(token, vk_version, count_search=4)
PATTERN = r'^([мж]|муж[.скойчина]{0,4}|жен[.скийщна]{0,4})[\s,]{1,2}' \
          r'(\d{2,3})[ ,-]+' \
          r'(\d{2,3})[ ,]+' \
          r'([а-яё]{2,}(?:[ -]*\w+){2})\s*$'

# Названия кнопок (они же - команды)
SEARCH_BUTTON_TEXT = 'Поиск'
QUIT_BUTTON_TEXT = 'Выйти'
NEXT_BUTTON_TEXT = 'Следующий'
TO_FAVORITES_BUTTON_TEXT = 'В Избранное'
LIST_BUTTON_TEXT = 'Список'

vk = VkApiGroup(token=token_bot)
longpoll = VkLongPoll(vk)
print('<Бот стартовал>')


def send_msg(user_id, message, keyboard=None, attachment=None):
    """Отправить сообщение пользователю"""
    params = {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)}
    if keyboard:
        params['keyboard'] = keyboard.get_keyboard()
    if attachment:
        params['attachment'] = attachment
    vk.method('messages.send', params)
    print(f'< to user_id = {user_id} отправлено сообщение> {message}')


def get_user_info(user_id):
    return vk.method('users.get', {'user_ids': user_id, 'fields': 'sex, city, bdate'})[0]


def create_button(text, color):
    colors = {'green': VkKeyboardColor.POSITIVE,
              'red': VkKeyboardColor.NEGATIVE,
              'blue': VkKeyboardColor.PRIMARY,
              'white': VkKeyboardColor.SECONDARY}
    kb.add_button(text, colors[color])


def get_query_data(request, offset):
    """Обработка поступивших поисковых данных от пользователя для формирования запроса на поиск"""
    if request == NEXT_BUTTON_TEXT:
        print('in get_query_data_if_next', offset)
        # TODO SELECT из таблицы юзера (первая таблица) в переменную request_from_db в формате
        # {'sex': sex, 'age_from': age_from, 'age_to': age_to, 'hometown': city}}
        request_from_db = {} # заменить {} на данные из БД
        query_data = {**request_from_db, 'offset': offset}

    else:
        sex_, age_from_, age_to_, city = re.search(PATTERN, request, re.I).groups()
        sex = 2 if sex_[:1] == 'м' else 1
        age_from, age_to = list(map(int, [age_from_, age_to_]))
        if age_from > age_to:
            age_from, age_to = age_to, age_from
        query_data = {'offset': offset, 'sex': sex, 'age_from': age_from, 'age_to': age_to, 'hometown': city}
    print('query_data', query_data)
    return query_data


def get_skip_id(user_id, users_in_db) -> set:
    """Формирует список id кандидатов, которые не должны попадаться при поиске"""
    if user_id in users_in_db:
        # TODO 1)если user_id есть в БД (функция проверки),
        #  то 2) получить всех id_candidates этого user в переменную skip_id (формат set)
        skip_id = set()  # сюда из БД добавляем кандидатов, которых нужно будет пропускать при поиске
    else:
        skip_id = set()  # оставляем пустым для тех, кто юзеров, кто еще не в БД
    return skip_id


def new_search(request, offset, user_id, users_in_db):
    """Отрабатывает новый поиск"""
    print('<Отрабатывает новый поиск>')
    query_data = get_query_data(request, offset[user_id])
    print('query_data', query_data)
    send_msg(user_id, f'...Идет поиск ')
    skip_id = get_skip_id(user_id, users_in_db)
    candidates = {user_id: vk_search.users_search(skip_id, **query_data)}
    print('-->candidates - 1', candidates[user_id][:1])
    return candidates, query_data


def next_candidate(user_id):
    """Формирует и отправлет информацию о кандидате в БД и пользователю"""
    cand_data = db_main.get_next_candidate(user_id)
    print('cand_data', cand_data)
    msg = f"{cand_data['first_name']} {cand_data['last_name']}\n" \
          f"{cand_data['bdate']}\n" \
          f"https://vk.com/id{cand_data['vk_id']}\n"
    send_msg(user_id, msg, kb, cand_data['attach'])
    # TODO UPDATE в 3 табл - Viewed-пометка в 3 табл = True
    return cand_data['vk_id']


def set_buttons(num=None):
    """Задать набор кнопок"""
    create_button(SEARCH_BUTTON_TEXT, 'blue')
    if num == 'full':
        create_button(NEXT_BUTTON_TEXT, 'white')
        create_button(TO_FAVORITES_BUTTON_TEXT, 'green')
        create_button(LIST_BUTTON_TEXT, 'green')
    create_button(QUIT_BUTTON_TEXT, 'red')


# TODO Select из БД списка юзеров в переменную users_in_db -->set
users_in_db = set()  # должны быть подгружены данные из БД
offset = {}
last_cand = {}

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        request = event.text
        user_id = event.user_id
        print(f'<from user_id = {user_id} Получено сообщение>', request)
        user_name = get_user_info(user_id)['first_name']

        if request == SEARCH_BUTTON_TEXT:
            send_msg(user_id, 'Ввведите через пробел данные того, о ком грезите:\n'
                              'пол (м/ж)\n'
                              'желаемый диапазон возраста в годах (от и до)\n'
                              'и город, в котором искать. Например:\nж 20 25 Нижний Новгород')
            continue
        # получили поисковые данные и ищем по ним
        if re.search(PATTERN, request, re.I):
            offset[user_id] = 0
            candidates, query_data = new_search(request, offset, user_id, users_in_db)
            if candidates[user_id]:
                print('----candidates[user_id]!!!', candidates[user_id])
                if user_id not in users_in_db:
                    users_in_db.add(user_id)
                    db_main.add_botuser(query_data, user_id)  # --> добавление to botuser db
                else:
                    db_main.update_botuser(query_data, user_id)  # --> UPDATE данных нового запроса to botuser db
                db_main.add_candidates(candidates[user_id], user_id)  # --> добавление в candidate db
                kb = VkKeyboard(inline=True)
                set_buttons('full')
                last_cand[user_id] = next_candidate(user_id)
                continue
            else:
                send_msg(user_id, 'По указанным данным ничего не найдено.\n'
                                  'Попробуйте снова. Пример формата ввода:\nж 25 30 Киров')
                continue
        if request == NEXT_BUTTON_TEXT:
            try:
                print('-->in try')
                last_cand[user_id] = next_candidate(user_id)
            except NameError:
                send_msg(user_id, "Нужно поискать. Нажмите 'Поиск'")
            except IndexError:
                send_msg(user_id, '...')
                # send_msg(user_id, "А ведь больше нет. Нажмите 'Поиск', если хотите еще кого-нибудь поискать")
                offset[user_id] += vk_search.count_search
                candidates, query_data = new_search(request, offset, user_id, users_in_db)
                if candidates[user_id]:
                    db_main.add_candidates(candidates[user_id], user_id)  # --> добавление в candidate db
                    last_cand[user_id] = next_candidate(user_id)
                    print(last_cand)
                else:
                    send_msg(user_id, "А ведь больше нет. Нажмите 'Поиск', если хотите еще кого-нибудь поискать")
                continue
            continue
        if request == TO_FAVORITES_BUTTON_TEXT:
            # TODO Поставить галку в Избранном (3-я табл), id_candidate - из переменной last_cand[user_id]
            try:
                if last_cand[user_id]:
                    send_msg(user_id, "Кнопка сломана. Пока не получится добавить. Работаем над этим.")
            except NameError:
                send_msg(user_id, "Пока некого заносить в избранное. Нажмите 'Поиск'")
            continue
        if request == LIST_BUTTON_TEXT:
            # TODO Выдать из БД список в переменную
            #  и Заменить if (ниже) (т.к. пока затычка) на : "if переменная с данными от этого пользователя"
            if user_id in users_in_db:
                print('<Список будет позже>')
                send_msg(user_id, "Список избранных разработчиком пока не реализован. Довольствуйтесь тем, что еть.'")
            else:
                send_msg(user_id, "К огромному сожалению, у вас пока нет никого в избранном.'")
            continue
        if request == QUIT_BUTTON_TEXT:
            send_msg(user_id, f'Всего доброго, {user_name}!\nЕсли захотите вернуться, просто что-нибудь напишите')

        else:
            kb = VkKeyboard(inline=True)
            if user_id not in users_in_db:
                set_buttons()
                send_msg(event.user_id, f'Привет, {user_name}!\n'
                                        f'Предлагаю поискать варианты для новых отношений (нажмите на кнопку)', kb)
            else:
                set_buttons('full')
                help_text = "'Поиск' - новый поиск\n" \
                            "'Следующий' - перейти к следующему\n" \
                            "'В избранное' - добавить в избранное\n" \
                            "'Список' - вывести список избранных"
                send_msg(event.user_id, f'Привет, {user_name}!\n{help_text}', kb)
