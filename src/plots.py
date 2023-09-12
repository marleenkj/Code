import seaborn as sns
from src.distance import get_waypoints_osrm
from src.data_matrix import create_dict_points
import shapely.geometry
import pandas as pd
import geopandas as gpd
from loguru import logger
import json
import plotly.express as px
import plotly.graph_objects as go
import itertools
import sys
import plotly.io as pio
sys.path.append('..')
color = sns.color_palette().as_hex()

pio.templates["my_modification"] = go.layout.Template(
    layout=dict(
        font={"size": 15, "family": "arial"},
        # colorway = ["#57B38E", "#50A382", "#468B6F", "#3B705A", "#305847",
        # "#2B4C3E"],
        colorway=[px.colors.sequential.Greys[i] for i in [2, 3, 4, 5]],
        # colorway = ["#626469"],
        mapbox_style="carto-positron",
        xaxis=dict(
            tickfont={
                "size": 15, "family": "arial"}, titlefont={
                "size": 15, "family": "arial"}),
        yaxis=dict(
            tickfont={
                "size": 15, "family": "arial"}, titlefont={
                "size": 15, "family": "arial"})
    )
)
template = "plotly_white+my_modification"
pio.templates.default = template

legend_layout = dict(
    #orientation = "h"
    yanchor="top",
    y=0.99,
    xanchor="right",
    x=0.99,
)


def graph_solution_direct(
        x,
        dict_points,
        dict_terminals,
        df_distance_matrix,
        path_plot=False):
    dc = x["dc"]
    logger.info(dc)
    client = x["client"]
    logger.info(client)
    terminal = x["terminal allocation"]
    logger.info(terminal)
    closest_dct = df_distance_matrix[dc].loc[dict_terminals.keys()].idxmin()
    # lon/lat [dict_points[node][::-1] for node in routes_terminal[j]]
    dc_coords = [dict_points[dc][1], dict_points[dc][0]]
    c_coords = [dict_points[client][1], dict_points[client][0]]
    dct_coords = [dict_points[closest_dct][1], dict_points[closest_dct][0]]
    t_coords = [dict_points[terminal][1], dict_points[terminal][0]]
    logger.info(t_coords)

    fig = go.Figure()
    waypoints = get_waypoints_osrm([dc_coords, c_coords])[
        "geometry"]["coordinates"]
    lat = [coords[1] for coords in waypoints]
    lon = [coords[0] for coords in waypoints]
    fig.add_trace(
        go.Scattermapbox(
            lat=lat,
            lon=lon,
            mode='lines',
            name="road",
            marker={
                'size': 10}))
    if terminal != closest_dct:
        # Add all routes
        waypoints = get_waypoints_osrm([dc_coords, dct_coords])[
            "geometry"]["coordinates"]
        lat = [coords[1] for coords in waypoints]
        lon = [coords[0] for coords in waypoints]
        waypoints = get_waypoints_osrm([t_coords, c_coords])[
            "geometry"]["coordinates"]
        lat = lat + [coords[1] for coords in waypoints]
        lon = lon + [coords[0] for coords in waypoints]
        fig.add_trace(
            go.Scattermapbox(
                lat=lat,
                lon=lon,
                mode='lines',
                name="railroad",
                marker={
                    'size': 10}))
    else:
        pass
    fig.add_trace(
        go.Scattermapbox(
            lat=[
                dc_coords[1]], lon=[
                dc_coords[0]], mode='markers', name=dc, marker={
                    'size': 10}))
    fig.add_trace(
        go.Scattermapbox(
            lat=[
                c_coords[1]], lon=[
                c_coords[0]], mode='markers', name=client, marker={
                    'size': 10}))
    fig.add_trace(
        go.Scattermapbox(
            lat=[
                t_coords[1]],
            lon=[
                t_coords[0]],
            mode='markers',
            name=terminal,
            marker={
                'size': 10}))
    fig.add_trace(
        go.Scattermapbox(
            lat=[
                dct_coords[1]],
            lon=[
                dct_coords[0]],
            mode='markers',
            name=closest_dct,
            marker={
                'size': 10}))
    fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 40}, mapbox={
                      'zoom': 4, "center": {'lat': 45, 'lon': 0}})
    fig.update_layout(mapbox_style="open-street-map")
    if not path_plot:
        return fig
    else:
        fig.write_html(path_plot, auto_open=False)


