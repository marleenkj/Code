from dash.dependencies import Input, Output, State
from app import app, df
from dash.exceptions import PreventUpdate
from loguru import logger
import io
import pandas as pd
import calendar
import numpy as np
import plotly.express as px

# functions
import pandas as pd
import calendar
import plotly.graph_objects as go
import datetime as dt

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value
    return [None] * 3


def apply_filters(dff, filter):
    # filtering
    filtering_expressions = filter.split(' && ')

    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]
    return dff


def apply_month_shipper(dff, month, shipper):
    # apply month filter
    dff['Pickup date'] = pd.to_datetime(dff["Pickup date"])
    if month is None:
        dff = dff
    else:
        dff = dff[dff['Pickup date'].dt.month == month]

    # apply shipper filter
    if shipper is None:
        dff = dff
    else:
        dff = dff[dff['DC name'] == shipper]
    return dff


def group_by_client_shipment(dff):
    dff = dff.groupby(
        [
            'Receiver longitude', 'Receiver latitude', "Client name", 'Shipment id']).agg(
        distance=(
            "Distance (km)", 'first'), weight=(
            'Sender weight (kg)', 'sum'), volume=(
            "Volume (m3)", 'sum'), count=(
            'Client name', 'count'), co2_diesel=(
            "Co2 diesel", 'sum'), co2_bev=(
            "Co2 BEV", 'sum')).reset_index()
    dff = dff.rename(
        columns={
            'distance': 'Distance (km)',
            'weight': 'Sender weight (kg)',
            'volume': 'Volume (m3)',
            'count': 'Number of shippings',
            'co2_diesel': 'Co2 diesel',
            'co2_bev': 'Co2 BEV'})
    return dff


def group_by_client(dff):
    dff = dff.groupby(
        [
            'Receiver longitude', 'Receiver latitude', "Client name"]).agg(
        distance=(
            "Distance (km)", 'first'), weight=(
            'Sender weight (kg)', 'sum'), volume=(
            "Volume (m3)", 'sum'), shipments=(
            'Number of shippings', 'sum'), co2_diesel=(
            "Co2 diesel", 'sum'), co2_bev=(
            "Co2 BEV", 'sum')).reset_index()
    dff = dff.rename(
        columns={
            'distance': 'Distance (km)',
            'weight': 'Sender weight (kg)',
            'volume': 'Volume (m3)',
            'shipments': 'Number of shippings',
            'co2_diesel': 'Co2 emissions (g)',
            'co2_bev': 'Co2 BEV (g)'})
    return dff


def apply_selected_rows_indices(dff, rows, selected_rows_indices):
    if (selected_rows_indices is None) or (selected_rows_indices == []):
        # No receiver selected
        dff = dff
    else:
        # filter for selected receiver
        df_select = pd.DataFrame(rows)
        logger.info(df_select.columns)
        receiver = df_select['Client name'].values[selected_rows_indices]
        receiver_lat = df_select['Receiver latitude'].values[selected_rows_indices]
        receiver_lon = df_select['Receiver longitude'].values[selected_rows_indices]
        dff = dff[(dff['Client name'].isin(receiver)) & (dff['Receiver latitude'].isin(
            receiver_lat)) & dff['Receiver longitude'].isin(receiver_lon)]
    return dff


def zoom_center(
        lons: tuple = None,
        lats: tuple = None,
        projection: str = 'mercator',
        width_to_height: float = 1.0):

    maxlon, minlon = max(lons), min(lons)
    maxlat, minlat = max(lats), min(lats)
    center = {
        'lon': round((maxlon + minlon) / 2, 6),
        'lat': round((maxlat + minlat) / 2, 6)
    }

    # longitudinal range by zoom level (20 to 1)
    # in degrees, if centered at equator
    lon_zoom_range = np.array([
        0.0007, 0.0014, 0.003, 0.006, 0.012, 0.024, 0.048, 0.096,
        0.192, 0.3712, 0.768, 1.536, 3.072, 6.144, 11.8784, 23.7568,
        47.5136, 98.304, 190.0544, 360.0
    ])

    if projection == 'mercator':
        margin = 1.2
        height = (maxlat - minlat) * margin * width_to_height
        width = (maxlon - minlon) * margin
        lon_zoom = np.interp(width, lon_zoom_range, range(20, 0, -1))
        lat_zoom = np.interp(height, lon_zoom_range, range(20, 0, -1))
        zoom = round(min(lon_zoom, lat_zoom), 2)
    else:
        raise NotImplementedError(
            f'{projection} projection is not implemented'
        )

    return zoom, center


