# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from functools import partial

import dash
from dash.dependencies import Input, Output, State
import dash_table
from dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from sqlalchemy import create_engine

from src import Config
from src.text_index import IndexReader
from src.app_utils import (
    format_colors_based_on_similarity,
    format_suggestions_based_on_search,
    row_col,
)
from src.orm import Cursor

config = Config()
ir = IndexReader(config)
engine = create_engine(f"sqlite:///{config['db_file']}")


def get_domain_form_group() -> dbc.FormGroup:
    with Cursor(engine) as cursor:
        domains = cursor.get_domains()

    return dbc.FormGroup(
        [
            dbc.Label('Dziedziny:', className='lead'),
            dcc.Dropdown(
                options=[
                   {'label': domain, 'value': domain}
                    for domain in domains
                ],
                value=['matematyka', 'informatyka'],
                multi=True,
                id="domain-input",

            )
        ]
    )


def get_publication_type_form_group() -> dbc.FormGroup:
    return dbc.FormGroup(
        [
            dbc.Label('Rodzaj publikacji:', className='lead'),
            html.Div(
                [
                    dbc.RadioItems(
                        className="btn-group",
                        labelClassName="btn btn-primary",
                        labelCheckedClassName="active",
                        options=[
                            {"label": "czasopisma", "value": 'czasopisma'},
                            {"label": "konferencje", "value": 'konferencje'},
                            {"label": "monografie", "value": 'monografie'},
                        ],
                        value='czasopisma',
                        id="publication-type-input",
                    ),
                ],
                className='radio-group',
            )
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
                    'value': 'Pełny lub częściowy tytuł',
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
            style_cell={
                'padding': '5px',
                'textAlign': 'left',
            },
            style_header={
                'fontWeight': 'bold',
                'textAlign': 'left',
                'backgroundColor': 'var(--light)',
            },
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
                'lineHeight': '15px'
            },
            style_cell_conditional=[
                {
                    'if': {'state': 'selected'},
                    'backgroundColor': '#dbf0ff',
                    'border': '1px solid #3498db',
                },
            ],
            editable=True,
            row_deletable=True,
            page_action='none',
        ),
    ]
    )
    return table


def get_results_wrapper() -> html.Div:
    wrapper = dcc.Loading(
        id='loading-results',
        color='var(--primary)',
        children=[
            html.H4('Wyniki wyszukiwania'),
            dash_table.DataTable(
                id='results-table',
                columns=[
                    {'id': 'Title', 'name': 'Tytuł', 'type': 'text', },
                    {'id': 'Date', 'name': 'Data', 'type': 'datetime', },
                    {'id': 'Points', 'name': 'Punkty', 'type': 'numeric', },
                    {'id': 'Similarity',
                     'name': 'Dopasowanie',
                     'type': 'numeric',
                     'format': Format(precision=0, scheme=Scheme.percentage)
                     }
                ],
                style_cell={
                    'padding': '0.2rem 0.3rem',
                },
                style_data={
                    'whiteSpace': 'normal',
                },
                style_header={
                    'fontWeight': 'bold',
                    'textAlign': 'left',
                    'backgroundColor': 'var(--light)',
                    'color': 'black',
                },
                style_cell_conditional=[
                    {
                        'if': {'state': 'selected'},
                        'backgroundColor': '#dbf0ff',
                        'border': '1px solid #3498db',
                    },
                    {
                        'if': {'column_id': 'Title'},
                        'textAlign': 'left',
                    },
                    {
                        'if': {'column_id': 'Date'},
                        'textAlign': 'left',
                    },
                ] + format_colors_based_on_similarity(),
                row_deletable=True,
                row_selectable=False,
                tooltip_duration=None,
                tooltip_delay=0,
            ),
            html.Div(
                dbc.Button(
                    'Eksportuj do .csv',
                    id='button-export',
                    color='info',
                    outline=True,
                    className='mt-2'
                ),
                style={'text-align': 'right'}
            ),
        ],
    )
    return wrapper


def get_extra_buttons() -> dbc.ButtonGroup:
    return dbc.ButtonGroup([
        dbc.Button(
            'Dodaj wiersz',
            id='button-add-row',
            color='info',
        ),
        dbc.Button(
            'Importuj .csv',
            id='button-import',
            color='info',
            outline=True,
        ),
    ])