def graph_road(df, list_routes, path_plot=False):
    #dict_routes = dict_results["routes road"]
    dict_points = create_dict_points(
        df, "Shipper name", "Shipper latitude", "Shipper longitude")
    dict_points.update(create_dict_points(
        df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    dc = list(dict_points.keys())[0]
    fig = go.Figure()

    # Add all routes
    for i in range(len(list_routes)):
        if list_routes[i]:
            waypoints = get_waypoints_osrm(
                [dict_points[node][::-1] for node in list_routes[i]])["geometry"]["coordinates"]
            lat = [coords[1] for coords in waypoints]
            lon = [coords[0] for coords in waypoints]
            fig.add_trace(go.Scattermapbox(
                lat=lat, lon=lon, name=f"Truck {i+1}",
                mode='lines', marker={'size': 10}))

    # Add clients
    list_clients = pd.Series(itertools.chain(
        *list_routes)).drop_duplicates()[1:]
    fig.add_trace(
        go.Scattermapbox(
            lat=[
                dict_points[i][0] for i in list_clients],
            lon=[
                dict_points[i][1] for i in list_clients],
            name="Clients",
            mode='markers',
            customdata=list_clients,
            hovertemplate='''<br>%{customdata}<br>''',
            marker={
                'size': 10,
                "color": "orange"}))

    # Add DC
    fig.add_trace(
        go.Scattermapbox(
            lat=[
                list(
                    dict_points.values())[0][0]],
            lon=[
                list(
                    dict_points.values())[0][1]],
            mode='markers',
            name="DC",
            marker={
                'size': 10,
                'color': "red"}))

    fig.update_layout(
        legend=legend_layout,
        margin={"r": 0, "t": 40, "l": 0, "b": 40},
        mapbox={'zoom': 4, "center": {'lat': df["Receiver latitude"].mean(),
                                      'lon': df["Receiver longitude"].mean()}})
    fig.update_layout(mapbox_style="open-street-map")
    if not path_plot:
        return fig
    else:
        fig.write_html(path_plot, auto_open=False)


def graph_solution(
        df,
        dict_routes,
        terminal_allocation,
        dict_terminals,
        closest_dct,
        path_plot=False):
    #dict_routes = dict_results["routes railroad"]
    dict_points = create_dict_points(
        df, "Shipper name", "Shipper latitude", "Shipper longitude")
    dict_points.update(create_dict_points(
        df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    dict_points.update(dict_terminals)
    dc = list(dict_points.keys())[0]

    fig = go.Figure()
    # Add all routes
    for i in dict_routes.keys():
        routes_terminal = dict_routes[i]
        for j in range(len(routes_terminal)):
            if routes_terminal[j]:
                waypoints = get_waypoints_osrm(
                    [dict_points[node][::-1] for node in routes_terminal[j]])["geometry"]["coordinates"]
                lat = [coords[1] for coords in waypoints]
                lon = [coords[0] for coords in waypoints]
                if i != closest_dct:
                    waypoints = get_waypoints_osrm(
                        [dict_points[dc][::-1], dict_points[closest_dct][::-1]])["geometry"]["coordinates"]
                    lat = [coords[1] for coords in waypoints] + lat
                    lon = [coords[0] for coords in waypoints] + lon
                    fig.add_trace(go.Scattermapbox(
                        lat=lat, lon=lon, name=f"Container {j+1} over {routes_terminal[j][0]}", mode='lines',
                        marker={'size': 10, "color": color[list(dict_terminals.keys()).index(i)]}))
                else:
                    fig.add_trace(go.Scattermapbox(
                        lat=lat, lon=lon, name=f"Truck {j+1} from {routes_terminal[j][0]}", mode='lines',
                        marker={'size': 10, "color": color[list(dict_terminals.keys()).index(i)]}))

    # Add clients
    list_clients = pd.Series(itertools.chain(
        *terminal_allocation)).drop_duplicates()

    fig.add_trace(
        go.Scattermapbox(
            lat=[
                dict_points[i][0] for i in list_clients],
            lon=[
                dict_points[i][1] for i in list_clients],
            name="Clients",
            mode='markers',
            customdata=list_clients,
            hovertemplate='''<br>%{customdata}<br>''',
            marker={
                'size': 10,
                "color": "orange"}))

    # add DC
    fig.add_trace(
        go.Scattermapbox(
            lat=[
                list(
                    dict_points.values())[0][0]],
            lon=[
                list(
                    dict_points.values())[0][1]],
            mode='markers',
            name="DC",
            marker={
                'size': 10,
                'color': "red"}))

    # Add relevant terminals
    for i in dict_routes.keys():
        if dict_routes[i] != [[]]:
            fig.add_trace(
                go.Scattermapbox(
                    lat=[
                        dict_terminals[i][0]],
                    lon=[
                        dict_terminals[i][1]],
                    name=f"Terminal {i[-1]}",
                    mode='markers',
                    marker={
                        'size': 10,
                        "color": "blue"}))
    fig.update_layout(
        legend=legend_layout,
        margin={
            "r": 0,
            "t": 40,
            "l": 0,
            "b": 40},
        mapbox={
            'zoom': 4,
            "center": {
                'lat': df["Receiver latitude"].mean(),
                'lon': df["Receiver longitude"].mean()}})
    fig.update_layout(mapbox_style="open-street-map")
    if not path_plot:
        return fig
    else:
        fig.write_html(path_plot, auto_open=False)


def graph_solution_with_radius(
        df,
        dict_routes,
        terminal_allocation,
        dict_terminals,
        closest_dct,
        list_terminals,
        path_plot=False):
    #dict_routes = dict_results["routes railroad"]
    dict_points = create_dict_points(
        df, "Shipper name", "Shipper latitude", "Shipper longitude")
    dict_points.update(create_dict_points(
        df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    dict_points.update(dict_terminals)
    dc = list(dict_points.keys())[0]
    list_dict_circle = [{
        "source": json.loads(
            poi_poly(None, poi={"Latitude": dict_terminals[f"T{i}"][0], "Longitude": dict_terminals[f"T{i}"][1]},
                     radius=150000).to_json()),
        "below": "traces",
        "type": "fill",
        "color": "green",
        "line": {"width": 1.5},
        "opacity": 0.2
        # "fillcolor": "red"
    } for i in list_terminals]

    fig = go.Figure()
    # Add all routes
    for i in dict_routes.keys():
        routes_terminal = dict_routes[i]
        for j in range(len(routes_terminal)):
            if routes_terminal[j]:
                waypoints = get_waypoints_osrm(
                    [dict_points[node][::-1] for node in routes_terminal[j]])["geometry"]["coordinates"]
                lat = [coords[1] for coords in waypoints]
                lon = [coords[0] for coords in waypoints]
                if i != closest_dct:
                    waypoints = get_waypoints_osrm(
                        [dict_points[dc][::-1], dict_points[closest_dct][::-1]])["geometry"]["coordinates"]
                    lat = [coords[1] for coords in waypoints] + lat
                    lon = [coords[0] for coords in waypoints] + lon
                    fig.add_trace(go.Scattermapbox(
                        lat=lat, lon=lon, name=f"Railroad {j+1} over {routes_terminal[j][0]}", mode='lines',
                        marker={'size': 10, "color": color[list(dict_terminals.keys()).index(i)]}))
                else:
                    fig.add_trace(go.Scattermapbox(
                        lat=lat, lon=lon, name=f"Truck {j+1} directly from {routes_terminal[j][0]}", mode='lines',
                        marker={'size': 10, "color": color[list(dict_terminals.keys()).index(i)]}))

    # Add clients
    list_clients = pd.Series(itertools.chain(
        *terminal_allocation)).drop_duplicates()

    fig.add_trace(
        go.Scattermapbox(
            lat=[
                dict_points[i][0] for i in list_clients],
            lon=[
                dict_points[i][1] for i in list_clients],
            name="Clients",
            mode='markers',
            customdata=list_clients,
            hovertemplate='''<br>%{customdata}<br>''',
            marker={
                'size': 10,
                "color": "orange"}))

    # add DC
    fig.add_trace(
        go.Scattermapbox(
            lat=[
                list(
                    dict_points.values())[0][0]],
            lon=[
                list(
                    dict_points.values())[0][1]],
            mode='markers',
            name="DC",
            marker={
                'size': 10,
                'color': "red"}))

    # Add relevant terminals
    for i in dict_routes.keys():
        if dict_routes[i] != [[]]:
            fig.add_trace(
                go.Scattermapbox(
                    lat=[
                        dict_terminals[i][0]], lon=[
                        dict_terminals[i][1]], name=i, mode='markers', marker={
                        'size': 10, "color": "blue"}))
    fig.update_layout(
        legend=legend_layout,
        margin={
            "r": 0,
            "t": 40,
            "l": 0,
            "b": 40},
        mapbox={
            'zoom': 4,
            "center": {
                'lat': df["Receiver latitude"].mean(),
                'lon': df["Receiver longitude"].mean()},
            "layers": list_dict_circle})
    fig.update_layout(mapbox_style="open-street-map")
    if not path_plot:
        return fig
    else:
        fig.write_html(path_plot, auto_open=False)


# Plot:
# Graph with radius


def poi_poly(
    df,
    radius=10 ** 5,
    poi={"Longitude": 0.06665166467428207, "Latitude": 51.19034957885742},
    lon_col="Longitude",
    lat_col="Latitude",
    include_radius_poly=False,
):

    # generate a geopandas data frame of the POI
    gdfpoi = gpd.GeoDataFrame(
        geometry=[shapely.geometry.Point(poi["Longitude"], poi["Latitude"])],
        crs="EPSG:4326",
    )
    # extend point to radius defined (a polygon).  Use UTM so that distances
    # work, then back to WSG84
    gdfpoi = (
        gdfpoi.to_crs(gdfpoi.estimate_utm_crs())
        .geometry.buffer(radius)
        .to_crs("EPSG:4326")
    )

    # create a geopandas data frame of all the points / markers
    if df is not None:
        gdf = gpd.GeoDataFrame(
            geometry=df.loc[:, ["Longitude", "Latitude"]]
            .dropna()
            .apply(
                lambda r: shapely.geometry.Point(r["Longitude"], r["Latitude"]), axis=1
            )
            .values,
            crs="EPSG:4326",
        )
    else:
        gdf = gpd.GeoDataFrame(geometry=gdfpoi)

    # create a polygon around the edges of the markers that are within POI
    # polygon
    return pd.concat(
        [
            gpd.GeoDataFrame(
                geometry=[
                    gpd.sjoin(
                        gdf, gpd.GeoDataFrame(geometry=gdfpoi), how="inner"
                    ).unary_union.convex_hull
                ]
            ),
            gpd.GeoDataFrame(geometry=gdfpoi if include_radius_poly else None),
        ]
    )


def graph_solution_with_radius_old(
        df,
        dict_results,
        dict_terminals,
        closest_dct):
    dict_routes = dict_results["routes railroad"]
    df = df[df["Receiver name"].isin(
        list(itertools.chain(*dict_results["terminal allocation"])))]
    dict_points = create_dict_points(
        df, "Shipper name", "Shipper latitude", "Shipper longitude")
    dict_points.update(create_dict_points(
        df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    dict_points.update(dict_terminals)
    dc = list(dict_points.keys())[0]

    fig = go.Figure()
    # für alle terminals
    dc = list(dict_points.keys())[0]
    # for i in dict_routes:
    for i in ["T4", "T6"]:
        routes_terminal = dict_routes[i]
        for j in range(len(routes_terminal)):
            if routes_terminal[j]:
                waypoints = get_waypoints_osrm(
                    [dict_points[node][::-1] for node in routes_terminal[j]])["geometry"]["coordinates"]
                lat = [coords[1] for coords in waypoints]
                lon = [coords[0] for coords in waypoints]
                if i != closest_dct:
                    waypoints = get_waypoints_osrm(
                        [dict_points[dc][::-1], dict_points[closest_dct][::-1]])["geometry"]["coordinates"]
                    lat = [coords[1] for coords in waypoints] + lat
                    lon = [coords[0] for coords in waypoints] + lon
                    fig.add_trace(go.Scattermapbox(lat=lat,
                                                   lon=lon,
                                                   name=f"Railroad {j+1} over {routes_terminal[j][0]}",
                                                   mode='lines',
                                                   marker={'size': 10,
                                                           "color": color[list(dict_terminals.keys()).index(i)]}))
                else:
                    fig.add_trace(go.Scattermapbox(lat=lat,
                                                   lon=lon,
                                                   name=f"Truck {j+1} directly from {routes_terminal[j][0]}",
                                                   mode='lines',
                                                   marker={'size': 10,
                                                           "color": color[list(dict_terminals.keys()).index(i)]}))
    fig.add_trace(
        go.Scattermapbox(
            lat=[
                list(
                    dict_points.values())[0][0]],
            lon=[
                list(
                    dict_points.values())[0][1]],
            mode='markers',
            name="DC",
            marker={
                'size': 10,
                'color': "red"}))
    df = df[df["Receiver name"].isin(
        list(itertools.chain(*dict_results["terminal allocation"])))]
    dict_clients = create_dict_points(
        df, "Receiver name", "Receiver latitude", "Receiver longitude")
    fig.add_trace(
        go.Scattermapbox(
            lat=[
                i[0] for i in list(
                    dict_clients.values())], lon=[
                i[1] for i in list(
                    dict_clients.values())], name="Clients", mode='markers', customdata=list(
                dict_clients.keys()), hovertemplate='''<br>%{customdata}<br>''', marker={
                'size': 10, "color": "orange"}))
    for i in dict_routes.keys():
        if dict_routes[i] != [[]]:
            fig.add_trace(
                go.Scattermapbox(
                    lat=[
                        dict_terminals[i][0]], lon=[
                        dict_terminals[i][1]], name=i, mode='markers', marker={
                        'size': 10, "color": "blue"}))
            poi = {"Latitude": dict_terminals[i][0],
                   "Longitude": dict_terminals[i][1]}
            fig.update_layout(
                mapbox={
                    "style": "open-street-map",
                    "zoom": 4,
                    "center": {
                        "lat": poi["Latitude"],
                        "lon": poi["Longitude"]},
                    "layers": [
                        {
                            "source": json.loads(
                                poi_poly(
                                    None,
                                    poi=poi,
                                    radius=150000).to_json()),
                            "below": "traces",
                            "type": "line",
                            "color": "green",
                            "line": {
                                "width": 1.5},
                        }],
                })

    fig.update_layout(mapbox_style="open-street-map", height=800, width=800)
    fig.show()


def show_clients(df):
    df = df.groupby(['Shipper longitude',
                     'Shipper latitude',
                     'Receiver longitude',
                     'Receiver latitude',
                     'Receiver name',
                     'Shipper name']).sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(lat=df['Receiver latitude'].to_list(),
                                   lon=df['Receiver longitude'].to_list(),
                                   mode='markers',
                                   marker={'size': 8},
                                   name="Clients",
                                   customdata=df[["Receiver name",
                                                  "Sender weight (kg)"]],
                                   hovertemplate='''<br>%{customdata[0]}: %{customdata[1]}kg<br>'''))
    fig.update_layout(
        margin={
            "r": 0,
            "t": 40,
            "l": 0,
            "b": 40},
        mapbox={
            'zoom': 4,
            "center": {
                'lat': df["Receiver latitude"].mean(),
                'lon': df["Receiver longitude"].mean()}})
    fig.update_layout(
        mapbox_style="open-street-map",
        showlegend=False,
        height=500)
    fig.show()


def show_clients_dc(df, path_plot=False, name_dc="DC"):
    df = df.groupby(['Shipper longitude',
                     'Shipper latitude',
                     'Receiver longitude',
                     'Receiver latitude',
                     'Receiver name',
                     'Shipper name']).sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(lat=df['Receiver latitude'].to_list(), lon=df['Receiver longitude'].to_list(),
                                   mode='markers', marker={'size': 4, "color": "#626469"}, name="Clients",
                                   customdata=df[["Receiver name", "Sender weight (kg)"]],
                                   hovertemplate='''<br>%{customdata[0]}: %{customdata[1]}kg<br>%{lat},%{lon}<br><extra></extra>'''))
    color_dc = ["#42B4E6", "#C40D20"]
    for i in range(len(df["Shipper name"].unique())):
        dc_name = list(df["Shipper name"].unique())[i]
        df_temp = df[df["Shipper name"] == dc_name]
        fig.add_trace(
            go.Scattermapbox(
                lat=[
                    df_temp["Shipper latitude"].iloc[0]],
                lon=[
                    df_temp["Shipper longitude"].iloc[0]],
                mode='markers',
                marker={
                    'size': 12,
                    "color": color_dc[i]},
                name=dc_name))
    fig.update_layout(
        margin={
            "r": 0,
            "t": 40,
            "l": 0,
            "b": 40},
        mapbox={
            'zoom': 4,
            "center": {
                'lat': df["Receiver latitude"].mean(),
                'lon': df["Receiver longitude"].mean()}})
    fig.update_layout(legend=legend_layout)
    fig.update_layout(mapbox_style="carto-positron", height=600, width=500)
    if not path_plot:
        return fig
    else:
        fig.write_html(path_plot, auto_open=False)


def show_clients_per_dc(df, path_plot=False):
    df = df.groupby(['Shipper longitude',
                     'Shipper latitude',
                     'Receiver longitude',
                     'Receiver latitude',
                     'Receiver name',
                     'Shipper name']).sum().reset_index()
    fig = go.Figure()
    for i in list(df["Shipper name"].unique()):
        df_temp = df[(df["Shipper name"] == i)]
        fig.add_trace(go.Scattermapbox(lat=df_temp['Receiver latitude'].to_list(),
                                       lon=df_temp['Receiver longitude'].to_list(),
                                       mode='markers',
                                       marker={'size': 4},
                                       name=f"Clients of {i}",
                                       customdata=df_temp[["Receiver name",
                                                           "Sender weight (kg)"]],
                                       hovertemplate='''<br>%{customdata[0]}: %{customdata[1]}kg<br><extra></extra>'''))
    fig.update_layout(
        margin={
            "r": 0,
            "t": 40,
            "l": 0,
            "b": 40},
        mapbox={
            'zoom': 4,
            "center": {
                'lat': df["Receiver latitude"].mean(),
                'lon': df["Receiver longitude"].mean()}})
    fig.update_layout(legend=legend_layout)
    fig.update_layout(mapbox_style="carto-positron", height=500, width=500)
    if not path_plot:
        return fig
    else:
        fig.write_html(path_plot, auto_open=False)


def show_clients_per_dc_and_both(df, path_plot=False):
    df = df.groupby(['Shipper longitude',
                     'Shipper latitude',
                     'Receiver longitude',
                     'Receiver latitude',
                     'Receiver name',
                     'Shipper name']).sum().reset_index()
    df = df.merge(
        df.groupby(
            df["Receiver name"])["Shipper name"].aggregate(
            lambda x: len(
                (x.unique()))).reset_index().rename(
                    {
                        "Shipper name": "Shipper"},
            axis=1),
        on="Receiver name",
        how="left")
    fig = go.Figure()
    color_dc = ["#42B4E6", "#C40D20"]
    for i in list(df["Shipper name"].unique()):
        index_dc = list(df["Shipper name"].unique()).index(i)
        df_temp = df[(df["Shipper name"] == i) & (df["Shipper"] != 2)]
        fig.add_trace(go.Scattermapbox(lat=df_temp['Receiver latitude'].to_list(),
                                       lon=df_temp['Receiver longitude'].to_list(),
                                       mode='markers',
                                       marker={'size': 4,
                                               'color': color_dc[index_dc]},
                                       name=f"Clients of {i}",
                                       customdata=df_temp[["Receiver name",
                                                           "Sender weight (kg)"]],
                                       hovertemplate='''<br>%{customdata[0]}: %{customdata[1]}kg<br><extra></extra>'''))
    df_temp = df[(df["Shipper"] == 2)]
    fig.add_trace(go.Scattermapbox(lat=df_temp['Receiver latitude'].to_list(),
                                   lon=df_temp['Receiver longitude'].to_list(),
                                   mode='markers',
                                   marker={'size': 4,
                                           "color": "grey"},
                                   name=f"Clients of both",
                                   customdata=df_temp[["Receiver name",
                                                       "Sender weight (kg)"]],
                                   hovertemplate='''<br>%{customdata[0]}: %{customdata[1]}kg<br><extra></extra>'''))
    fig.update_layout(
        margin={
            "r": 0,
            "t": 40,
            "l": 0,
            "b": 40},
        mapbox={
            'zoom': 4,
            "center": {
                'lat': df["Receiver latitude"].mean(),
                'lon': df["Receiver longitude"].mean()}})
    fig.update_layout(legend=legend_layout)
    fig.update_layout(mapbox_style="carto-positron", height=600, width=500)
    if not path_plot:
        return fig
    else:
        fig.write_html(path_plot, auto_open=False)
