import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class BotUser(Base):
    __tablename__ = "botuser"

    id = sq.Column(sq.Integer, primary_key=True)
    user_vk_id = sq.Column(sq.Integer)
    age_on = sq.Column(sq.Integer)
    age_to = sq.Column(sq.Integer)
    pol = sq.Column(sq.Integer)
    city = sq.Column(sq.String(length=40))


class Candidate(Base):
    __tablename__ = "candidate"

    id = sq.Column(sq.Integer, primary_key=True)
    candidate_lastname = sq.Column(sq.String(length=40))
    vk_id = sq.Column(sq.Integer)
    candidate_bdate = sq.Column(sq.String(length=40))
    candidate_firstname = sq.Column(sq.String(length=40))
    candidate_fots = sq.Column(sq.String(length=240))
    viewed = sq.Column(sq.String(length=6))  # Просмотренно True/False




class Variants(Base):
    __tablename__ = "variants"

    id = sq.Column(sq.Integer, primary_key=True)
    id_botuser = sq.Column(sq.Integer, sq.ForeignKey("botuser.id"), nullable=False, )
    id_candidate = sq.Column(sq.Integer, sq.ForeignKey("candidate.id"), nullable=False, )
    loved = sq.Column(sq.String(length=6))# Избранное True/False

    botuser = relationship(BotUser, backref="botuser")
    candidate = relationship(Candidate, backref="candidate")


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
