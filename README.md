# kyrsach_vkyinder


### Перед запуском 
 В корне проекта нужно заполнить config.ini для запуска проекта


### Цель проекта
Создать программу-бота для помощи поиска пары в VK используя взаимодействие с API VK.

###Сделано:

- Спроектирована и реализована база данных для программы
- Создано сообщество vk https://vk.com/club214720213 для бота, необходимо написать в сообщество для запуска
- Разработана программа-бота на Python использующая алгоритм:
- При первом сообщении используя данные пользователя отправляет привтественное сообщение в чат с предложением для поиска пар
- При поступлении данных от пользователя с параметрами поиска (пол, возраст от, возраст до, город) производится поиск пользователей vk подходящих для знакомства.
- У подошедших пользователей vk, получает три популярные фотографии в альбоме/профиле (популярность определяется по количеству лайков).
- Бот выводит в чат информацию о пользователе в формате: ФИО, дата рождеиня,ссылка, Фото
- Реализовано меню "Следующий", "В Избранное", "Список" (список избранных), "Выход" .
- Загрузка пользователей осуществляется блоками по N человек с записью в базу данных, когда все кандидаты в БД просмотрены, осуществляется запрос к API VK на загрузку следующих N пользователей. 


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