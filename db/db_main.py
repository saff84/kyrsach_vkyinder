import sqlalchemy
from sqlalchemy import and_, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from db.bd_tables import create_tables, BotUser, Candidate, Variants
import configparser

config_db = configparser.ConfigParser()
config_db.read("config.ini")
db_pass = config_db["DB_config"]["db_password"]
db_name = config_db["DB_config"]["db_name"]

DSN = f'postgresql://postgres:{db_pass}@localhost:5432/{db_name}'

engine = sqlalchemy.create_engine(DSN)

create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()


def add_botuser(query_info, user_id):
    botuser = BotUser(user_vk_id=user_id,
                      age_on=query_info['age_from'],
                      age_to=query_info['age_to'],
                      pol=query_info['sex'],
                      city=query_info['hometown']
                      )
    session.add(botuser)
    session.commit()


def add_candidates(candidates, user_id):
    for el in candidates:
        candidate = Candidate(vk_id=el['vk_id'],
                              candidate_firstname=el['first_name'],
                              candidate_lastname=el['last_name'],
                              candidate_bdate=el['bdate'],
                              candidate_fots=el['attach']
                              )
        session.add(candidate)
        session.commit()

        bu = session.query(
            BotUser.user_vk_id).filter(
            BotUser.user_vk_id == user_id).scalar()
        can = session.query(
            Candidate.vk_id).filter(
            Candidate.vk_id == el['vk_id']).scalar()

        variants = Variants(id_botuser=bu,
                            id_candidate=can
                            )
        session.add(variants)
        session.commit()


def get_search_parameters(user_id):
    botuser = session.query(BotUser).filter(
        BotUser.user_vk_id == user_id).scalar()

    return {'sex': botuser.pol,
            'age_from': botuser.age_on,
            'age_to': botuser.age_to,
            'hometown': botuser.city}


def get_users_in_db():
    list_vk_id_all_botuser = list(session.query(BotUser.user_vk_id))
    set_vk_id_all_botuser = set()
    for el in range(len(list_vk_id_all_botuser)):
        set_vk_id_all_botuser.add(list_vk_id_all_botuser[el][0])

    return set_vk_id_all_botuser


def get_all_id_candidates(user_id):
    list_all_candidates_for_botuser = list(
        session.query(
            Variants.id_candidate).filter(
            Variants.id_botuser == user_id))

    set_all_candidates_for_botuser = set()
    for el in range(len(list_all_candidates_for_botuser)):
        set_all_candidates_for_botuser.add(
            list_all_candidates_for_botuser[el][0])

    return set_all_candidates_for_botuser


def candidate_viewed(cand_id, user_id):
    session.query(Variants).filter(Variants.id_botuser == user_id,
                                   Variants.id_candidate == cand_id).update({'viewed': True})
    session.commit()


def update_botuser(query_info, user_id):
    """Сохраняет новые параметры запроса пользователя"""

    botuser = {'age_on': query_info['age_from'],
               'age_to': query_info['age_to'],
               'pol': query_info['sex'],
               'city': query_info['hometown']
               }
    session.query(BotUser).filter(
        BotUser.user_vk_id == user_id).update(botuser)
    session.commit()


def get_next_candidate(user_id):
    """Получает данные по кандидату, которого отдаем для просмотра юзеру"""

    cand = session.query(Candidate).join(Variants.candidate).filter(Variants.id_botuser == user_id).filter(
        Variants.viewed == False)[0]
    return {'vk_id': cand.vk_id,
            'first_name': cand.candidate_firstname,
            'last_name': cand.candidate_lastname,
            'bdate': cand.candidate_bdate,
            'attach': cand.candidate_fots
            }


def check_unviewed(user_id):
    """Проверяет, есть ли у пользователя непросмотренные кандидаты"""

    return session.query(exists().where(and_(
        Variants.id_botuser == user_id,
        Variants.viewed == False))).scalar()


def delete_unviewed(user_id):
    """Удаляет непросмотренных кандидатов (из неактуального поиска)"""

    subq = session.query(Variants.id_candidate, func.count(Variants.id_candidate)). \
        group_by(Variants.id_candidate). \
        having(func.count(Variants.id_candidate) < 2).subquery()

    result = session.query(Variants.id_candidate). \
        join(subq, Variants.id_candidate == subq.c.id_candidate). \
        filter(and_(
        Variants.id_botuser == user_id,
        Variants.viewed == False))
    unviewed_id = [el[0] for el in result]

    # удаляет всех непросмотренных у данного пользователя
    session.query(Variants).filter(and_(
        Variants.id_botuser == user_id,
        Variants.viewed == False)).delete()
    # удаляет всех непросмотренных из таблицы Candidate, если этих кандидатов
    # нет у других пользователей
    session.query(Candidate).filter(Candidate.vk_id.in_(unviewed_id)).delete()

    session.commit()


def candidate_to_favorite(user_id, vk_id):
    session.query(Variants).filter(and_(
        Variants.id_candidate == vk_id,
        Variants.id_botuser == user_id)).update({'loved': True})
    session.commit()


def get_favorites_list(user_id):
    res = session.query(Candidate).join(Variants.candidate).filter(and_(
        Variants.id_botuser == user_id),
        Variants.loved).all()
    favorites_list = ''.join([f"{el.candidate_firstname} {el.candidate_lastname}, "
                              f"{el.candidate_bdate}, https://vk.com/id{el.vk_id}\n" for el in res])
    return favorites_list


session.close()
