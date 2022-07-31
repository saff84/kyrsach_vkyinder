from random import randrange
from vk_api.vk_api import VkApiGroup
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from pprint import pprint
from vkt_bot_candidates import VkRequest
from vkt_bot_config import token, token_bot, vk_version


vk_item_main = VkRequest(token, vk_version)
inviting_text = 'Предлагаю поискать варианты для новых отношений (нажмите на кнопку)'
search_button_text = 'Поиск'
search_age_city_text = 'Ввведите через пробел желаемый диапазон возраста (в годах) и город, ' \
                       'в котором искать. Например:\n20 25 Нижний Новгород'
help_text = "'Поиск' - новый поиск\n"\
            "'Следующий' - перейти к следующему\n" \
            "'В избранное' - добавить в избранное\n" \
            "'Список' - вывести список избранных"

quit_button_text = 'Выйти'
male_button_text = 'Мужика бы мне'
female_button_text = 'Женщину хочу'

# club_url = 'https://vk.com/club214720213'

# vk = vk_api.VkApi(token=token)
vk = VkApiGroup(token=token_bot)
longpoll = VkLongPoll(vk)
print('<Бот стартовал>')


def send_msg(user_id, message, keyboard=None, attachment=None):
    params = {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7)}
    if keyboard:
        params['keyboard'] = keyboard.get_keyboard()
    if attachment:
        params['attachment'] = ','.join(attachment)
        print(params['attachment'])

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


def get_age_city_data(request):
    try:
        age_from, age_to, *city_name = request.split()
        age_from = int(age_from)
        age_to = int(age_to)
        city_name = ' '.join(city_name)
        city_id, city_name_db = vk_item_main.database_getCities(city_name)
        print(age_from, age_to, city_name_db)
        if age_from not in range(0, 125) or age_to not in range(0, 125):
            print('<Возраст вне диапазона>')
            raise
    except:
        print('--ошибка--'*5)
        return False
    if age_from > age_to:
        age_from, age_to = age_to, age_from
    return {'age_from': age_from, 'age_to': age_to, 'city': city_id}

def next_candidate(cand):
    """Формирует и отправлет информацию о кандидате в БД и пользователю"""

    # TODO Записать в БД
    cand_data = next(cand)
    msg = f"{cand_data['first_name']} {cand_data['last_name']}\n" \
          f"{cand_data['bdate']}\n" \
          f"https://vk.com/id{cand_data['vk_id']}\n"
    send_msg(user_id, msg, kb, cand_data['attach'])



# TODO Select из БД списка юзеров в переменную users_in_db -->set
users_in_db = {999, 888, 7413785340}


# user_id = 0
# query_info = {'user_id': user_id}

flag = False
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        request = event.text
        user_id = event.user_id
        print(f'<from user_id = {user_id} Получено сообщение>', request)
        user_name = get_user_info(user_id)['first_name']

        if request == search_button_text:
            kb = VkKeyboard(inline=True)
            create_button(male_button_text, 'blue')
            create_button(female_button_text, 'red')
            send_msg(user_id, 'Отлично! Поехали.\nКого будем искать (нажмите кнопку)?', kb)
            continue
        if request in (male_button_text, female_button_text):
            # создаем форму для заполнения в БД и вносим первые данные: id и sex:
            query_info = {'user_id': user_id}
            query_info['sex'] = 2 if request == male_button_text else 1
            print('query_info: ', query_info)
            send_msg(user_id, search_age_city_text)
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me and user_id == event.user_id:
                    request = event.text
                    age_city_dict = get_age_city_data(request)
                    if age_city_dict:
                        query_info = {**query_info, **age_city_dict}
                        print(query_info)
                        #добавляем user в текущую переменную, чтобы понимать, что...
                        #TODO в идеале это надо делать одновременно (сразу после) и не вносить самому,
                        # а запрос из БД на обновление
                        # т.е по сути не надо проверять, а сначала добавить в базу запрос и результаты поиска
                        if user_id not in users_in_db:
                            users_in_db.add(user_id)
                            print(users_in_db)
                        #TODO загнать в функцию, т.к. понадобится может при дальнейшем поиске
                        #поиск кандиатов и их фото, и выдача первого кандидата
                        candidates = vk_item_main.users_search(**query_info)
                        print('-->candidates - 3', candidates[:3])
                        kb = VkKeyboard(inline=True)
                        create_button(search_button_text, 'blue')
                        create_button('Следующий', 'white')
                        create_button('В избранное', 'green')
                        create_button('Список', 'green')
                        create_button(quit_button_text, 'red')
                        cand = iter(candidates)
                        # cand_data = next(cand)
                        next_candidate(cand)
                        flag = True
                        break

                    else:
                        send_msg(user_id, 'Некорректные данные')
        if flag == True:
            flag = False
            continue
        if request == 'Следующий':
            try:
                next_candidate(cand)
            except NameError:
                send_msg(user_id, "Нужно поискать. Нажмите 'Поиск'")
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
