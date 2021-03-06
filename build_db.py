import os
import numpy as np
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
import sqlite3

from sqlalchemy.orm import sessionmaker

from src.data_preprocessing.monographs import parse_monographs, scrape_monographs
from src.orm import Base
from src import Config
from src.text_index import IndexBuilder


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


def conference_to_db(engine, config: Config):
    data_path = config['data_path'] + '/journals'
    conferences = pd.DataFrame(columns=['title', 'points', 'government_statement_id'])
    gov = pd.DataFrame(config['journals']).reset_index()
    government_statements = pd.DataFrame(columns=['id', 'url', 'title', 'starting_date'])
    government_statements['id'] = gov['index'] + len(config['monographs'])
    government_statements['url'] = gov['url']
    government_statements['title'] = gov['title']
    government_statements['starting_date'] = pd.to_datetime(gov['date'])
    government_statements.to_sql(name='GovernmentStatements', con=engine, if_exists='append', index=False, index_label='id')
    for filename in os.listdir(data_path):
        if int(filename[-9:-5]) > 2017:
            c = pd.read_excel(os.path.join(data_path, filename), 1, header=0)
            c = c.iloc[:, 1:3]
            c.columns = ['title', 'points']
            c['title'] = c['title'].str.extract(
                '((^[^\[]*$)|(.*(?=\s\[)))')  # remove more additional data in titles (present in 2021 data)
            c['title'] = c['title'].str.extract(
                '((^.*[^\)\s]\s*$)|(.*(?=\([^\)]*\)\s?$)))')  # remove additional data in titles
            c['title'] = c['title'].str.extract('(.*[^\s](?=\s*$))')  # remove trailing spaces
            c['government_statement_id'] = government_statements[government_statements['starting_date'] == filename[-15:-5].replace('-','.')]['id'].values[0]
            conferences = conferences.append(c)
    titles = pd.DataFrame(columns=['id', 'title'])
    titles['title'] = conferences['title'].unique()
    titles['id'] = titles.index
    dates = titles.join(conferences.set_index('title'), on='title', how='outer')[['id', 'government_statement_id', 'points']]
    dates.columns = ['conference_id', 'government_statement_id', 'points']
    dates = dates.sort_values('points').drop_duplicates(subset=['conference_id', 'government_statement_id'], keep='last')
    titles.to_sql(name='Conferences', con=engine, if_exists='append', index=False, index_label='id')
    dates.drop_duplicates(inplace=True)
    dates.to_sql(name='ConferenceDatePoints', con=engine, if_exists='append', index=False, index_label=None)
    c_domains = pd.DataFrame(columns=['conference_id', 'domain_id'])
    c_domains['conference_id'] = np.tile(titles['id'], 2)
    c_domains['domain_id'] = np.repeat([9,37], len(titles['id']))
    c_domains.to_sql(name='ConferenceDomains', con=engine, if_exists='append', index=False, index_label=None)

