# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import csv
import re
import base64
from functools import partial
from io import StringIO
from typing import List

import dash
from dash.dependencies import Input, Output, State
import dash_table
from dash.exceptions import PreventUpdate
from dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash_extensions import Download
from dash_extensions.snippets import send_data_frame
from sqlalchemy import create_engine

from src import Config
from src.text_index import IndexReader
from src.app_utils import (
    format_colors_based_on_similarity,
    format_suggestions_based_on_search_sidebar,
    row_col, format_points_tooltip_based_on_search, format_suggestions_based_on_search,
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
    , id='domain-form-group')


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


def publication_type_to_column_title(publication_type: str = None) -> str:
    if publication_type == 'konferencje':
        return 'Nazwa konferencji'
    elif publication_type == 'monografie':
        return 'Nazwa wydawnictwa'

    return 'Tytu?? czasopisma'


def get_search_table_columns(title_text) -> List[dict]:
    return [
        {'id': 'Title', 'name': title_text, 'type': 'text', },
        {'id': 'Date', 'name': 'Data', 'type': 'datetime', }
    ]


def get_search_table() -> html.Div:
    table = html.Div([
        dash_table.DataTable(
            id='search-table',
            columns=get_search_table_columns(publication_type_to_column_title()),
            data=[
                {'Title': 'IEEE Transactions on Pattern Analysis and Machine Intelligence', 'Date': '2020'},
                {'Title': 'IEEE Intelligent Systems', 'Date': '2018'},
                {'Title': 'Foundations and Trends in Machine Learning',
                 'Date': '2019-12-20'},
                {'Title': 'Science Robotics', 'Date': '2020-01-20'},
            ],
            tooltip={
                'Title': {
                    'value': 'Pe??na lub cz????ciowa nazwa',
                    'use_with': 'both',
                    'delay': 500
                },
                'Date': {
                    'value': 'YYYY lub YYYY-MM-DD',
                    'delay': 500
                }
            },
            tooltip_header={
                'Date': 'Data wed??ug kt??rej liczone s?? punkty za osi??gni??cia naukowe. Format YYYY lub YYYY-MM-DD',
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


def get_results_table_columns(title_text: str) -> List[dict]:
    return [
        {'id': 'Title', 'name': title_text, 'type': 'text'},
        {'id': 'Date', 'name': 'Data', 'type': 'datetime'},
        {'id': 'Points', 'name': 'Punkty', 'type': 'numeric'},
        {
            'id': 'Similarity',
            'name': 'Dopasowanie',
            'type': 'numeric',
            'format': Format(precision=0, scheme=Scheme.percentage),
        },
    ]


def get_results_wrapper() -> html.Div:
    wrapper_content = html.Div(
        id='wrapper-content',
        style={'display': 'none'},
        children=[
            html.H4('Wyniki wyszukiwania'),
            html.P('', id='searched-for-label'),
            dcc.Input(id='searched-for-type', type='hidden'),
            dcc.Input(id='searched-for-domains', type='hidden'),
            dash_table.DataTable(
                id='results-table',
                columns=get_results_table_columns(publication_type_to_column_title()),
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
                    'textDecoration': 'none',
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
                    {
                        'if': {
                            'column_id': 'Points',
                            'filter_query': '{Points} < 1'
                        },
                        'color': 'var(--danger)',
                        'fontWeight': 'bold',
                    },
                    {
                        'if': {
                            'column_id': 'Points',
                            'filter_query': '{Date} < "2019-12-18" && {Date} contains " "'
                        },
                        'textDecoration': 'underline',
                    },
                ] + format_colors_based_on_similarity(),
                row_deletable=True,
                row_selectable=False,
                tooltip_header={
                    'Title': 'Nazwa znaleziona w bazie danych',
                    'Date': 'Data wed??ug kt??rej liczone s?? punkty za osi??gni??cia naukowe',
                    'Points': 'Punkty ustalone na podstawie wybranych dziedzin i daty',
                    'Similarity': 'W jakim stopniu wynik wyszukiwania jest podobny do zapytania',
                },
                tooltip_duration=None,
                tooltip_delay=0,
            ),
            html.Div(
                [dbc.Button(
                    'Eksportuj do .csv',
                    id='button-export',
                    color='info',
                    outline=True,
                    className='mt-2'
                ), Download(id='download')],
                style={'text-align': 'right'}
            ),
        ],
    )

    wrapper = dcc.Loading(
        id='loading-results',
        color='var(--primary)',
        style={'display': 'none'},
        children=wrapper_content
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
                html.P('Wklej lub prze??lij plik .csv z danymi do wyszukania.'),
                html.Ul([
                    html.Li('Plik powinien zawiera?? przynajmniej dwie kolumny: szukana nazwa i data.'
                            ' Warto??ci w drugiej kolumnie mog?? zosta?? pomini??te, ale separator musi by?? obecny.'),
                    html.Li('Kolumny mog?? by?? rozdzielone znakami , ; lub tabulatora.'),
                    html.Li('Je??li to konieczne, warto??ci mog?? by?? zawarte w cudzys??owach, np.: "nazwa".'),
                    html.Li('Daty powinny by?? w formacie YYYY lub YYYY-MM-DD.'),
                ]),
                dcc.Upload(
                    html.Div([
                        'Przeci??gnij i upu???? lub ',
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
                    debounce=True,
                ),
                dbc.FormGroup(
                    id='group-cb-import-headers',
                    className='mt-2',
                    children=[
                        dbc.Checkbox(id='checkbox-import-headers'),
                        dbc.Label(
                            'Moje dane maj?? nag????wki',
                            html_for='checkbox-import-headers',
                            className='form-check-label',
                        )
                    ]
                ),
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
            html.H4("Kalkulator punkt??w ministerialnych"),
            html.Hr(),
            html.Div(
                id='sidebar-content',
                children=html.P(
                    "Wype??nij formularz po prawej stronie, a nast??pnie wci??nij ???Szukaj???. Kliknij na wynik "
                    "wyszukiwania, aby zobaczy?? wi??cej informacji.",
                    id='starting-info'
                ),
            ),
            html.Div(id='sidebar-suggestions', hidden=True)
        ],
        className='bg-light col-3',
        id='sidebar',
    )


def get_content_column():
    return html.Div(
        id='content-column',
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
                row_col([], [], row_extra_classes='content-spacer'),
            ],
        ),
    )


def get_footer() -> html.Footer:
    return html.Footer(
        [
            html.P('J??zef Jasek, Micha?? Rdzany, Micha?? Sok??lski, Piotr Sowi??ski ??? MINI PW 2021'),
            html.P(html.A(
                'Zobacz kod na GitHubie.',
                href='https://github.com/rdzanyM/science_points',
            ))
        ],
        id='footer',
        className='text-primary',
    )


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title='Punkty ministerialne',
    update_title='??? Punkty ministerialne',
)
app.layout = html.Div(
    children=[
        html.Div(
            [get_sidebar(), get_content_column()],
            className='row',
        ),
        get_footer(),
    ],
    className='container-fluid',
)


@app.callback(
    Output('modal-import', 'is_open'),
    [
        Input('button-import', 'n_clicks'),
        Input('button-cancel-import', 'n_clicks'),
        Input('button-do-import', 'n_clicks'),
    ],
    [State('modal-import', 'is_open')],
)
def toggle_modal(n1, n2, n3, is_open: bool) -> bool:
    if n1 or n2 or n3:
        return not is_open
    return is_open


@app.callback(
    Output('textarea-import', 'value'),
    Input('upload-query', 'contents'),
)
def upload_file(content):
    if content is None or len(content) == 0:
        raise PreventUpdate

    try:
        _, text = content.split(',')
        return base64.b64decode(text).decode()
    except Exception:
        raise PreventUpdate


@app.callback(
    Output('checkbox-import-headers', 'checked'),
    Input('textarea-import', 'value'),
)
def guess_headers(content: str) -> bool:
    lines = (content or '').strip().split('\n')
    if len(lines) < 2:
        return False

    h_line = lines[0]
    if len(h_line) < 3:
        return False

    # all of these have the same length
    known_variants = ['Title;Points', 'Title,Points', 'Title\tPoints']
    if lines[0][:len(known_variants[0])] in known_variants:
        # Probably a reimport of exported data
        return True

    try:
        dialect = csv.Sniffer().sniff(content.strip())
    except csv.Error:
        return False

    header = lines[0].split(str(dialect.delimiter))
    if len(header) >= 2 and not re.search(r'\d\d', header[1]):
        # The second column name doesn't look like a date, assume it's a header
        return True

    return False


@app.callback(
    Output('search-table', 'data'),
    Input('button-add-row', 'n_clicks'),
    Input('button-do-import', 'n_clicks'),
    State('search-table', 'data'),
    State('search-table', 'columns'),
    State('textarea-import', 'value'),
    State('checkbox-import-headers', 'checked'),
)
def update_search_table(add_row_clicks, import_clicks, data, columns, import_text, import_header: bool):
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'button-add-row':
        data.append({c['id']: '' for c in columns})
        return data

    if button_id != 'button-do-import' or not import_text:
        return data

    try:
        df = pd.read_csv(
            StringIO(import_text),
            names=('Title', 'Date'),
            header=0 if import_header else None,
            parse_dates=False,
            quotechar='"',
            sep=None,
            dtype='str',
            skip_blank_lines=True,
            usecols=[0, 1],
            engine='python',
        ).fillna('')
    except Exception:
        # This should properly report the error, but meh, we can live without it
        raise PreventUpdate
    
    data = df.to_dict('records')
    return data


@app.callback(
    Output('results-table', 'columns'),
    Output('results-table', 'data'),
    Output('results-table', 'tooltip_data'),
    Output('searched-for-label', 'children'),
    Output('searched-for-type', 'value'),
    Output('searched-for-domains', 'value'),
    Output('sidebar-suggestions', 'value'),
    Input('button-search', 'n_clicks'),
    State('domain-input', 'value'),
    State('publication-type-input', 'value'),
    State('search-table', 'data'),
)
def search(n_clicks, domains, publication_type, search_table_data):
    if n_clicks is None:
        raise PreventUpdate

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
        suggestions = []
        for row in search_table_data:
            if not re.match(r'^\d{4}(-\d\d-\d\d)?$', row['Date']):
                row['Date'] = pd.to_datetime('today').strftime('%Y-%m-%d')
            elif re.match(r'^\d{4}$', row['Date']):
                row['Date'] = row['Date'] + '-01-01'
            df = query_function(row["Title"])
            try:
                domains_match = True
                name = df.name.iloc[0]
                sim = df.score.iloc[0]
                if publication_type == 'czasopisma':
                    domains_for_selected_row = set(db_cursor.get_journal_domains(name))
                elif publication_type == 'konferencje':
                    domains_for_selected_row = set(db_cursor.get_conference_domains(name))
                date_points = db_cursor.get_date_points(name, publication_type)
                points_for_selected_date = None
                for _, date, points in date_points:
                    if points_for_selected_date is None:
                        last_date = date
                        points_for_selected_date = points
                    if date > row['Date']:
                        if publication_type != 'monografie' and len(domains_for_selected_row & set(domains)) == 0:
                            domains_match = False
                            points_for_selected_date = 0
                        break
                    else:
                        last_date = date
                        points_for_selected_date = points
            except AttributeError as e:
                if 'name' in str(e):  # No matches have been found for this title
                    sim = 0.
                    name = ''
                    date_points = []
                    points_for_selected_date = 0
                else:
                    raise e

            try:
                elems = df[['name', 'score']].values.tolist()[1:]
            except:
                elems = []

            suggestions.append((row["Title"], elems))
            date_points.reverse()
            if publication_type == 'czasopisma' and last_date < '2019-12-18':
                row['Date'] = row['Date'] + ' '
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
                'Points': {
                    'value': format_points_tooltip_based_on_search(domains_match, name, last_date, publication_type),
                    'type': 'markdown'
                },
                'Date': {'value': 'Kliknij, by zobaczy?? szczeg????y', 'type': 'text'},
                'Similarity': {'value': 'Kliknij, by zobaczy?? szczeg????y', 'type': 'text'},
            })

    searched_for_label = f'Szukany rodzaj publikacji: {publication_type}.'
    if publication_type != 'monografie' and domains:
        searched_for_label += f" Dziedziny: {', '.join(domains)}."

    columns = get_results_table_columns(publication_type_to_column_title(publication_type))
    return columns, data, tooltip_data, searched_for_label, publication_type, domains, suggestions