def plot_map(df, shipper='all', shipper_lat=50, shipper_long=2):
    zoom, center = zoom_center(pd.concat([df['Receiver longitude'], df['Shipper longitude']]), pd.concat(
        [df['Receiver latitude'], df['Shipper latitude']]))
    fig = go.Figure()
    if shipper == 'all':
        # No shipper selected
        for i in df['DC name'].unique():
            df_plot = df[df['DC name'] == i]
            fig.add_trace(go.Scattermapbox(
                lat=df_plot["Receiver latitude"], lon=df_plot["Receiver longitude"], name=i,
                customdata=df[["Client name", "Distance (km)", "Sender weight (kg)"]],
                hovertemplate='''<br>Client: %{customdata[0]}<br>Distance: %{customdata[1]:,.0f} km<br>Weight: %{customdata[2]:,.0f} kg<br><extra></extra>'''))
        fig.update_layout(title=f'Map with clients per DC')
    else:
        # Shipper selected
        zoom, center = zoom_center(pd.concat([df['Receiver longitude'], df['Shipper longitude']]), pd.concat(
            [df['Receiver latitude'], df['Shipper latitude']]))
        fig.add_trace(go.Scattermapbox(
            lat=df["Receiver latitude"], lon=df["Receiver longitude"], name="Clients", marker={'color': '#009530', 'size': 8},
            customdata=df[["Client name", "Distance (km)", "Sender weight (kg)"]],
            hovertemplate='''<br>Client: %{customdata[0]}<br>Distance: %{customdata[1]:,.0f} km<br>Weight: %{customdata[2]:,.2f} kg<br><extra></extra>'''))
        fig.add_trace(
            go.Scattermapbox(
                lat=[shipper_lat],
                lon=[shipper_long],
                name=f'{shipper}',
                marker={
                    'color': '#B10043',
                    'size': 12}))
        fig.update_layout(title=f'Map with clients of {shipper}')
    fig.update_layout(mapbox_style="open-street-map")
    if shipper == 'all':
        fig.update_layout(
            margin={
                "r": 0,
                "t": 40,
                "l": 0,
                "b": 40},
            mapbox={
                'zoom': 3,
                "center": {
                    'lat': df['Shipper latitude'].mean(),
                    'lon': df['Shipper longitude'].mean()}})
    else:
        fig.update_layout(
            margin={
                "r": 0,
                "t": 40,
                "l": 0,
                "b": 40},
            mapbox={
                'zoom': 4,
                "center": {
                    'lat': df['Shipper latitude'].mean(),
                    'lon': df['Shipper longitude'].mean()}})
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01))
    return fig


def prepare_data_bar_plot(dff, selected_rows_indices):
    dff['Pickup date'] = pd.to_datetime(dff['Pickup date'])

    if (selected_rows_indices is None) or (selected_rows_indices == []):
        dff['Pickup date'] = dff['Pickup date'].dt.date
        dff = dff.groupby(['Pickup date', 'Carrier name']).agg({
            'Sender weight (kg)': sum,
            'Volume (m3)': sum}).reset_index()
    else:
        dff = dff.groupby(['Pickup date', 'Shipment id', 'Carrier name']).agg({
            'Client name': lambda tdf: tdf.unique(),
            'Sender weight (kg)': sum,
            'Volume (m3)': sum}).reset_index()

    dff['Pickup date'] = pd.to_datetime(dff['Pickup date'])
    return dff


