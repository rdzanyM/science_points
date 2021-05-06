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
        markdown_value+=f'\n{i}. {search_result.name.iloc[i]}'
    return markdown_value

def format_colors_based_on_similarity():
    scale = cl.scales['5']['div']['RdYlGn']
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
            'color': 'black'
        },

        {
            'if': {
                'column_id': 'Similarity',

                'filter_query': '{Similarity} >= 0.7 && {Similarity} < 0.8'
            },
            'backgroundColor': scale[2],
            'color': 'black'
        },
        
        {
            'if': {
                'column_id': 'Similarity',

                'filter_query': '{Similarity} >= 0.6 && {Similarity} < 0.7'
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
            'color': 'white'
        },
    ]