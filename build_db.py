import os
from pathlib import Path
from sqlalchemy import create_engine
import sqlite3

from src.data_preprocessing.monographs import parse_monographs, scrape_monographs, urls, dates, titles


def monograph_to_db(engine, data_path):
    paths = scrape_monographs(urls, data_path)
    monographs, monograph_date_points, government_statements = parse_monographs(urls, paths, dates, titles)
    monographs.to_sql(name='monographs', con=engine, if_exists='append',
                      index=False, index_label='id')
    monograph_date_points.to_sql(name='MonographDatePoints', con=engine, if_exists='append',
                                 index=False, index_label=None)
    government_statements.to_sql(name='GovernmentStatements', con=engine, if_exists='append',
                                 index=False, index_label='id')


if __name__ == '__main__':
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    engine = create_engine('sqlite:///database.db')

    with open('src/data_preprocessing/build_db_query.sql') as query_file:
        cur.executescript(query_file.read())

    data_path = Path('./data')
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    monograph_to_db(engine, data_path)
