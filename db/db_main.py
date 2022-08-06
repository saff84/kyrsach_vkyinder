import sqlalchemy
from sqlalchemy.orm import sessionmaker
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
    # for el in query_info:
    botuser = BotUser(user_vk_id=user_id,
                      age_on=query_info['age_from'],
                      age_to=query_info['age_to'],
                      pol=query_info['sex'],
                      city=query_info['hometown']
                      )
    session.add(botuser)
    session.commit()


def update_botuser(query_info, user_id):
    botuser = {'age_on': query_info['age_from'],
               'age_to': query_info['age_to'],
               'pol': query_info['sex'],
               'city': query_info['hometown']
               }
    session.query(BotUser).filter(
        BotUser.user_vk_id == user_id).update(botuser)
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


def get_next_candidate(user_id):
    # cand = session.query(Candidate).join(Variants.candidate).filter(Variants.id_botuser == user_id).filter(
    #         Variants.viewed == False)[0]
    cand = session.query(Candidate).join(Variants.candidate).filter(Variants.id_botuser == user_id).filter(
        Variants.viewed == False)[0]
    return {'vk_id': cand.vk_id,
            'first_name': cand.candidate_firstname,
            'last_name': cand.candidate_lastname,
            'bdate': cand.candidate_bdate,
            'attach': cand.candidate_fots
            }


def get_search_parametrs(user_id):

    botuser = session.query(BotUser).filter(BotUser.user_vk_id == user_id)

    if botuser:
        return {'sex': botuser.pol,
            'age_from': botuser.age_on,
            'age_to': botuser.age_to,
            'hometown': botuser.city}
    else:
        pass

def get_users_in_db():

    list_vk_id_all_botuser = list(session.query(BotUser.user_vk_id))
    set_vk_id_all_botuser  = set()
    for el in range(len(list_vk_id_all_botuser)):
        set_vk_id_all_botuser.add(list_vk_id_all_botuser[el][0])

    return set_vk_id_all_botuser


def get_all_id_candidates(user_id):

    return set(session.query(Candidate.id).join(Variants).join(BotUser).filter(BotUser.user_vk_id == user_id))

def candidate_viewed(cand_id, user_id):
    session.query(Variants).filter(Variants.id_botuser == user_id, Variants.id_candidate == cand_id).update({'viewed': True})
    session.commit()




session.close()
