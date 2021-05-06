# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from functools import partial

import dash
from dash.dependencies import Input, Output, State
import dash_table
from dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
import dash_html_components as html
from sqlalchemy import create_engine

from src import Config
from src.text_index import IndexReader
from src.app_utils import format_colors_based_on_similarity 
from src.app_utils import format_suggestions_based_on_search
from src.orm import Cursor

config = Config()
ir = IndexReader(config)


def get_domain_form_group() -> dbc.FormGroup:
    return dbc.FormGroup(
        [
            dbc.Label("Wybierz dziedziny"),
            dbc.Checklist(
                options=[
                    {"label": "Matematyka", "value": 'matematyka'},
                    {"label": "Informatyka", "value": 'informatyka'},
                ],
                value=['matematyka', 'informatyka'],
                id="domain-input",
                inline=True
            ),
        ]
    )


def get_publication_type_form_group() -> dbc.FormGroup:
    return dbc.FormGroup(
        [
            dbc.Label("Wybierz rodzaj publikacji"),
            dbc.RadioItems(
                options=[
                    {"label": "czasopisma", "value": 'czasopisma'},
                    {"label": "konferencje", "value": 'konferencje'},
                    {"label": "monografie", "value": 'monografie'},
                ],
                value='czasopisma',
                id="publication-type-input",
                inline=True
            ),
        ]
    )


def get_search_table() -> html.Div:
    table = html.Div([
        dash_table.DataTable(

            id='search-table',

            columns=(
                [{'id': 'Title', 'name': 'Tytuł', 'type': 'text', }] +
                [{'id': 'Date', 'name': 'Data', 'type': 'datetime', }]
            ),

            data=[
                {'Title': 'IEEE Transactions on Pattern Analysis and Machine Intelligence', 'Date': '2020'},
                {'Title': 'IEEE Intelligent Systems', 'Date': '2018'},
                {'Title': 'Foundations and Trends in Machine Learning',
                    'Date': '2019-12-20'},
                {'Title': 'Science Robotics', 'Date': '2020-01-20'},
            ],

            tooltip={
                'Title': {
                    'value': 'Wpisz pełny lub częściowy tytuł.',
                    'use_with': 'both',
                    'delay': 500
                },

                'Date': {
                    'value': 'YYYY lub YYYY-MM-DD',
                    'use_with': 'both',
                    'delay': 500
                }
            },

            style_as_list_view=False,

            style_cell={'padding': '5px'},

            style_header={
                'backgroundColor': 'white',
                'fontWeight': 'bold',
                'textAlign': 'left',
            },
        
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Date'},
                    'width': '140px',
                },
            ],
            
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
                'lineHeight': '15px'
            },

            editable=True,
            row_deletable=True,
            page_action='none',
            export_format='csv',
            export_headers='display',
        ),
        dbc.Button(
            'Dodaj wiersz',
            id='button-add-row',
            className='btn-success',
        ),
    ]
    )
    return table


def get_results_table() -> html.Div:
    table = html.Div([
        dash_table.DataTable(
            id='results-table',
            columns=[
                {'id': 'Title', 'name': 'Tytuł', 'type': 'text', },
                {'id': 'Date', 'name': 'Data', 'type': 'datetime', },
                {'id': 'Points', 'name': 'Punktacja', 'type': 'numeric', },
                {'id': 'Similarity', 
                 'name': 'Zgodność z wyszukaniem', 
                 'type': 'numeric', 
                 'format': Format(precision=4, scheme=Scheme.fixed)
                }
            ],
            style_as_list_view=True,

            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
                'lineHeight': '15px'
            },
            
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Date'},
                    'width': '140px',
                },

                {
                    'if': {'column_id': 'Points'},
                    'width': '60px',
                },
                
            ] + format_colors_based_on_similarity(),
            row_deletable=True,
            row_selectable=False,
            tooltip_duration=None,
            tooltip_delay=0,
        ),
    ])
    return table


def get_extra_buttons() -> dbc.ButtonGroup:
    return dbc.ButtonGroup([
        dbc.Button(
            "Importuj .csv",
            id='button-import',
            className='btn-warning'),
    ])


