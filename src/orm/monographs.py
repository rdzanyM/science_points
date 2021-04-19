from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base
from .government_statements import GovernmentStatements


class Monographs(Base):
    __tablename__ = 'Monographs'

    id = Column(Integer, primary_key=True)
    publisher_name = Column(String)

    def __repr__(self):
        return f"Monographs(\"{self.id}\", \"{self.publisher_name}\")"


class MonographDatePoints(Base):
    __tablename__ = 'MonographDatePoints'

    monograph_id = Column(Integer, ForeignKey('Monographs.id'), primary_key=True)
    government_statement_id = Column(Integer, ForeignKey('GovernmentStatements.id'), primary_key=True)
    points = Column(Integer)


Monographs.monograph_date_points = relationship("MonographDatePoints",
                                                order_by=MonographDatePoints.government_statement_id,
                                                backref="Monographs")
GovernmentStatements.monograph_date_points = relationship("MonographDatePoints",
                                                          order_by=MonographDatePoints.monograph_id,
                                                          backref="GovernmentStatements")
