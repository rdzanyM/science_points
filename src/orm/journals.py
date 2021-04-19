from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship

from .base import Base
from .government_statements import GovernmentStatements
from .domains import Domains


class Journals(Base):
    __tablename__ = 'Journals'

    id = Column(Integer, primary_key=True)
    title = Column(String)


class JournalDatePoints(Base):
    __tablename__ = 'JournalDatePoints'

    journal_id = Column(Integer, ForeignKey('Journals.id'), primary_key=True)
    government_statement_id = Column(Integer, ForeignKey('GovernmentStatements.id'), primary_key=True)
    points = Column(Integer)


class JournalDomains(Base):
    __tablename__ = 'JournalDomains'

    journal_id = Column(Integer, ForeignKey('Journals.id'), primary_key=True)
    domain_id = Column(Integer, ForeignKey('Domains.id'), primary_key=True)


Journals.journal_date_points = relationship("JournalDatePoints",
                                            order_by=JournalDatePoints.government_statement_id,
                                            backref="Monographs")

GovernmentStatements.journal_date_points = relationship("JournalDatePoints",
                                                        order_by=JournalDatePoints.journal_id,
                                                        backref="GovernmentStatements")

Domains.journals = relationship("JournalDomains",
                                order_by=Journals.id,
                                backref="Domains")
