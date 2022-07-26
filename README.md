# kyrsach_vkyinder


### Перед запуском 
 В корне проекта нужно заполнить config.ini для запуска проекта


### Цель проекта
Создать программу-бота для помощи поиска пары в VK используя взаимодействие с API VK.

### Сделано:

1. Спроектирована и реализована база данных для программы
2. Создано сообщество vk для бота, необходимо написать в сообщество для запуска
3. Разработана программа-бота на Python использующая алгоритм:
- При первом сообщении, используя данные пользователя, бот отправляет приветственное сообщение с предложением осуществить поиск.
- При поступлении данных от пользователя с параметрами поиска (пол, возраст от, возраст до, город) производится поиск пользователей vk, подходящих для знакомства.
- У подошедших пользователей vk бот получает три популярные (по количеству лайков) фотографии на стене/профиле.
- Бот выводит в чат информацию о пользователе в формате: Имя Фамилия, дата рождения, ссылка на vk-профиль, фото.
- Реализовано меню "Поиск", "Следующий", "В Избранное", "Список" (список избранных), "Выйти" .
- Загрузка пользователей осуществляется блоками по N человек с записью в базу данных. Когда все кандидаты в БД просмотрены, осуществляется запрос к API VK на загрузку следующих N пользователей. 


### Техническое описание проекта

#### vkt_bot_main.py

Управляющий файл работы логики бота


#### vkt_bot_candidates.py

Запрашивает данные по параметрам поиска и определяет популярные фотографии пользователя


#### config.ini

Файл для токенов и доступов и запуску БД


#### Пакет db

#### db/bd_tables.py

Описывает таблицы их взаимосвязи и запуск на создание

#### db/db_main

Управляющий файл со всеми функциями по работе с БД

#### Структура БД

![Структура БД](https://github.com/saff84/kyrsach_vkyinder/blob/master/db/db_schema.jpg)