def plot_bar_client(df, month):
    df['Pickup date'] = pd.to_datetime(df["Pickup date"])
    df['Pickup time'] = df["Pickup date"].dt.time
    df['Pickup date'] = df["Pickup date"].dt.date
    fig = go.Figure()
    for i in df['Carrier name'].unique():
        df_plot = df[df['Carrier name'] == i]
        fig.add_trace(go.Bar(
            x=df_plot["Pickup date"],
            y=df_plot["Sender weight (kg)"],
            name=i,
            xperiodalignment="middle",
            customdata=df_plot[["Pickup time", "Sender weight (kg)", "Volume (m3)", 'Shipment id']],
            hovertemplate='<br>%{x}Time: %{customdata[0]}<br>Weight: %{customdata[1]:,.3f}<br>Volume: %{customdata[2]:,.3f}<br>%{customdata[3]}<br><extra></extra>'
        ))
    if month is not None:
        fig.update_layout(xaxis_range=[dt.datetime(2022, month, 1),
                                       dt.datetime(2022, month + 1, 1)])
        fig.update_xaxes(dtick=86400000.0)
    else:
        fig.update_layout(xaxis_range=[dt.datetime(2022, 1, 1),
                                       dt.datetime(2022, 12, 31)])
    fig.update_layout(barmode='relative')
    return fig


def plot_px_bar_client(df, month):
    df['Pickup date'] = pd.to_datetime(df["Pickup date"])
    df['Pickup time'] = df["Pickup date"].dt.time
    df['Pickup date'] = df["Pickup date"].dt.date
    fig = px.bar(
        df,
        x='Pickup date',
        y="Sender weight (kg)",
        color="Carrier name",
        barmode="stack")
    if month is not None:
        fig.update_xaxes(dtick=86400000.0)
    else:
        fig.update_xaxes(dtick='M1')
    fig.update_layout(barmode='relative')
    fig.update_traces(customdata=df[["Pickup time", "Sender weight (kg)", "Volume (m3)", 'Shipment id']],
                      hovertemplate='<br>%{x}<br>Time: %{customdata[0]}<br>Weight: %{customdata[1]:,.3f}<br>Volume: %{customdata[2]:,.3f}<br>%{customdata[3]}<br><extra></extra>')
    #fig.update_layout(legend=dict(orientation="h",yanchor="bottom", y=1.02,xanchor="right",bordercolor="grey",borderwidth=1,x=1))
    return fig


def plot_bar_no_client(df, month):
    fig = go.Figure()
    for i in df['Carrier name'].unique():
        df_plot = df[df['Carrier name'] == i]
        fig.add_trace(go.Bar(
            x=df_plot["Pickup date"],
            y=df_plot["Sender weight (kg)"],
            name=i,
            customdata=df_plot[["Sender weight (kg)", "Volume (m3)"]],
            hovertemplate='<br>%{x}<br>Weight: %{customdata[0]:,.2f} kg<br>Volume: %{customdata[1]:,.3f} m3<br><extra></extra>'
        ))
    if month is not None:
        fig.update_layout(xaxis_range=[dt.datetime(2022, month, 1),
                                       dt.datetime(2022, month + 1, 1)])
        fig.update_xaxes(dtick=86400000.0)
    else:
        fig.update_layout(xaxis_range=[dt.datetime(2022, 1, 1),
                                       dt.datetime(2022, 12, 31)])
    fig.update_layout(barmode='relative')
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01))
    return fig


def plot_px_bar_no_client(df, month, shipper):
    if shipper is None:
        df = df.groupby(['Pickup date'])[
            ['Sender weight (kg)', 'Volume (m3)']].sum().reset_index()
        fig = px.bar(
            df,
            x='Pickup date',
            y="Sender weight (kg)",
            barmode="stack")
        title = f"Shipments for all DC's"
    else:
        fig = px.bar(
            df,
            x='Pickup date',
            y="Sender weight (kg)",
            color="Carrier name",
            barmode="stack")
        title = f'Shipments for {shipper}'
    if month is not None:
        fig.update_xaxes(dtick=86400000.0)
    else:
        fig.update_xaxes(dtick='M1')
    fig.update_layout(barmode='relative')
    fig.update_traces(customdata=df[["Sender weight (kg)", "Volume (m3)"]],
                      hovertemplate='<br>%{x}<br>Weight: %{customdata[0]:,.2f} kg<br>Volume: %{customdata[1]:,.3f} m3<br><extra></extra>')
    fig.update_layout(title=title)
    #fig.update_layout(legend=dict(orientation="h",yanchor="bottom", y=1.02,xanchor="right",bordercolor="grey",borderwidth=1,x=1))
    return fig

# callbacks


@app.callback(
    Output('dropdown-shipper', 'options'),
    Output('dropdown-shipper', 'value'),
    Input('url', 'pathname'),
)
def shipper_input(_):
    logger.info(df['DC name'].unique())
    shippers = [{"label": value, "value": value}
                for value in df['DC name'].unique()]
    default_shipper = df['DC name'].unique()[0]
    return shippers, default_shipper


