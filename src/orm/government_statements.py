from sqlalchemy import Column, Integer, String, Date

from .base import Base


class GovernmentStatements(Base):
    __tablename__ = 'GovernmentStatements'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    title = Column(String)
    starting_date = Column(Date)