def journal_to_db(engine, config: Config):
    journals = None
    data_path = config['data_path'] + '/journals'
    gov = pd.DataFrame(config['journals']).reset_index()
    government_statements = pd.DataFrame(columns=['id', 'url', 'title', 'starting_date'])
    government_statements['id'] = gov['index'] + len(config['monographs'])
    government_statements['url'] = gov['url']
    government_statements['title'] = gov['title']
    government_statements['starting_date'] = pd.to_datetime(gov['date'])
    for filename in os.listdir(data_path):
        if int(filename[-9:-5]) > 2017:
            j = pd.read_excel(os.path.join(data_path, filename), 0, header=0)
            j = j.iloc[:, 1:]
            j.columns = list(j.iloc[0, :5].values) + ['issn 2', 'e-issn 2', 'points'] + list(j.columns[8:])
            j = j.iloc[1:, 1:]
            j[j.columns[7:]] = np.where(j[j.columns[7:]].notna(), True, False)

            # removing 2nd issn/title/e-issn if same
            j.loc[(j['issn'] == j['issn 2']), 'issn 2'] = np.nan
            j.loc[(j['Tytu?? 1'] == j['Tytu?? 2']), 'Tytu?? 2'] = np.nan
            j.loc[(j['e-issn'] == j['e-issn 2']), 'e-issn 2'] = np.nan

            # fill 1st title/issn/e-issn with 2nd if 1st not present
            j.loc[j['Tytu?? 1'].isna(), 'Tytu?? 1'] = j[j['Tytu?? 1'].isna()]['Tytu?? 2']
            j.loc[j['issn'].isna(), 'issn'] = j[j['issn'].isna()]['issn 2']
            j.loc[j['e-issn'].isna(), 'e-issn'] = j[j['e-issn'].isna()]['e-issn 2']

            j['government_statement_id'] = government_statements[government_statements['starting_date'] == filename[-15:-5].replace('-','.')]['id'].values[0]
            if journals is None:
                journals = j
            else:
                journals = journals.append(j)
    for filename in os.listdir(data_path):
        if int(filename[-9:-5]) < 2018:
            j = pd.read_excel(os.path.join(data_path, filename), 0, header=0)
            j = j.iloc[:, 1:]
            j.columns = list(j.iloc[0, :5].values) + ['issn 2', 'e-issn 2', 'points'] + list(j.columns[8:])
            j = j.iloc[1:, 1:]
            j[j.columns[7:]] = np.where(j[j.columns[7:]].notna(), True, False)

            j['government_statement_id'] = government_statements[government_statements['starting_date'] == filename[-15:-5].replace('-','.')]['id'].values[0]
            journals = journals.append(j)

    
    titles = pd.DataFrame(columns=['id', 'title'])
    journals['Tytu?? 1'] = journals['Tytu?? 1'].replace('\n', ' ', regex=True).replace('\r', '', regex=True)
    titles['title'] = journals['Tytu?? 1'].unique()
    titles['id'] = titles.index
    joined = titles.join(journals.set_index('Tytu?? 1'), on='title', how='outer')
    dates = joined[['id', 'government_statement_id', 'points']]
    dates.columns = ['journal_id', 'government_statement_id', 'points']
    dates = dates.sort_values('points').drop_duplicates(subset=['journal_id', 'government_statement_id'], keep='last')
    titles.to_sql(name='Journals', con=engine, if_exists='append', index=False, index_label='id')
    # drop duplicates
    dates = dates.groupby(['journal_id', 'government_statement_id'])['points'].max().reset_index()
    dates.to_sql(name='JournalDatePoints', con=engine, if_exists='append', index=False, index_label=None)
    domains = pd.DataFrame(columns=['id', 'name'])
    domains['name'] = journals.columns[7:-2]
    domains['id'] = domains.index
    domains.to_sql(name='Domains', con=engine, if_exists='append', index=False, index_label=None)
    domain_matrix = joined.drop_duplicates(['id']).sort_values(by=['id']).iloc[:, 8:-2].values
    j_domains = pd.DataFrame(np.argwhere(domain_matrix), columns=['journal_id', 'domain_id'])
    j_domains.to_sql(name='JournalDomains', con=engine, if_exists='append', index=False, index_label=None)


if __name__ == '__main__':
    config = Config()

    con = sqlite3.connect(config['db_file'])
    cur = con.cursor()
    engine = create_engine(f"sqlite:///{config['db_file']}")

    with open('src/data_preprocessing/drop_all_tables.sql') as query_file:
        cur.executescript(query_file.read())

    Base.metadata.create_all(engine)

    os.makedirs(config['data_path'], exist_ok=True)
    monograph_to_db(engine, config)
    journal_to_db(engine, config)
    conference_to_db(engine, config)

    # Build the text index
    Session = sessionmaker(bind=engine)
    index_builder = IndexBuilder(config, Session())
    index_builder.build_index()
