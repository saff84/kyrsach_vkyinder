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

vk_search = VkRequest(token, vk_version, count_search=6)
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
        # SELECT из таблицы юзера (первая таблица) в переменную request_from_db в формате
        # {'sex': sex, 'age_from': age_from, 'age_to': age_to, 'hometown': city}}
        request_from_db = db_main.get_search_parameters(user_id) #-> запрос поисковых параметров в БД если ботюзер уже есть
        print('request_from_db', request_from_db)
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
        skip_id = db_main.get_all_id_candidates(user_id)  # кандидаты, которых нужно будет пропускать при поиске
    else:
        skip_id = set()  # оставляем пустым для тех, кто юзеров, кто еще не в БД
    return skip_id


def new_search(request, offset, user_id, users_in_db):
    """Отрабатывает новый поиск"""
    print('<Отрабатывает новый поиск>')
    print('request, offset', request, offset[user_id])
    query_data = get_query_data(request, offset[user_id])
    print('request, offset', query_data)
    print('query_data-start', query_data)
    send_msg(user_id, f'...Идет поиск ')
    skip_id = get_skip_id(user_id, users_in_db)
    candidates = {user_id: vk_search.users_search(skip_id, **query_data)}
    print('-->candidates - 1', candidates[user_id][:1])
    return candidates, query_data


def next_candidate(user_id):
    """Формирует и отправлет информацию о кандидате в БД и пользователю"""
    print('in next_candidate', user_id)
    cand_data = db_main.get_next_candidate(user_id)
    print('cand_data', cand_data)
    msg = f"{cand_data['first_name']} {cand_data['last_name']}\n" \
          f"{cand_data['bdate']}\n" \
          f"https://vk.com/id{cand_data['vk_id']}\n"
    send_msg(user_id, msg, kb, cand_data['attach'])
    # Viewed-пометка в 3 табл = True
    db_main.candidate_viewed(cand_data['vk_id'], user_id)
    return cand_data['vk_id']


def set_buttons(num=None):
    """Задать набор кнопок"""
    create_button(SEARCH_BUTTON_TEXT, 'blue')
    if num == 'full':
        create_button(NEXT_BUTTON_TEXT, 'white')
        create_button(TO_FAVORITES_BUTTON_TEXT, 'green')
        create_button(LIST_BUTTON_TEXT, 'green')
    create_button(QUIT_BUTTON_TEXT, 'red')


users_in_db = db_main.get_users_in_db()  # ------> селект всех ботюзеров из БД в виде vk_id
print(users_in_db)
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
                    db_main.add_botuser(query_data, user_id)  # -> добавление to botuser db
                else:
                    ('--Новый запрос--')
                    db_main.update_botuser(query_data, user_id)  # -> UPDATE данных нового запроса to botuser db
                    if db_main.check_unviewed(user_id): # -> если непросмотренные в предыдущем поиске
                        print('--Однако есть еще непросмотренные--')
                        db_main.delete_unviewed(user_id) # -> DELETE непросмотренных из предыдущего поиска
                print('before add_candidates')
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
            try:
                if user_id in last_cand:
                    print(f'last_cand[user_id]', last_cand[user_id])
                    db_main.candidate_to_favorite(user_id, last_cand[user_id])
                    send_msg(user_id, "Добавлено в избранное")
                else:
                    print('Нет никого для занесения')
            except NameError:
                send_msg(user_id, "Пока некого заносить в избранное. Нажмите 'Поиск'")
            continue
        if request == LIST_BUTTON_TEXT:
            favorites_list = db_main.get_favorites_list(user_id)
            if favorites_list:
                send_msg(user_id, favorites_list)
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
