import sqlalchemy
from sqlalchemy.orm import sessionmaker
from db import bd_tables
import configparser

config_db = configparser.ConfigParser()
config_db.read("config.ini")
db_pass = config_db["DB_config"]["db_password"]
db_name = config_db["DB_config"]["db_name"]

DSN = f'postgresql://postgres:{db_pass}@localhost:5432/{db_name}'

engine = sqlalchemy.create_engine(DSN)


bd_tables.create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()


def add_botuser(query_info, user_id):
    # for el in query_info:
    botuser = bd_tables.BotUser(user_vk_id=user_id,

                                age_on=query_info['age_from'],
                                age_to=query_info['age_to'],
                                pol=query_info['sex'],
                                city=query_info['hometown']
                                )
    session.add(botuser)
    session.commit()


def add_candidates(candidates, user_id):
    for el in candidates:
        candidate = bd_tables.Candidate(vk_id=el['vk_id'],
                                        candidate_firstname=el['first_name'],
                                        candidate_lastname=el['last_name'],
                                        candidate_bdate=el['bdate'],
                                        candidate_fots=el['attach'],
                                        viewed='False'
                                        )
        session.add(candidate)
        session.commit()

        bu = session.query(bd_tables.BotUser.id).filter(bd_tables.BotUser.user_vk_id == user_id).scalar()
        can = session.query(bd_tables.Candidate.id).filter(bd_tables.Candidate.vk_id == el['vk_id']).scalar()

        variants = bd_tables.Variants(id_botuser=bu,
                                      id_candidate=can,
                                      loved='False'
                                      )
        session.add(variants)
        session.commit()


# add_botuser(query_info,user_name)
# add_candidates(candidates,user_id)


session.close()
