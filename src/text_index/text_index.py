import os
from typing import Iterable

from sqlalchemy.orm import Session
import whoosh
from whoosh import query
from whoosh.filedb.filestore import FileStorage
from whoosh.index import Index
from whoosh.qparser import QueryParser, OrGroup

from .. import Config
from .schema import *
from .. import orm


class IndexBuilder:
    def __init__(self, config: Config, session: Session):
        self.index_dir = config['text_index_path']
        self.session = session

    def build_index(self):
        os.makedirs(self.index_dir, exist_ok=True)
        storage = FileStorage(self.index_dir)
        index = storage.create_index(schema)

        result = dict()

        result['publisher'] = self.__add_documents(index, map(
            lambda r: {
                'id': str(r.id),
                'name': r.publisher_name,
                'type': EntryType.Publisher,
                # 'domains': 'test,kot'
            },
            self.session.query(orm.Monographs)
        ))

    @staticmethod
    def __add_documents(index: Index, docs: Iterable[dict]) -> int:
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

        return written


class IndexReader:
    def __init__(self, config: Config):
        self.index = whoosh.index.open_dir(config['text_index_path'])
        self.name_parser = QueryParser('name', schema, plugins=[], group=OrGroup)
        self.type_parser = QueryParser('type', schema, plugins=[])

    def query_monographs(self, text: str):
        return self.__query(
            query.Require(
                self.name_parser.parse(text),
                query.Term('type', EntryType.Publisher),
                # self.type_parser.parse(EntryType.Publisher),

            )
        )

    def __query(self, q: query.Query) -> [dict]:
        print(q)
        with self.index.searcher() as s:
            return [
                {
                    **hit.fields(),
                    'score': hit.score,
                }
                for hit in s.search(q)
            ]
