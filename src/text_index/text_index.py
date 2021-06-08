import os
from typing import Iterable, Set, Tuple

import jellyfish
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
import whoosh
from whoosh.filedb.filestore import FileStorage
from whoosh.index import Index
from whoosh.qparser import QueryParser, OrGroup

from .. import Config
from .schema import *
from .. import orm


class IndexBuilder:
    def __init__(self, config: Config, session: Session):
        self.index_dir = config['search']['index_path']
        self.session = session

    def build_index(self):
        """
        Recreates and builds the text index for all types of entries.
        """
        # Monographs
        index = self.__create_index('monographs')
        self.__add_documents(index, map(
            lambda r: {
                'id': str(r.id),
                'name': r.publisher_name,
            },
            self.session.query(orm.Monographs)
        ))

        # Journals
        index = self.__create_index('journals')
        self.__add_documents(index, map(
            lambda r: {
                'id': str(r[0]),
                'name': r[1],
                'domains': r[2],
            },
            self.session.query(
                orm.Journals.id,
                orm.Journals.title,
                func.group_concat(orm.Domains.name, ',')
            ).
            select_from(orm.Journals).
            join(orm.JournalDomains).
            join(orm.Domains).
            group_by(orm.Journals.id)
        ))

        # Conferences
        index = self.__create_index('conferences')
        self.__add_documents(index, map(
            lambda r: {
                'id': str(r.id),
                'name': r.title,
            },
            self.session.query(orm.Conferences)
        ))

    def __create_index(self, i_type: str):
        index_dir = os.path.join(self.index_dir, i_type)
        os.makedirs(index_dir, exist_ok=True)
        storage = FileStorage(index_dir)
        return storage.create_index(schema)

    @staticmethod
    def __add_documents(index: Index, docs: Iterable[dict]):
        writer = index.writer()
        written = 0

        try:
            for doc in docs:
                writer.add_document(**doc)
                written += 1
            writer.commit()
        except BaseException:
            writer.cancel()
            print('Failed to index documents')
            raise


class IndexReader:
    def __init__(self, config: Config):
        self.index_m = whoosh.index.open_dir(
            os.path.join(config['search']['index_path'], 'monographs')
        )
        self.index_j = whoosh.index.open_dir(
            os.path.join(config['search']['index_path'], 'journals')
        )
        self.index_c = whoosh.index.open_dir(
            os.path.join(config['search']['index_path'], 'conferences')
        )
        self.matching_domains_boost = config['search']['matching_domains_boost']
        self.name_parser = QueryParser('name', schema, plugins=[], group=OrGroup)

    def query_monographs(self, text: str) -> pd.DataFrame:
        """
        :param text: publisher name to search for
        :return: DataFrame with results
        """
        return self.__query(self.index_m, text, set())

    def query_journals(self, text: str, domains: [str]) -> pd.DataFrame:
        """
        :param text: journal name to search for
        :param domains: list of domains the user is interested in, this will
        help boost relevant journals
        :return: DataFrame with results
        """
        return self.__query(self.index_j, text, set(domains))

    def query_conferences(self, text: str) -> pd.DataFrame:
        """
        :param text: conference name to search for
        :return: DataFrame with results
        """
        return self.__query(self.index_c, text, set())

    def __query(self, index: Index, text: str, domains: Set[str]) -> pd.DataFrame:
        q = self.name_parser.parse(text)

        with index.searcher() as s:
            results = []
            for hit in s.search(q, limit=6):
                ds = set((hit.get('domains') or '').split(','))
                results.append({
                    'raw_score': hit.score,
                    'id': hit['id'],
                    'name': hit['name'],
                    'domains_boost': self.matching_domains_boost if len(ds & domains) > 0 else 1
                })

        if len(results) == 0:
            return pd.DataFrame()

        df = pd.DataFrame.from_records(results, index='id')

        # Compute accurate score based on string similarity (lowercased)
        df['score'] = df['name'].apply(
            # "Sharpen" the similarity to make it more intuitive
            lambda name: jellyfish.jaro_winkler_similarity(name.lower(), text.lower()) ** 1.5
        )

        df['score'] = df['score'] * df['domains_boost'] / self.matching_domains_boost
        df = df.sort_values(by='score', ascending=False)
        return df.reset_index(drop=True)
