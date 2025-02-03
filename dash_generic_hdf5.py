import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import base64
import io
import h5py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
import codecs
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select hdf5 Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=True
    ),
    html.Div([
        html.H4('Select File:'),
        dcc.Dropdown(id='file-dropdown-1', options=[]),
        dcc.Dropdown(id='file-dropdown-2', options=[]),
        dcc.Dropdown(
            id='data-key-dropdown',
            options=[],
            value='',
            placeholder="Select a key"
        )   
    ]),
    html.Div([
        html.H4('Select Radionuclide:'),
        dcc.Dropdown(
            id='radionuclide-dropdown',
            options=[],
            value=[],
            multi=True
        ),
        html.Div([
            html.H4('X Axis:'),
            dcc.Dropdown(
                id='x-axis-type',
                options=[
                    {'label': 'Linear', 'value': 'linear'},
                    {'label': 'Log', 'value': 'log'}
                ],
                value='log'
            )
        ]),
        html.Div([
            html.H4('Y Axis:'),
            dcc.Dropdown(
                id='y-axis-type',
                options=[
                    {'label': 'Linear', 'value': 'linear'},
                    {'label': 'Log', 'value': 'log'}
                ],
                value='log'
            )
        ]),
        html.Div([
            html.H4('Limit Value:'),
            dcc.Input(
                id='limit-value',
                type='number',
                placeholder='Enter a limit value'
            )
        ]),
        html.Div([
        html.Label('X-axis minimum:'),
        dcc.Input(id='xmin', type='number', value=1000)
        ]),
        html.Div([
            html.Label('X-axis maximum:'),
            dcc.Input(id='xmax', type='number', value=100000)
        ]),
        html.Div([
            html.Label('Y-axis minimum:'),
            dcc.Input(id='ymin', type='number', value=1)
        ]),
        html.Div([
            html.Label('Y-axis maximum:'),
            dcc.Input(id='ymax', type='number', value=1e8)
        ]),
        html.Div(id='table-div'),
        html.Div(id='output-data-upload'),
        dcc.Store(id='contents-store')
    ]),
    dcc.Graph(id='graph'),
    html.Div([
        html.Label('Width:'),
        dcc.Input(id='width', type='number', value=800),
    ]),
    html.Div([
        html.Label('Height:'),
        dcc.Input(id='height', type='number', value=600),
    ]),
    html.Button("Download Image", id="btn_image"),
    dcc.Download(id="download-image")   
])


@app.callback(
    Output('data-key-dropdown', 'options'),
    [Input('file-dropdown-1', 'value')],
    [State('contents-store', 'data')]
)
def update_data_key_options(filename, contents):
    if filename is not None and contents is not None:
        content = contents.get(filename)
        if content:
            if isinstance(content, list):
                content = content[0]
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            with h5py.File(io.BytesIO(decoded), 'r') as hf:
                keys = list(hf.keys())
                return [{'label': key, 'value': key} for key in keys]
    return []