@app.callback(
    Output('dropdown-month', 'options'),
    Output('dropdown-month', 'value'),
    Input('url', 'pathname'),
)
def month_input(_):
    months = [{'label': calendar.month_name[value], 'value': value}
              for value in df['Pickup date'].dt.month.unique()]
    default_month = df['Pickup date'].dt.month.unique()[0]
    return months, default_month


@app.callback(
    Output('table-shipments-grouped', 'columns'),
    Input('url', 'pathname'),
)
def table_shipments_columns(_):
    format_int = {'locale': {}, 'nully': '',
                  'prefix': None, 'specifier': ',.0f'}
    format_float = {'locale': {}, 'nully': '',
                    'prefix': None, 'specifier': ',.2f'}

    columns = [
        dict(
            id='Client name',
            name='Client name'),
        dict(
            id='Distance (km)',
            name='Distance (km)',
            type='numeric',
            format=format_float),
        dict(
            id='Sender weight (kg)',
            name='Sender weight (kg)',
            type='numeric',
            format=format_float),
        dict(
            id='Number of shippings',
            name='Number of shippings',
            type='numeric',
            format=format_int),
        dict(
            id='Co2 emissions (g)',
            name='Co2 emissions (g)',
            type='numeric',
            format=format_int),
        dict(
            id='Co2 BEV (g)',
            name='Co2 BEV (g)',
            type='numeric',
            format=format_int)]
    return columns


@app.callback(
    Output('table-shipments-grouped', 'selected_rows'),
    Input('table-shipments-grouped', "filter_query"),
    Input('table-shipments-grouped', 'sort_by'),
    Input('dropdown-shipper', "value"),
    Input('dropdown-month', "value")
)
def reset_selected_rows(filter, sort_by, shipper, month):
    selected_rows = []
    return selected_rows


@app.callback(
    Output('table-shipments-client', 'columns'),
    Input('url', 'pathname'),
)
def table_client_columns(_):
    format_int = {'locale': {}, 'nully': '',
                  'prefix': None, 'specifier': ',.0f'}
    format_float = {'locale': {}, 'nully': '',
                    'prefix': None, 'specifier': ',.2f'}

    columns = [
        dict(
            id='Client name',
            name='Client name'),
        dict(
            id='Pickup date',
            name='Pickup date'),
        dict(
            id='DC name',
            name='DC name)'),
        dict(
            id='Sender weight (kg)',
            name='Sender weight (kg)',
            type='numeric',
            format=format_float),
        dict(
            id='Volume (m3)',
            name='Volume (m3)',
            type='numeric',
            format=format_float)]
    return columns


@app.callback(
    Output('table-shipments-grouped', "data"),
    Input('table-shipments-grouped', "page_current"),
    Input('table-shipments-grouped', "page_size"),
    Input('table-shipments-grouped', "filter_query"),
    Input('table-shipments-grouped', 'sort_by'),
    Input('dropdown-shipper', "value"),
    Input('dropdown-month', "value")
)
def apply_filter_to_datatable(
        page_current,
        page_size,
        filter,
        sort_by,
        shipper,
        month):
    dff = df

    # apply month and shipper filter
    dff = apply_month_shipper(dff, month, shipper)

    # group by longitude and latitude
    dff = group_by_client(group_by_client_shipment(dff))

    # apply filters
    dff = apply_filters(dff, filter)

    # sorting
    if len(sort_by):
        dff = dff.sort_values(
            sort_by[0]['column_id'],
            ascending=sort_by[0]['direction'] == 'asc',
            inplace=False
        )
    else:
        # No sort is applied
        dff = dff

    return dff.iloc[page_current *
                    page_size:(page_current + 1) * page_size].to_dict('records')


