import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class BotUser(Base):
    __tablename__ = "botuser"

    user_vk_id = sq.Column(sq.Integer, primary_key=True)
    age_on = sq.Column(sq.Integer)
    age_to = sq.Column(sq.Integer)
    pol = sq.Column(sq.Integer)
    city = sq.Column(sq.String(length=40))


class Candidate(Base):
    __tablename__ = "candidate"

    vk_id = sq.Column(sq.Integer, primary_key=True)
    candidate_firstname = sq.Column(sq.String(length=40))
    candidate_lastname = sq.Column(sq.String(length=40))
    candidate_bdate = sq.Column(sq.String(length=40))
    candidate_fots = sq.Column(sq.String(length=100))



class Variants(Base):
    __tablename__ = "variants"

    id = sq.Column(sq.Integer, primary_key=True)
    id_botuser = sq.Column(sq.Integer, sq.ForeignKey("botuser.user_vk_id"), nullable=False, )
    id_candidate = sq.Column(sq.Integer, sq.ForeignKey("candidate.vk_id"), nullable=False, )
    loved = sq.Column(sq.BOOLEAN, default=False)
    viewed = sq.Column(sq.BOOLEAN, default=False)


    botuser = relationship(BotUser, backref="variants")
    candidate = relationship(Candidate, backref="variants")


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
