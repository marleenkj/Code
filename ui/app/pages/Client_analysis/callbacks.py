from src.plots import graph_solution_direct
from dash.dependencies import Input, Output
from app import app, results_direct_ftl_truck, results_direct_ftl_train, dict_terminals, dict_points, df_distance_matrix
from loguru import logger
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import sys
sys.path.append('../..')


def pie_distribution_recommendation(df):
    fig = go.Figure()
    fig.add_trace(go.Pie(values=df["Recommendation"].value_counts().values,
                         labels=df["Recommendation"].value_counts().index,
                         hole=0.3, textinfo="label+percent",
                         textfont={"size": 14, "family": "arial"},
                         ))
    return fig


def boxplot_distribution(df):
    fig = go.Figure()
    fig.add_trace(go.Box(x=df[df["Recommendation"] ==
                  "Rail"]["haversine distance"], name="Rail"))
    fig.add_trace(go.Box(x=df[df["Recommendation"] ==
                  "Road"]["haversine distance"], name="Road"))
    fig.update_traces(boxpoints=False)
    fig.update_layout(xaxis_title='Distance DC-Client')
    return fig


def correlation_matrix(df_original, closest_dct):
    df = df_original.copy()
    column_names = {
        'co2 road': "GHG road (total)",
        'co2 railroad': "GHG railroad (total)",
        'co2 mainhaul': "GHG railroad (mainhaul)",
        'co2 prehaul': "GHG railroad (prehaul)",
        'co2 endhaul': "GHG railroad (endhaul)",
        'distance road': "Distance DC-Client (road)",
        'haversine distance': "Distance DC-C (crow flies)",
        'distance railroad': "Distance DC-C (railroad)",
        'distance mainhaul': "Distance T-T (mainhaul)",
        'distance prehaul': "Distance DC-T (prehaul)",
        'distance endhaul': "Distance DC-T (endhaul)"
    }
    df["Recommendation"] = np.where(df["Recommendation"] == "Rail", 1, 0)
    df = df[df["terminal allocation"] != closest_dct]
    df["GHG Savings Ratio"] = df["co2 railroad"] / df["co2 road"]
    df["GHG Savings Ratio"] = (1 - df["GHG Savings Ratio"]) * 100
    df = df.rename(column_names, axis=1)
    df = df[["Distance DC-Client (road)",
             "Distance DC-C (crow flies)",
             "Distance DC-C (railroad)",
             "Distance T-T (mainhaul)",
             "Distance DC-T (endhaul)",
             "GHG Savings Ratio"]]
    df_corr = df.corr()
    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            x=df_corr.columns,
            y=df_corr.index,
            z=np.array(df_corr),
            text=df_corr.values,
            texttemplate='%{text:.2f}',
            colorscale=px.colors.diverging.RdBu,
            zmin=-1,
            zmax=1
        )
    )
    return fig


@app.callback(
    Output('plot-pie-truck', 'figure'),
    Output('plot-pie-train', 'figure'),
    Output('plot-boxplot-truck', 'figure'),
    Output('plot-boxplot-train', 'figure'),
    Input('url', 'pathname'),
)
def plot_boxplot(_):
    closest_dct = "T4"
    fig1 = pie_distribution_recommendation(results_direct_ftl_truck)
    fig2 = pie_distribution_recommendation(results_direct_ftl_train)
    fig3 = boxplot_distribution(results_direct_ftl_truck)
    fig4 = boxplot_distribution(results_direct_ftl_train)
    fig5 = correlation_matrix(results_direct_ftl_truck, closest_dct)
    fig6 = correlation_matrix(results_direct_ftl_train, closest_dct)
    return fig1, fig2, fig3, fig4  # , fig5, fig6


@app.callback(
    Output('dropdown-client', 'options'),
    Output('dropdown-client', 'value'),
    Input('url', 'pathname'),
)
def client_input(_):
    dff = results_direct_ftl_truck
    clients = [{"label": value, "value": value}
               for value in dff['client'].unique()]
    default_client = "C1017"
    return clients, default_client


@app.callback(
    Output('table-clients-truck', 'columns'),
    Input('url', 'pathname'),
)
def table_clients_columns(_):
    format_int = {'locale': {}, 'nully': '',
                  'prefix': None, 'specifier': ',.0f'}
    format_float = {'locale': {}, 'nully': '',
                    'prefix': None, 'specifier': ',.2f'}

    columns = [
        dict(
            id='client',
            name='Client',
            type="text"),
        dict(
            id='co2 road',
            name='GHG road [kg]',
            type='numeric',
            format=format_float),
        dict(
            id='co2 railroad',
            name='GHG railroad [kg]',
            type='numeric',
            format=format_float),
        dict(
            id='Recommendation',
            name='Recommendation',
            type="text")]
    return columns


@app.callback(
    Output('table-clients-truck', "data"),
    Input('url', 'pathname'),
)
def table_ghg(_):
    dff = results_direct_ftl_truck.reset_index()
    dff = dff.drop_duplicates()
    dff = dff[dff["dc"] == "DC1"]
    return dff.to_dict('records')


@app.callback(
    Output('plot-routing', "data"),
    Input('dropdown-client', 'value'),
)
def plot_map(client):
    dff = results_direct_ftl_truck.reset_index()
    dff = dff.drop_duplicates().reset_index()
    logger.info(dff.columns)
    dff = dff[dff["dc"] == "DC1"]
    x = dff[dff["client"] == client].iloc()
    logger.info(x)
    fig = graph_solution_direct(
        x,
        dict_points,
        dict_terminals,
        df_distance_matrix)
    return fig
