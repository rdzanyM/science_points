from sqlalchemy import Column, Integer, String, Date

from .base import Base


class Domains(Base):
    __tablename__ = 'Domains'

    id = Column(Integer, primary_key=True)
    name = Column(String)
