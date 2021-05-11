from typing import List

import dash_html_components as html
import colorlover as cl
import pandas as pd


def format_suggestions_based_on_search(searched_term: str, search_result: pd.DataFrame) -> str:
    if len(search_result) == 0:
        return f'Szukano: *{searched_term}*, nie znaleziono żadnych wyników.'

    if len(search_result) == 1:
        return f'Szukano: *{searched_term}*, znaleziono tylko powyższy wynik.'

    markdown_value = f'Szukano: *{searched_term}*.\n\n Inne sugestie:'
    for i in range(1, min(len(search_result), 3)):
        markdown_value += f'\n{i}. {search_result.name.iloc[i]}'
    return markdown_value


def format_colors_based_on_similarity():
    scale = cl.scales['5']['seq']['PuBu']
    return [
        {
            'if': {
                'column_id': 'Similarity',
                'filter_query': '{Similarity} >= 0.9'
            },
            'backgroundColor': scale[4],
            'color': 'white'
        },
        {
            'if': {
                'column_id': 'Similarity',

                'filter_query': '{Similarity} >= 0.8 && {Similarity} < 0.9'
            },
            'backgroundColor': scale[3],
            'color': 'white'
        },

        {
            'if': {
                'column_id': 'Similarity',

                'filter_query': '{Similarity} >= 0.65 && {Similarity} < 0.8'
            },
            'backgroundColor': scale[2],
            'color': 'black'
        },

        {
            'if': {
                'column_id': 'Similarity',

                'filter_query': '{Similarity} >= 0.5 && {Similarity} < 0.65'
            },
            'backgroundColor': scale[1],
            'color': 'black'
        },

        {
            'if': {
                'column_id': 'Similarity',

                'filter_query': '{Similarity} < 0.5'
            },
            'backgroundColor': scale[0],
            'color': 'black'
        },
    ]


def row_col(
        column_contents: list,
        column_widths: List[int],
        column_styles: List[dict] = None,
        row_extra_classes: str = '',
        row_style: dict = None,
):
    column_styles = column_styles or [dict()] * len(column_contents)
    return html.Div(
        className=f'row {row_extra_classes}',
        style=row_style or dict(),
        children=[
            html.Div(
                className=f'col-{width}',
                style=style,
                children=content,
            )
            for content, width, style in zip(column_contents, column_widths, column_styles)
        ]
    )
