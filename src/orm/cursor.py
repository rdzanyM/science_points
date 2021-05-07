from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.orm import Conferences, Journals, Monographs, JournalDatePoints, ConferenceDatePoints,\
    MonographDatePoints, GovernmentStatements


class Cursor:
    def __init__(self, config):
        engine = create_engine(f"sqlite:///{config['db_file']}")
        self.session = Session(engine)

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