def get_search_button() -> dbc.Button:
    return dbc.Button(
        "Szukaj",
        id='button-search',
        className='btn-success',
        block=True)


def get_sidebar():
    return html.Div(
    children=[
        html.H2("Wyszukiwarka punktów", className="display-4"),
        html.Hr(),
        html.P(
            "Wypełnij formularz po prawej stronie, a następnie wciśnij `Szukaj`. Kliknij na wynik wyszukiwania aby zobaczyć więcej informacji.",
            className="lead",
            id='starting-info'
        ),

    ],
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "30rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    },
    id='sidebar'
)

def get_content():
    return html.Div(
        id="page-content",
        style={
            "margin-left": "34rem",
            "margin-right": "4rem",
            "padding": "2rem 1rem",
        },
        children=[
            get_domain_form_group(),
            get_publication_type_form_group(),
            get_search_table(),
            get_extra_buttons(),
            get_search_button(),
            get_results_table(),
        ],
    )

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([get_sidebar(), get_content()])


@app.callback(
    Output('search-table', 'data'),
    Input('button-add-row', 'n_clicks'),
    State('search-table', 'data'),
    State('search-table', 'columns')
)
def add_row(n_clicks, rows, columns):

    if n_clicks is not None:
        rows.append({c['id']: '' for c in columns})
    return rows


@app.callback(
    Output('results-table', 'data'),
    Output('results-table', 'tooltip_data'),
    Input('button-search', 'n_clicks'),
    Input('domain-input', 'value'),
    Input('publication-type-input', 'value'),
    State('search-table', 'data'),
)
def search(n_clicks, domains, publication_type, search_table_data):
    if n_clicks is None:
        return None, None

    db_cursor = Cursor(config)

    if publication_type == 'czasopisma':
        query_function = partial(ir.query_journals, domains=domains)

    elif publication_type == 'konferencje':
        query_function = ir.query_conferences

    elif publication_type == 'monografie':
        query_function = ir.query_monographs

    else:
        raise RuntimeError("Unknown publication type!")

    data = []
    tooltip_data = []
    for row in search_table_data:

        sim, df = query_function(row["Title"])
        try:
            name = df.name.iloc[0]
            date_points = db_cursor.get_date_points(name, publication_type)
            for _, date, points in date_points:
                points_for_selected_date = points
                if date > row['Date']:
                    break
        except AttributeError:  # No matches have been found for this title
            sim = 0.0
            name = ''
            date_points = []
            points_for_selected_date = 0

        data.append({
            'Title': name,
            'Date': row["Date"],
            'Points': [points_for_selected_date],
            'PointsHistory': date_points,
            'Similarity': sim
        })

        tooltip_data.append({
            'Title': {
                'value': format_suggestions_based_on_search(row['Title'], df),
                'type': 'markdown',
                },
            'Points': {'value': 'Kliknij aby zobaczyć szczegóły', 'type': 'text'}
        })

    return data, tooltip_data

@app.callback(
    Output('sidebar', 'children'),
    Input('results-table', 'selected_cells'),
    State('results-table', 'data'),
    State('sidebar', 'children')

)
def update_sidebar_on_row_click(selected_cells, data, current_children):
    if selected_cells is None:
        return current_children

    selected_row = data[selected_cells[0]['row']]

    table_header = [
        html.Thead(html.Tr([html.Th("Data obowiązwania"), html.Th("Punkty")]))
    ]

    past_points = [
        html.Tr([html.Td(date), html.Td(points)])
        for _, date, points in selected_row['PointsHistory']
        ]

    table_body = [html.Tbody(past_points)]

    return  [
        html.H2("Wyszukiwarka punktów", className="display-4"),
        html.Hr(),
        html.H4(
            selected_row['Title'],
        ),
        html.P(
            'Wartości punktowe w czasie:'
        ),
        dbc.Table(table_header + table_body, bordered=True), 
    ]


if __name__ == "__main__":
    app.run_server()
