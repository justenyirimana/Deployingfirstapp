########Dependencies
import pandas as pd
import geopandas as gp
pd.set_option('max_rows',20)
import plotly.express as px
import plotly.io as pio
pio.renderers.default = "browser"
import pyproj

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_auth

USERNAME_PASSWORD = [['dsdivision', 'womensday123#']]
##########Get Data
# reading in the shapefile
fp = r"Districts\District.shp"

map_df = gp.read_file(fp)

amount_df = pd.read_csv("loans_amount.csv")#, header=0, encoding='cp1252')

final_df = map_df.set_index('District').join(amount_df.set_index('District'))

final_df['Amount'] = final_df['Amount'].fillna(0)
########Data Processing

#get data in cleaned time series format for country
def process_data(map_data, yr=2019):
    df = map_data[map_data['year'] == yr] 
    df = df.to_crs(pyproj.CRS.from_epsg(4326))
    return df

#get overall amount of application
def get_overall_total(df):
    return df.iloc[:,-1].sum()

#get overall volume of application
def get_overall_volume(df):
    return df.shape[0]

loan_overall_total = get_overall_total(amount_df)
loan_overall_volume = get_overall_volume(amount_df)

print('Overall Amount:',loan_overall_total)
print('Overall Applications:',loan_overall_volume)

#!!! I am hereMoving on to year

#get total amount per year
def get_yr_total(df,yr=2019):
    return df[df['year']==yr].iloc[:,-1].sum()

#get total volume per year
def get_yr_volume(df,yr=2019):
    return df[df['year']==yr].shape[0]

yr = 2019
loan_yr_total = get_yr_total(amount_df,yr)
volume_yr_total = get_yr_volume(amount_df,yr)
print(f'{yr} Amount:',loan_yr_total)
print(f'{yr} Volume:',volume_yr_total)

###########Generate Map Graph using Plotly
def fig_map_trend(yr=2019):
    df = process_data(map_data = final_df, yr=yr)
    fig = px.choropleth(
        data_frame=df,
        geojson=df.geometry,
        locations=df.index,
        color='Amount',
        color_continuous_scale=px.colors.sequential.YlOrRd,
        title='<b>'+'Total loan amount for the year {}'.format(yr)+'<b>'
    )
    fig.update_geos(fitbounds="locations", visible=False)
    return fig

external_stylesheets = [dbc.themes.DARKLY]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Loan Monitoring Dashboard'
auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD)

########Page Header
colors = {
    'background': '#EBCF8A',#EBCF8A, #AA892C 
    'bodyColor':'#F9F1DC',
    'text': '#652C0E'
}
def get_page_heading_style():
    return {'backgroundColor': colors['background']}


def get_page_heading_title():
    return html.H1(children='Loan Monitoring Dashboard',
                                        style={
                                        'textAlign': 'center',
                                        'color': colors['text']
                                    })

def get_page_heading_subtitle():
    return html.Div(children='Visualize loan distribution across districts',
                                         style={
                                             'textAlign':'center',
                                             'color':colors['text']
                                         })

def generate_page_header():
    main_header =  dbc.Row(
                            [
                                dbc.Col(get_page_heading_title(),md=12)
                            ],
                            align="center",
                            style=get_page_heading_style()
                        )
    subtitle_header = dbc.Row(
                            [
                                dbc.Col(get_page_heading_subtitle(),md=12)
                            ],
                            align="center",
                            style=get_page_heading_style()
                        )
    header = (main_header,subtitle_header)
    return header

##########Select Country dropdown
def get_year_list():
    return amount_df['year'].unique()

def create_dropdown_list(yr_list):
    dropdown_list = []
    for yr in sorted(yr_list):
        tmp_dict = {'label':str(yr),'value':yr}
        dropdown_list.append(tmp_dict)
    return dropdown_list

def get_year_dropdown(id):
    return html.Div([
                        html.Label('Select Year'),
                        dcc.Dropdown(id='my-id'+str(id),
                            options=create_dropdown_list(get_year_list()),
                            value=2019
                        ),
                        html.Div(id='my-div'+str(id))
                    ], style={'color':colors['text']}
                                         )

###########Graph Container for DASH
def graph1():
    return dcc.Graph(id='graph1',figure=fig_map_trend(2019))


#########Generate CARDS for overall numbers
def generate_card_content(card_header,card_value,overall_value):
    card_head_style = {'textAlign':'center','fontSize':'150%'}
    card_body_style = {'textAlign':'center','fontSize':'200%'}
    card_header = dbc.CardHeader(card_header,style=card_head_style)
    card_body = dbc.CardBody(
        [
            html.H5(f"{int(card_value):,}", className="card-title",style=card_body_style),
            html.P(
                "Overall: {:,}".format(overall_value),
                className="card-text",style={'textAlign':'center'}
            ),
        ]
    )
    card = [card_header,card_body]
    return card

def generate_cards(yr=2019):
    loan_yr_total = get_yr_total(amount_df,yr)
    volume_yr_total = get_yr_volume(amount_df,yr)
    cards = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(dbc.Card(generate_card_content("Amount",loan_yr_total,loan_overall_total), color="success", inverse=True),md=dict(size=3,offset=3)),
                    dbc.Col(dbc.Card(generate_card_content("Volume",volume_yr_total,loan_overall_volume), color="warning", inverse=True),md=dict(size=2)),
                ],
                className="mb-4",
            ),
        ],id='card1'
    )
    return cards


# #########DASH Slider for Moving Average Window
# def get_slider():
#     return html.Div([  
#                         dcc.Slider(
#                             id='my-slider',
#                             min=1,
#                             max=15,
#                             step=None,
#                             marks={
#                                 1: '1',
#                                 3: '3',
#                                 5: '5',
#                                 7: '1-Week',
#                                 14: 'Fortnight'
#                             },
#                             value=3,
#                         ),
#                         html.Div([html.Label('Select Moving Average Window')],id='my-div'+str(id),style={'textAlign':'center'})
#                     ])

#########Generate APP layout
def generate_layout():
    page_header = generate_page_header()
    layout = dbc.Container(
        [
            page_header[0],
            page_header[1],
            html.Hr(),
            generate_cards(),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(get_year_dropdown(id=1),md=dict(size=4,offset=4))                    
                ]
            
            ),
            html.Br(),
            html.Br(),
            dbc.Row(
                [                
                    
                    dbc.Col(graph1(),md=dict(size=6,offset=3))
        
                ],
                align="center",

            ),
        ],fluid=True,style={'backgroundColor': colors['bodyColor']}
    )
    return layout

app.layout = generate_layout()

########Assign DASH Callbacks
@app.callback(
    [Output(component_id='graph1',component_property='figure'), #line chart
    Output(component_id='card1',component_property='children')], #overall card numbers
    [Input(component_id='my-id1',component_property='value')] #dropdown 
)
def update_output_div(input_value1):
    return fig_map_trend(input_value1),generate_cards(input_value1)

if __name__ == '__main__':
    app.run_server(debug=True)