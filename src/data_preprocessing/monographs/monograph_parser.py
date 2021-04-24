import pandas as pd
import re
import tabula
from sklearn.preprocessing import LabelEncoder
from typing import List

from src import MonographConfigEntry


def monograph_parser_strategy_1(table):
    """
        Assumes format
        __________________________________________________________________
        |    POZIOM X - Y punktów                                        |
        |--------+-----------------------------------+-------------------|
        |Lp.     |Unikatowy Identyfikator Wydawnictwa|       Wydawnictwo |
        |1       |id1                                |       wyd_1       |
        |2       |id2                                |       wyd_2       |
        |...     |  ...                              |       ...         |
        |--------+-----------------------------------+-------------------|
        |    POZIOM X - Y punktów                                        |
        |--------+-----------------------------------+-------------------|
        |Lp.     |Unikatowy Identyfikator Wydawnictwa|       Wydawnictwo |
        |1       |id1                                |       wyd_1       |
        |2       |id2                                |       wyd_2       |
        |...     |  ...                              |       ...         |
        |----------------------------------------------------------------|

        :param table: table read from pdf
        :return: pandas.DataFrame with columns 'publisher' and 'points' (points equal to Y)
    """
    level_rows = table[pd.isnull(table[1])]
    points = level_rows[0].apply(lambda x: int(re.search(r'\d+', x).group()))
    idx = list(points.index) + [len(table)]
    table['points'] = 0
    for i, _ in enumerate(idx[:-1]):
        table.loc[(table.index >= idx[i]) & (table.index < idx[i + 1]), 'points'] = points[idx[i]]

    # Drop POZIOM/uid columns and lp rows
    table = table[(table[0] != 'Lp.') & (~pd.isnull(table[1]))].drop(columns=[0, 1]).reset_index(drop=True)
    table.columns = ['publisher_name', 'points']
    return table


def monograph_parser_strategy_2(table):
    """
        Assumes format
        ______________________________
        |    POZIOM X - Y punktów    |
        |--------+-------------------|
        |Lp.     |       Wydawnictwo |
        |1       |       wyd_1       |
        |2       |       wyd_2       |
        |...     |       ...         |
        |--------+-------------------|
        |    POZIOM X - Y punktów    |
        |--------+-------------------|
        |Lp.     |      Wydawnictwo  |
        |1       |      wyd_1        |
        |2       |      wyd_2        |
        |...     |       ...         |
        |----------------------------|

        :param table: table read from pdf
        :param date: date of the document
        :return: pandas.DataFrame with columns 'publisher' and 'points' (points equal to Y)
    """
    level_rows = table[pd.isnull(table[1])]
    points = level_rows[0].apply(lambda x: int(re.search(r'\d+', x).group()))
    idx = list(points.index) + [len(table)]
    table['points'] = 0
    for i, _ in enumerate(idx[:-1]):
        table.loc[(table.index >= idx[i]) & (table.index < idx[i + 1]), 'points'] = points[idx[i]]

    # Drop POZIOM and lp rows
    table = table[(table[0] != 'Lp.') & (~pd.isnull(table[1]))].drop(columns=0).reset_index(drop=True)
    table.columns = ['publisher_name', 'points']
    return table


def parse_monographs(monograph_config: List[MonographConfigEntry]):
    """
    Parse tables with monographs.
    At the moment we don't merge with publisher_info to get DOI (no common column - names are different).
    :param monograph_config:
    :return: 3 tables ready for db insertion: monograph,
    MonographDatePoints, GovernmentStatements
    """
    results = []
    monograph_encoder = LabelEncoder()
    government_document_encoder = LabelEncoder()
    for m in monograph_config:
        table = tabula.read_pdf(m.path, pages='all',
                                multiple_tables=True,
                                pandas_options={'header': None},
                                lattice=True)
        table = pd.concat(table).reset_index(drop=True)
        if len(table.columns) == 3:
            result = monograph_parser_strategy_1(table)
        elif len(table.columns) == 2:
            result = monograph_parser_strategy_2(table)
        else:
            # Add different parser strategies
            raise NotImplementedError()
        result['starting_date'] = m.date
        result['title'] = m.title
        result['url'] = m.url
        results.append(result)
    results = pd.concat(results)
    results['monograph_id'] = monograph_encoder.fit_transform(results['publisher_name'])
    results['government_statement_id'] = government_document_encoder.fit_transform(results['title'])
    monographs = results[['monograph_id', 'publisher_name']]\
        .rename(columns={'monograph_id': 'id'}).drop_duplicates('id').sort_values('id')
    monograph_date_points = results[['monograph_id', 'government_statement_id', 'points']]
    government_statements = results[['government_statement_id', 'url', 'title', 'starting_date']]\
        .rename(columns={'government_statement_id': 'id'}).drop_duplicates('id').sort_values('id')
    government_statements['starting_date'] = pd.to_datetime(government_statements['starting_date'])
    return monographs, monograph_date_points, government_statements
