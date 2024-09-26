import os
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
from datetime import datetime
import dash_bootstrap_components as dbc


def collect_file_metadata(directory_path):
    file_info_list = []  

   
    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                
                file_stats = os.stat(file_path)
                created_time = datetime.fromtimestamp(file_stats.st_ctime)
                modified_time = datetime.fromtimestamp(file_stats.st_mtime)
                accessed_time = datetime.fromtimestamp(file_stats.st_atime)

                
                file_info_list.append({
                    "folder": os.path.basename(root),
                    "file_name": file_name,
                    "created_time": created_time,
                    "modified_time": modified_time,
                    "accessed_time": accessed_time,
                    "file_path": file_path
                })
            except Exception as e:
                
                print(f"Error reading file metadata for {file_path}: {e}")

   
    return pd.DataFrame(file_info_list)


data_directory = "C:/Extract/Data"
system_directory = "C:/Extract/System"


data_metadata = collect_file_metadata(data_directory)
system_metadata = collect_file_metadata(system_directory)


all_file_metadata = pd.concat([data_metadata, system_metadata], ignore_index=True)


all_file_metadata['date'] = all_file_metadata['modified_time'].dt.date


app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])


app.layout = dbc.Container([
    
    dbc.Tabs([
        
        dbc.Tab(label='Timeline Visualization', tab_id='timeline-tab', children=[
            dbc.Row([
                dbc.Col(html.H1("Forensic Timeline Dashboard"), className="mb-4")
            ]),
            dbc.Row([
                dbc.Col([
                    
                    dbc.Card([
                        dbc.CardHeader("Filters"),
                        dbc.CardBody([
                            dcc.DatePickerRange(
                                id='date-picker-range',
                                start_date=all_file_metadata['date'].min(),
                                end_date=all_file_metadata['date'].max(),
                                display_format='YYYY-MM-DD',
                            ),
                            html.Br(),
                            html.Label("Select Event Type:"),
                            dcc.Dropdown(
                                id='event-type-dropdown',
                                options=[
                                    {'label': 'File Created', 'value': 'created_time'},
                                    {'label': 'File Modified', 'value': 'modified_time'},
                                    {'label': 'File Accessed', 'value': 'accessed_time'}
                                ],
                                value='modified_time',
                                clearable=False,
                                style={'width': '100%'}
                            )
                        ])
                    ], className="mb-4")
                ], width=4),
                dbc.Col([
                    
                    dbc.Card([
                        dbc.CardHeader("Timeline Analysis"),
                        dbc.CardBody([
                            dcc.Graph(id='timeline-graph')
                        ])
                    ])
                ], width=8),
            ]),
            dbc.Row([
                dbc.Col([
                   
                    dbc.Card([
                        dbc.CardHeader("Event Details"),
                        dbc.CardBody(
                            html.Div(id='event-details', style={'whiteSpace': 'pre-line'})
                        )
                    ])
                ])
            ])
        ]),
        
        dbc.Tab(label='CSV Export', tab_id='export-tab', children=[
            dbc.Row([
                dbc.Col(html.H1("Export Filtered Data as CSV"), className="mb-4")
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Button("Export CSV", id='export-csv', color="primary", className="mb-3"),
                    dcc.Download(id="download-dataframe-csv"),
                    html.Div(id='export-status')
                ])
            ])
        ]),
    ], id='tabs', active_tab='timeline-tab')
], fluid=True)

@app.callback(
    Output('timeline-graph', 'figure'),
    Output('event-details', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('event-type-dropdown', 'value'),
    Input('timeline-graph', 'clickData')
)
def update_timeline(start_date, end_date, selected_event_type, clicked_data):
    filtered_data = all_file_metadata[(all_file_metadata['date'] >= pd.to_datetime(start_date).date()) &
                                      (all_file_metadata['date'] <= pd.to_datetime(end_date).date())]

    event_counts = filtered_data.groupby(filtered_data[selected_event_type].dt.date).size().reset_index(name='counts')

    timeline_figure = px.bar(event_counts, x=event_counts[selected_event_type], y='counts',
                             title=f'{selected_event_type.replace("_", " ").capitalize()} Events Over Time',
                             labels={selected_event_type: 'Date', 'counts': 'Number of Events'})

    timeline_figure.update_layout(xaxis_title="Date", yaxis_title="Number of Events", hovermode='x unified')

    event_details = "Click on a bar to see more details here."
    if clicked_data:
        selected_date = clicked_data['points'][0]['x']
        clicked_events = filtered_data[filtered_data[selected_event_type].dt.date == pd.to_datetime(selected_date).date()]

        event_details = f"Details for {selected_date}:\n"
        for _, row in clicked_events.iterrows():
            event_details += f"File: {row['file_name']} | Path: {row['file_path']}\n"

    return timeline_figure, event_details

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("export-csv", "n_clicks"),
    prevent_initial_call=True,
)
def export_filtered_data(n_clicks):
    csv_data = all_file_metadata.to_csv(index=False)
    return dict(content=csv_data, filename="file_metadata.csv")

if __name__ == '__main__':
    app.run_server(debug=True)
