# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from typing import Type

import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_bootstrap_components as dbc
import dash_html_components as html


def get_domain_form_group() -> Type[dbc.FormGroup]:
    return dbc.FormGroup(
        [
            dbc.Label("Wybierz dziedziny"),
            dbc.Checklist(
                options=[
                    {"label": "Matematyka", "value": 'matematyka'},
                    {"label": "Informatyka", "value": 'informatyka'},
                ],
                value=[],
                id="domain-input",
                inline=True
            ),
        ]
    )


def get_publication_type_form_group() -> Type[dbc.FormGroup]:
    return dbc.FormGroup(
        [
            dbc.Label("Wybierz rodzaj publikacji"),
            dbc.RadioItems(
                options=[
                    {"label": "czasopisma", "value": 'czasopisma'},
                    {"label": "konferencje", "value": 'konferencje'},
                    {"label": "monografie", "value": 'monografie'},
                ],
                value=[],
                id="publication-type-input",
                inline=True
            ),
        ]
    )

def get_search_table():
    table = html.Div([
        dash_table.DataTable(

            id='search-table',

            columns=(
                [{'id': 'Title', 'name': 'Tytuł', 'type': 'text', }] +
                [{'id': 'Date', 'name': 'Data', 'type': 'datetime', }]
            ),

            data=[
                dict(Model=i, Date=i) for i in range(1, 5)
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

            style_as_list_view=True,

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
    ])
    return table


def get_extra_buttons() -> Type[dbc.ButtonGroup]:
    return dbc.ButtonGroup([
        dbc.Button(
            "Importuj .csv",
            id='button-import',
            className='btn-warning'),
    ])


def get_search_button() -> Type[dbc.Button]:
    return dbc.Button(
        "Szukaj",
        id='button-search',
        className='btn-success',
        block=True)


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    children=[
        get_domain_form_group(),
        get_publication_type_form_group(),
        get_search_table(),
        get_extra_buttons(),
        get_search_button(),
    ],
    className="p-5",
)


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


if __name__ == "__main__":
    app.run_server()
