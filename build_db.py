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


def conference_to_db(engine, data_path):
    conferences = pd.DataFrame(columns=['title', 'points', 'date'])
    for filename in os.listdir(data_path):
        c = pd.read_excel(os.path.join(data_path, filename), 1, header=0)
        c = c.iloc[:, 1:3]
        c.columns = ['title', 'points']
        c['title'] = c['title'].str.extract('((^[^\[]*$)|(.*(?=\s\[)))')  # remove more additional data in titles (present in 2021 data)
        c['title'] = c['title'].str.extract('((^.*[^\)\s]\s*$)|(.*(?=\([^\)]*\)\s?$)))')  # remove additional data in titles
        c['title'] = c['title'].str.extract('(.*[^\s](?=\s*$))')  # remove trailing spaces
        c['date'] = filename[-15:-5]
        conferences = conferences.append(c)
    titles = pd.DataFrame(columns=['id', 'title'])
    titles['title'] = conferences['title'].unique()
    titles['id'] = titles.index
    dates = titles.join(conferences.set_index('title'), on='title', how='outer')[['id', 'date', 'points']]
    dates.columns = ['conference_id', 'starting_date', 'points']
    titles.to_sql(name='Conferences', con=engine, if_exists='append', index=False, index_label='id')
    dates.to_sql(name='ConferenceDatePoints', con=engine, if_exists='append', index=False, index_label=None)


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
    conference_to_db(engine, './data/journals')