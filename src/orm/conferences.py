from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship

from .base import Base
from .government_statements import GovernmentStatements
from .domains import Domains


class Conferences(Base):
    __tablename__ = 'Conferences'

    id = Column(Integer, primary_key=True)
    title = Column(String)


class ConferenceDatePoints(Base):
    __tablename__ = 'ConferenceDatePoints'

    conference_id = Column(Integer, ForeignKey('Conferences.id'), primary_key=True)
    government_statement_id = Column(Integer, ForeignKey('GovernmentStatements.id'), primary_key=True)
    points = Column(Integer)


class ConferenceDomains(Base):
    __tablename__ = 'ConferenceDomains'

    conference_id = Column(Integer, ForeignKey('Conferences.id'), primary_key=True)
    domain_id = Column(Integer, ForeignKey('Domains.id'), primary_key=True)


Conferences.conference_date_points = relationship("ConferenceDatePoints",
                                                  order_by=ConferenceDatePoints.government_statement_id,
                                                  backref="Monographs")

GovernmentStatements.conference_date_points = relationship("ConferenceDatePoints",
                                                           order_by=ConferenceDatePoints.conference_id,
                                                           backref="GovernmentStatements")

Domains.conferences = relationship("ConferenceDomains",
                                   order_by=Conferences.id,
                                   backref="Domains")
