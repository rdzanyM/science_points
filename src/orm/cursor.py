from src.orm.conferences import ConferenceDomains
from src.orm.journals import JournalDomains
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.orm import Conferences, Journals, Monographs, JournalDatePoints, ConferenceDatePoints, \
    MonographDatePoints, GovernmentStatements, Domains


class Cursor:

    def __init__(self, engine):
        self.engine = engine

    def __enter__(self):
        self.session = Session(self.engine)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get_conference_date_points(self, title):
        conferences = self.session.query(Conferences) \
            .where(Conferences.title == title) \
            .join(ConferenceDatePoints) \
            .join(GovernmentStatements).all()
        conference = conferences[0]
        point_dates = [(i.GovernmentStatements.title,
                        str(i.GovernmentStatements.starting_date),
                        i.points) for i in conference.conference_date_points]
        return point_dates

    def get_monograph_date_points(self, publisher_name):
        monographs = self.session.query(Monographs) \
            .where(Monographs.publisher_name == publisher_name) \
            .join(MonographDatePoints) \
            .join(GovernmentStatements).all()
        monograph = monographs[0]
        point_dates = [(i.GovernmentStatements.title,
                        str(i.GovernmentStatements.starting_date),
                        i.points) for i in monograph.monograph_date_points]
        return point_dates

    def get_journal_date_points(self, title):
        journals = self.session.query(Journals) \
            .where(Journals.title == title) \
            .join(JournalDatePoints) \
            .join(GovernmentStatements).all()
        journal = journals[0]
        point_dates = [(i.GovernmentStatements.title,
                        str(i.GovernmentStatements.starting_date),
                        i.points) for i in journal.journal_date_points]
        return point_dates

    def get_date_points(self, title, publication_type):
        if publication_type == 'czasopisma':
            result = self.get_journal_date_points(title)
        elif publication_type == 'konferencje':
            result = self.get_conference_date_points(title)
        elif publication_type == 'monografie':
            result = self.get_monograph_date_points(title)
        else:
            raise RuntimeError(f'Unknown publication type: {publication_type}')
        result.sort(key=lambda x: x[1])
        return result

    def get_domains(self) -> List[str]:
        return [d.name for d in self.session.query(Domains.name).order_by(Domains.name)]

    def get_journal_domains(self, title):
        domains = self.session.query(Domains) \
            .join(JournalDomains) \
            .join(Journals) \
            .where(Journals.title == title).all()
        return [d.name for d in domains]

    def get_conference_domains(self, title):
        domains = self.session.query(Domains) \
            .join(ConferenceDomains) \
            .join(Conferences) \
            .where(Conferences.title == title).all()
        return [d.name for d in domains]