def get_import_modal() -> dbc.Modal:
    return dbc.Modal(
        [
            dbc.ModalHeader('Importuj zapytanie z pliku .csv'),
            dbc.ModalBody([
                html.P('Wklej lub prześlij plik .csv z danymi do wyszukania.'),
                html.Ul([
                    html.Li('Plik nie powinien zawierać nagłówków.'),
                    html.Li('Plik powinien zawierać maksymalnie dwie kolumny: szukana nazwa i data. Druga kolumna '
                            'może zostać pominięta.'),
                    html.Li('Kolumny mogą być rozdzielone znakami , ; lub tabulatora.'),
                    html.Li('Jeśli to konieczne, pola mogą być zawarte w cudzysłowach, np.: "nazwa".')
                ]),
                dcc.Upload(
                    html.Div([
                        'Przeciągnij i upuść lub ',
                        html.A('wybierz plik', className='text-info', style={'cursor': 'pointer'})
                    ]),
                    id='upload-query',
                    style={
                        'width': '100%',
                        'height': '2.5rem',
                        'lineHeight': '2.5rem',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                    },
                    className='mb-2',
                ),
                dbc.Textarea(
                    id='textarea-import',
                    placeholder='Wklej plik .csv',
                    style={
                        'height': '12rem',
                    },
                    className='text-monospace',
                )
            ]),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        'Anuluj',
                        id='button-cancel-import',
                        color='danger',
                        outline=True,
                        className='mr-2',
                    ),
                    dbc.Button(
                        'Importuj',
                        id='button-do-import',
                        color='primary',
                    ),
                ],
                style={'justify-content': 'space-between'}
            ),
        ],
        id='modal-import',
        centered=True,
        size='lg',
    )


def get_search_button() -> dbc.Button:
    return dbc.Button(
        "Szukaj",
        id='button-search',
        color='primary',
        block=True
    )


def get_sidebar():
    return html.Div(
        children=[
            html.H4("Kalkulator punktów ministerialnych"),
            html.Hr(),
            html.Div(
                id='sidebar-content',
                children=html.P(
                    "Wypełnij formularz po prawej stronie, a następnie wciśnij „Szukaj”. Kliknij na wynik "
                    "wyszukiwania, aby zobaczyć więcej informacji.",
                    id='starting-info'
                ),
            )
        ],
        className='bg-light col-3',
        style={
            'padding': '2rem 1rem',
            'height': '100vh',
        },
        id='sidebar'
    )


def get_content_column():
    return html.Div(
        className='col-9',
        children=html.Div(
            className='container',
            children=[
                row_col([get_publication_type_form_group()], [12], row_extra_classes='mt-3'),
                row_col([get_domain_form_group()], [12]),
                row_col([get_search_table()], [12], row_extra_classes='mt-1'),
                row_col(
                    [[get_extra_buttons(), get_import_modal()]],
                    [12],
                    [{'text-align': 'right'}],
                    row_extra_classes='mt-2',
                ),
                row_col([get_search_button()], [12], row_extra_classes='mt-3'),
                row_col([get_results_wrapper()], [12], row_extra_classes='mt-5'),
            ],
        ),
    )


app = dash.Dash(
    external_stylesheets=[dbc.themes.FLATLY],
    title='Punkty ministerialne',
    update_title='⌛ Punkty ministerialne',
)

app.layout = html.Div(
    html.Div(
        [get_sidebar(), get_content_column()],
        className='row',
    ),
    className='container-fluid',
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


@app.callback(
    Output('modal-import', 'is_open'),
    [Input('button-import', 'n_clicks'), Input('button-cancel-import', 'n_clicks')],
    [State('modal-import', 'is_open')],
)
def toggle_modal(n1, n2, is_open: bool) -> bool:
    if n1 or n2:
        return not is_open
    return is_open


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

    with Cursor(engine) as db_cursor:
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
            except AttributeError as e:
                if 'name' in str(e):  # No matches have been found for this title
                    sim = 0.0
                    name = ''
                    date_points = []
                    points_for_selected_date = 0
                else:
                    raise e

            data.append({
                'Title': name,
                'Date': row["Date"],
                'Points': [points_for_selected_date],
                'PointsHistory': date_points,
                'Similarity': round(float(sim), 2)
            })

            tooltip_data.append({
                'Title': {
                    'value': format_suggestions_based_on_search(row['Title'], df),
                    'type': 'markdown',
                },
                'Points': {'value': 'Kliknij, by zobaczyć szczegóły', 'type': 'text'},
                'Date': {'value': 'Kliknij, by zobaczyć szczegóły', 'type': 'text'},
                'Similarity': {'value': 'Kliknij, by zobaczyć szczegóły', 'type': 'text'},
            })

    return data, tooltip_data


@app.callback(
    Output('sidebar-content', 'children'),
    Input('results-table', 'selected_cells'),
    State('results-table', 'data'),
    State('sidebar-content', 'children')
)
def update_sidebar_on_row_click(selected_cells, data, current_children):
    if selected_cells is None or len(selected_cells) == 0:
        return current_children

    selected_row = data[selected_cells[0]['row']]

    table_header = [
        html.Thead(html.Tr([html.Th('Data'), html.Th('Punkty')]))
    ]

    past_points = [
        html.Tr([html.Td(date), html.Td(points)])
        for _, date, points in selected_row['PointsHistory']
    ]

    table_body = [html.Tbody(past_points)]

    return [
        html.H5(
            selected_row['Title'],
        ),
        html.P(
            'Wartości punktowe w czasie:'
        ),
        dbc.Table(table_header + table_body, bordered=True),
    ]


if __name__ == "__main__":
    app.run_server()
