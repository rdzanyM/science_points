import os
import numpy as np
import pandas as pd
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
        c['title'] = c['title'].str.extract(
            '((^[^\[]*$)|(.*(?=\s\[)))')  # remove more additional data in titles (present in 2021 data)
        c['title'] = c['title'].str.extract(
            '((^.*[^\)\s]\s*$)|(.*(?=\([^\)]*\)\s?$)))')  # remove additional data in titles
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


def journal_to_db(engine, data_path):
    journals = pd.DataFrame(columns=['Tytuł 1', 'issn', 'e-issn', 'Tytuł 2', 'issn 2', 'e-issn 2', 'Punkty',
                                     'archeologia', 'filozofia', 'historia', 'językoznawstwo',
                                     'literaturoznawstwo', 'nauki o kulturze i religii', 'nauki o sztuce',
                                     'architektura i urbanistyka',
                                     'automatyka, elektronika i elektrotechnika',
                                     'informatyka techniczna i telekomunikacja', 'inżynieria biomedyczna',
                                     'inżynieria chemiczna', 'inżynieria lądowa i transport',
                                     'inżynieria materiałowa', 'inżynieria mechaniczna',
                                     'inżynieria środowiska, górnictwo i energetyka', 'nauki farmaceutyczne',
                                     'nauki medyczne', 'nauki o kulturze fizycznej', 'nauki o zdrowiu',
                                     'nauki leśne', 'rolnictwo i ogrodnictwo',
                                     'technologia żywności i żywienia', 'weterynaria',
                                     'zootechnika i rybactwo', 'ekonomia i finanse',
                                     'geografia społeczno-ekonomiczna i gospodarka przestrzenna',
                                     'nauki o bezpieczeństwie', 'nauki o komunikacji społecznej i mediach',
                                     'nauki o polityce i administracji', 'nauki o zarządzaniu i jakości',
                                     'nauki prawne', 'nauki socjologiczne', 'pedagogika', 'prawo kanoniczne',
                                     'psychologia', 'astronomia', 'informatyka', 'matematyka',
                                     'nauki biologiczne', 'nauki chemiczne', 'nauki fizyczne',
                                     'nauki o Ziemi i środowisku', 'nauki teologiczne', 'date'])

    for filename in os.listdir(data_path):
        j = pd.read_excel(os.path.join(data_path, filename), 0, header=0)
        j = j.iloc[:, 1:]
        j.columns = list(j.iloc[0, :5].values) + ['issn 2', 'e-issn 2', 'points'] + list(j.columns[8:])
        j = j.iloc[1:, 1:]
        j[j.columns[7:]] = np.where(j[j.columns[7:]].notna(), True, False)

        # removing 2nd issn/title/e-issn if same
        j.loc[(j['issn'] == j['issn 2']), 'issn 2'] = np.nan
        j.loc[(j['Tytuł 1'] == j['Tytuł 2']), 'Tytuł 2'] = np.nan
        j.loc[(j['e-issn'] == j['e-issn 2']), 'e-issn 2'] = np.nan

        # fill 1st title/issn/e-issn with 2nd if 1st not present
        j.loc[j['Tytuł 1'].isna(), 'Tytuł 1'] = j[j['Tytuł 1'].isna()]['Tytuł 2']
        j.loc[j['issn'].isna(), 'issn'] = j[j['issn'].isna()]['issn 2']
        j.loc[j['e-issn'].isna(), 'e-issn'] = j[j['e-issn'].isna()]['e-issn 2']

        j['date'] = filename[-15:-5]
        journals = journals.append(j)

    titles = pd.DataFrame(columns=['id', 'title'])
    titles['title'] = journals['Tytuł 1'].unique()
    titles['id'] = titles.index
    dates = titles.join(journals.set_index('Tytuł 1'), on='title', how='outer')[['id', 'date', 'points']]
    dates.columns = ['journal_id', 'starting_date', 'points']
    titles.to_sql(name='Journals', con=engine, if_exists='append', index=False, index_label='id')
    dates.to_sql(name='JournalDatePoints', con=engine, if_exists='append', index=False, index_label=None)


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
    journal_to_db(engine, './data/journals')