@app.callback(
    Output('file-dropdown-1', 'options'),
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_file_dropdown_1(contents, filename):
    if contents is not None:
        return [{'label': f, 'value': f} for f in filename]
    return []

@app.callback(
    Output('file-dropdown-2', 'options'),
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_file_dropdown_2(contents, filename):
    if contents is not None:
        return [{'label': f, 'value': f} for f in filename]
    return []

@app.callback(
    Output('contents-store', 'data'),
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_contents_store(contents, filename):
    if contents is not None:
        return {f: contents for f in filename}
    return {}

@app.callback(
    Output('radionuclide-dropdown', 'options'),
    [Input('file-dropdown-1', 'value'),
     Input('file-dropdown-2', 'value')],
    [State('contents-store', 'data')]
)
def update_radionuclide_dropdown(filename1, filename2, contents):
    if filename1 is not None and contents is not None:
        content = contents.get(filename1)
        if content:
            if isinstance(content, list):
                content = content[0]
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            with h5py.File(io.BytesIO(decoded), 'r') as hf:
                radionuclides = list(hf['OutflowGeosphere'].keys())
                return [{'label': radionuclide, 'value': radionuclide} for radionuclide in radionuclides]
    elif filename2 is not None and contents is not None:
        content = contents.get(filename2)
        if content:
            if isinstance(content, list):
                content = content[0]
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            with h5py.File(io.BytesIO(decoded), 'r') as hf:
                radionuclides = list(hf['OutflowGeosphere'].keys())
                return [{'label': radionuclide, 'value': radionuclide} for radionuclide in radionuclides]
    return []

@app.callback(
    Output('graph', 'figure'),
    [Input('xmin', 'value'),
     Input('xmax', 'value'),
     Input('ymin', 'value'),
     Input('ymax', 'value'),
    Input('radionuclide-dropdown', 'value'),
     Input('x-axis-type', 'value'),
     Input('y-axis-type', 'value'),
     Input('file-dropdown-1', 'value'),
     Input('file-dropdown-2', 'value'),
     Input('limit-value', 'value'),
     Input('data-key-dropdown', 'value')],
    [State('contents-store', 'data')]
)
def update_graph(xmin, xmax, ymin, ymax, selected_radionuclides, x_axis_type, y_axis_type, filename1, filename2, limit_value, data_key, contents,):
    if selected_radionuclides is not None and contents is not None:
        coloraxis='Black'
        fig = go.Figure()
        color_palette = px.colors.qualitative.Set3
        fig.add_trace(go.Scatter(x=[0, 100000], y=[limit_value, limit_value], name='Limit Value', mode='lines', line=dict(color='black', dash='dash')))
        for i, filename in enumerate([filename1, filename2]):
            if filename is not None:
                content = contents.get(filename)
                if content:
                    if isinstance(content, list):
                        content = content[0]
                    content_type, content_string = content.split(',')
                    decoded = base64.b64decode(content_string)
                    with h5py.File(io.BytesIO(decoded), 'r') as hf:
                        for j, radionuclide in enumerate(selected_radionuclides):
                            if data_key in hf:
                                df = pd.DataFrame(hf[data_key][radionuclide])
                                if len(df.columns) == 1:
                                    if i == 0:
                                        fig.add_trace(go.Scatter(x=hf['time'][:], y=df.iloc[:, 0], name=f"{radionuclide} ({filename})", line=dict(color=color_palette[j % len(color_palette)])))
                                    else:
                                        fig.add_trace(go.Scatter(x=hf['time'][:], y=df.iloc[:, 0], name=f"{radionuclide} ({filename})", mode='markers', marker=dict(symbol='cross', color=color_palette[j % len(color_palette)])))
                                else:
                                    if i == 0:
                                        fig.add_trace(go.Scatter(x=hf['time'][:], y=df.iloc[:, 1], name=f"{radionuclide} ({filename})", line=dict(color=color_palette[j % len(color_palette)])))
                                    else:
                                        fig.add_trace(go.Scatter(x=hf['time'][:], y=df.iloc[:, 1], name=f"{radionuclide} ({filename})", mode='markers', marker=dict(symbol='cross', color=color_palette[j % len(color_palette)])))
        fig.update_layout(
            xaxis_title='Time (years)',
            yaxis_title='Activity (Bq)',
            title='Radionuclide Activity (Bq)',
            legend=dict()
        )
        if x_axis_type == 'log':
            fig.update_layout(xaxis=dict(type=x_axis_type, range=[np.log10(xmin), np.log10(xmax)]))
        else:
            fig.update_layout(xaxis=dict(type=x_axis_type, range=[xmin, xmax]))
                
        if y_axis_type == 'log':
            fig.update_layout(yaxis=dict(type=y_axis_type, range=[np.log10(ymin), np.log10(ymax)]))
        else:
            fig.update_layout(yaxis=dict(type=y_axis_type, range=[ymin, ymax]))
        # Draw border around the plot:
        fig.update_xaxes(showgrid=True,
                         showline=True,
                         ticks='outside',
                         tickwidth=2,
                         linewidth=2,
                         linecolor=coloraxis, 
                         mirror=False,
                         tickcolor=coloraxis,
                         minor=dict(ticks='outside', ticklen=2, tickwidth=1, showgrid=True))


        fig.update_yaxes(showgrid=True,
                         showline=True,
                         ticks='outside',
                         tickwidth=2,
                         linewidth=2,
                         linecolor=coloraxis, 
                         mirror=False,
                         exponentformat='power',
                         tickcolor=coloraxis,
                         minor=dict(ticks='outside', ticklen=2, tickwidth=1, showgrid=True))
        return fig
    return {}


@app.callback(
    Output("download-image", "data"),
    Input("btn_image", "n_clicks"),
    [State('graph', 'figure'),
     State('width', 'value'),
     State('height', 'value')],
    prevent_initial_call=True,
)
def download_figure(n_clicks, figure, width, height):
    fig = go.Figure(data=figure['data'], layout=figure['layout'])
    image_bytes = fig.to_image(format='png', width=width, height=height)
    encoded_image = base64.b64encode(image_bytes).decode()
    return dict(content=encoded_image, filename='figure.png', type='image/png', base64=True)
if __name__ == '__main__':
    app.run_server(debug=True)