@app.callback(
    Output('domain-form-group', 'style'),
    Output('search-table', 'columns'),
    Input('publication-type-input', 'value'),
)
def hide_domains_for_monographs(publication_type):
    style = {'display': 'block'}
    title_name = None

    if publication_type == 'czasopisma':
        title_name = 'Tytu?? czasopisma'
    elif publication_type == 'konferencje':
        title_name = 'Nazwa konferencji'
    elif publication_type == 'monografie':
        title_name = 'Nazwa wydawnictwa'
        style = {'display': 'none'}

    return style, get_search_table_columns(title_name)


@app.callback(
    Output('loading-results', 'style'),
    Output('wrapper-content', 'style'),
    Input('button-search', 'n_clicks'),
)
def hide_results_table_before_search_click(n_clicks):
    if n_clicks is None:
        return {'display': 'none'}, {'display': 'none'}
    return {'display': 'block'}, {'display': 'block'}


@app.callback(
    Output('sidebar-content', 'children'),
    Input('results-table', 'selected_cells'),
    State('searched-for-type', 'value'),
    State('searched-for-domains', 'value'),
    State('results-table', 'data'),
    State('sidebar-content', 'children'),
    State('sidebar-suggestions', 'value')
)
def update_sidebar_on_row_click(
        selected_cells,
        publication_type,
        searched_domains,
        data,
        current_children,
        suggestions
):
    if selected_cells is None or len(selected_cells) == 0:
        return current_children

    selected_row = data[selected_cells[0]['row']]

    table_tooltips = [
        'Data opublikowania rozporz??dzenia',
        'Warto???? punktowa podana w rozporz??dzeniu',
    ]
    table_header = [
        html.Thead(html.Tr([
            html.Th('Data', title=table_tooltips[0]),
            html.Th('Punkty', title=table_tooltips[1]),
        ]))
    ]

    past_points = [
        html.Tr([
            html.Td(date, title=table_tooltips[0]),
            html.Td(points, 
                title=table_tooltips[1] + '\nPunktacja wed??ug starego systemu (max 50 pkt)', 
                style={'text-decoration': 'underline'}),
        ]) if publication_type == 'czasopisma' and int(date[:4]) < 2018 
        else 
        html.Tr([
            html.Td(date, title=table_tooltips[0]),
            html.Td(points, title=table_tooltips[1]),
        ])
        for _, date, points in selected_row['PointsHistory']
    ]

    table_body = [html.Tbody(past_points)]
    title = selected_row['Title']

    domains = []
    with Cursor(engine) as cursor:
        if publication_type == 'czasopisma':
            domains = cursor.get_journal_domains(selected_row['Title'])
        elif publication_type == 'konferencje':
            domains = cursor.get_conference_domains(selected_row['Title'])

    result = [
        html.H5(title),
        dbc.Table(table_header + table_body, bordered=True),
    ]
    if domains:
        result.extend([
            html.P('Przypisane dziedziny:'),
            html.Ul(
                id='domain-list',
                children=[
                    html.Li(html.Strong(i)) if i in searched_domains else html.Li(i)
                    for i in domains
                ],
            ),
        ])

    original_name, additional_list = suggestions[selected_cells[0]['row']]
    suggestion_list = [
        dcc.Markdown(format_suggestions_based_on_search_sidebar(original_name, additional_list))
    ]
    result.extend(suggestion_list)
    return result


@app.callback(
    Output('download', 'data'),
    Input('button-export', 'n_clicks'),
    State('results-table', 'data')
)
def export_button_click(n_clicks, data):
    if n_clicks is None:
        return None

    df = pd.DataFrame(data)
    df.drop(columns=['PointsHistory', 'Similarity'], inplace=True)
    df['Points'] = df['Points'].apply(lambda x: x[0])
    return send_data_frame(df.to_csv, 'points.csv', sep=';', index=False)


if __name__ == "__main__":
    app.run_server()
