# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from typing import Type

import dash
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

def get_search_table() -> Type[dbc.Table]:
    table_header = [

    html.Thead(html.Tr([html.Th("Tytuł czasopisma"), html.Th("Data publikacji")]))
    ]

    row1 = html.Tr([html.Td("Nature"), html.Td("2019-02-21")])
    row2 = html.Tr([html.Td("Nature"), html.Td("2019-01-16")])
    row3 = html.Tr([html.Td("Journal of Machine Learning Research"), html.Td("2018-03-01")])
    table_body = [html.Tbody([row1, row2, row3])]
    table = dbc.Table(table_header + table_body, bordered=True)

    return table

def get_extra_buttons() -> Type[dbc.ButtonGroup]:
    return dbc.ButtonGroup([

        dbc.Button(
            "Importuj .csv",
            id='button-import',
            className='btn-warning'),

        dbc.Button(
            "Dodaj wiersz",
            id="button-add-row",
            className='btn-success'
            ),
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

if __name__ == "__main__":
    app.run_server()
