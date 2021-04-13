import os
from pathlib import Path
from sqlalchemy import create_engine
import sqlite3

from src.data_preprocessing.monographs import parse_monographs, scrape_monographs
from src import Config


def monograph_to_db(engine, config: Config):
    monograph_config = config.get_monograph_config()

    scrape_monographs(monograph_config, Path(config['data_path']))
    monographs, monograph_date_points, government_statements = parse_monographs(monograph_config)
    monographs.to_sql(name='monographs', con=engine, if_exists='append',
                      index=False, index_label='id')
    monograph_date_points.to_sql(name='MonographDatePoints', con=engine, if_exists='append',
                                 index=False, index_label=None)
    government_statements.to_sql(name='GovernmentStatements', con=engine, if_exists='append',
                                 index=False, index_label='id')


if __name__ == '__main__':
    config = Config()

    con = sqlite3.connect(config['db_file'])
    cur = con.cursor()
    engine = create_engine(f"sqlite:///{config['db_file']}")

    with open('src/data_preprocessing/build_db_query.sql') as query_file:
        cur.executescript(query_file.read())

    os.makedirs(config['data_path'], exist_ok=True)
    monograph_to_db(engine, config)
