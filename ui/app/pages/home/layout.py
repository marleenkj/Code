from dash import html, dcc
import dash_bootstrap_components as dbc

ROW_STYLE = {"padding": "1rem 1rem"}
FONT_STYLE = {"font-family": "inherit"}
COLOR_SE = {"color": "#36C746"}

card1 = dbc.Card(
    [
        #dbc.CardImg(src="/static/images/placeholder286x180.png", top=True),
        dbc.CardBody(
            [
                html.H6(
                    "Individual Client Analysis",
                    className="card-title",
                    style={
                        "height": "2rem"}),
                html.P(
                    """
                    To analyze the impact of combined railroad freight transportation by
                    examining each client individually and considering only direct delivery from the DC to the client.
                    """,
                    className="card-text", style={"height": "12rem"}
                ),
                dbc.CardFooter(
                    dbc.CardLink(
                        "Go to analysis",
                        href="http://127.0.0.1:5000/Client_analysis",
                        className="card-text text-muted")),
            ]
        ),
    ], className="w-100 mb-5", color="light"
)

card2 = dbc.Card(
    [
        #dbc.CardImg(src="/static/images/placeholder286x180.png", top=True),
        dbc.CardBody(
            [
                html.H6(
                    "Transport Plan Routing Analysis",
                    className="card-title",
                    style={
                        "height": "2rem"}),
                html.P(
                    """
                    A more realistic analysis for a whole transport plan where the goods are distributed from a central depot to geographically scattered customers simultaneously
                    """,
                    className="card-text", style={"height": "12rem"}
                ),
                dbc.CardFooter(
                    dbc.CardLink(
                        "Go to analysis",
                        href="http://127.0.0.1:5000/Routing_analysis",
                        className="card-text text-muted")),
            ]
        ),
    ], className="w-100 mb-5", color="light"
)

card3 = dbc.Card(
    [
        #dbc.CardImg(src="/static/images/placeholder286x180.png", top=True),
        dbc.CardBody(
            [
                html.H6(
                    "Railroad Freight Systems Analysis",
                    className="card-title",
                    style={
                        "height": "2rem"}),
                html.P(
                    """
                    To study the change in impact when providing more flexibility for the length of the road leg.
                    """,
                    className="card-text", style={"height": "12rem"}
                ),
                dbc.CardFooter(
                    dbc.CardLink(
                        "Go to analysis",
                        href="http://127.0.0.1:5000/System_analysis",
                        className="card-text text-muted")),
            ]
        ),
    ], className="w-100 mb-5", color="light"
)

cards = dbc.CardGroup([card1, card2, card3])

card0 = dbc.Card(
    [
        #dbc.CardImg(src="/static/images/placeholder286x180.png", top=True),
        dbc.CardBody(
            [
                html.H6(
                    "Summary of results",
                    className="card-title",
                    style={
                        "height": "2rem"}),
                html.P(
                    """
                    To get overall results of the study
                    """,
                    className="card-text", style={"height": "12rem"}

                ),
                dbc.CardFooter(
                    dbc.CardLink(
                        "Go to overview",
                        href="http://127.0.0.1:5000/Dataset",
                        className="card-text text-muted")),
            ]
        ),
    ], className="w-100 mb-5", color="light"
)

layout = dbc.Container([dcc.Markdown(
    f'''
    ## Sustainable Assessment of Combined Railroad Freight Transportation
    '''),
    dbc.Row([
        dbc.Col(card0, width={"size": 3}, style=ROW_STYLE),
        dbc.Col(cards, width={"size": 9}, style=ROW_STYLE),
        # dbc.Col(card2,  width={"size": 3}, style = ROW_STYLE),
        # dbc.Col(card3,  width={"size": 3}, style = ROW_STYLE),
    ], style=ROW_STYLE, className="h-25",)
])