@app.callback(
    Output('output-emissions', "children"),
    Output('output-emissions-savings', "children"),
    Output('output-emissions-savings-share', "children"),
    Input('dropdown-shipper', "value"),
    Input('dropdown-month', "value"),
    Input('input-distance-bev', "value"),
    Input('table-shipments-grouped', "filter_query"),
    Input('table-shipments-grouped', "derived_virtual_selected_rows"),
    State('table-shipments-grouped', 'data'),
)
def get_co2_emissions(
        shipper,
        month,
        distance,
        filter,
        selected_rows_indices,
        rows):
    # format input
    dff = df
    distance = pd.to_numeric(distance)

    # apply month and shipper filter
    dff = apply_month_shipper(dff, month, shipper)

    # group by longitude and latitude
    dff = group_by_client(group_by_client_shipment(dff))

    # apply filters
    dff = apply_filters(dff, filter)

    dff = apply_selected_rows_indices(dff, rows, selected_rows_indices)

    # Co2 emissions with diesel
    co2_emissions = f"{dff['Co2 emissions (g)'].sum()/1000:,.2f} kg Co2"

    # Co2 emissions with bev
    dff['Co2 emissions new'] = np.where(
        dff['Distance (km)'] < distance,
        dff['Co2 BEV (g)'],
        dff['Co2 emissions (g)'])
    absolute_emissions_savings = f"{((dff['Co2 emissions (g)'].sum()-dff['Co2 emissions new'].sum())/1000):,.2f} kg Co2"
    relative_emissions_savings = f"{((dff['Co2 emissions (g)'].sum()-dff['Co2 emissions new'].sum())/dff['Co2 emissions (g)'].sum())*100:,.2f} %"
    return co2_emissions, absolute_emissions_savings, relative_emissions_savings


@app.callback(
    Output("download-csv", "data"),
    Input("button-save-csv", "n_clicks"),
    State('table-shipments-grouped', "filter_query"),
    State('dropdown-shipper', "value"),
    State('dropdown-month', "value")
)
def download_as_csv(n_clicks, filter, shipper, month):
    dff = df

    # apply month and shipper filter
    dff = apply_month_shipper(dff, month, shipper)

    # group by longitude and latitude
    dff = group_by_client(group_by_client_shipment(dff))

    # apply filters
    dff = apply_filters(dff, filter)

    df_download = dff.drop(['Receiver longitude', 'Receiver latitude'], axis=1)

    if not n_clicks:
        raise PreventUpdate
    download_buffer = io.StringIO()
    df_download.to_csv(download_buffer, index=False)
    download_buffer.seek(0)

    # format file_name
    if month is None:
        file_name = f'2022_clientlist_{shipper}.csv'
    else:
        file_name = f'{month}2022_clientlist_{shipper}.csv'

    return dict(content=download_buffer.getvalue(), filename=file_name)


@app.callback(
    Output('plot-map', "figure"),
    Output('plot-bar-shipments', "figure"),
    Output('table-shipments-client', "data"),
    Input('table-shipments-grouped', "derived_virtual_selected_rows"),
    State('table-shipments-grouped', 'data'),
    Input('dropdown-shipper', "value"),
    Input('dropdown-month', "value"),
    Input('table-shipments-grouped', "filter_query")
)
def create_graphs(selected_rows_indices, rows, shipper, month, filter):
    dff = df
    dff['Pickup date'] = pd.to_datetime(dff['Pickup date'])

    dff = apply_month_shipper(dff, month, shipper)
    dff = apply_filters(dff, filter)
    dff = apply_selected_rows_indices(dff, rows, selected_rows_indices)
    dff['Pickup date'] = pd.to_datetime(dff['Pickup date'])

    # plot map
    if shipper is None:
        fig_map = plot_map(dff)
    else:
        shipper_lat = dff["Shipper latitude"].iloc[0]
        shipper_long = dff["Shipper longitude"].iloc[0]
        fig_map = plot_map(dff, shipper, shipper_lat, shipper_long)

    # plot bar
    df_bar_plot = prepare_data_bar_plot(dff, selected_rows_indices)
    if (selected_rows_indices is None) or (selected_rows_indices == []):
        fig_bar = plot_px_bar_no_client(df_bar_plot, month, shipper)
    else:
        fig_bar = plot_px_bar_client(df_bar_plot, month)
        fig_bar.update_layout(title='')
        df_select = pd.DataFrame(rows)
        receiver = df_select['Client name'].values[selected_rows_indices]
        fig_bar.update_layout(title=f'Shipments for client(s) {receiver}')
    return fig_map, fig_bar, dff.to_dict('records')


@app.callback(
    Output("collapse", "is_open"),
    [Input("button-table-shipments-client", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
