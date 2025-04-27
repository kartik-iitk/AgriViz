import dash
from dash import dcc, html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
import json
import os
from functools import lru_cache
import calendar
from collections import defaultdict
import datetime
from datetime import date
from pages.utils.utils import *
from pages.utils.node_graph import *
from pages.utils.wcloud import *
import time
import threading


# ---------- Load Time Series Data ----------
df2 = pd.read_parquet("../data/data_new.parquet")
all_states = df2["StateName"].unique()
df2["Date"] = df2["CreatedOn"].dt.date

with open("../data/query_to_cluster_id.json") as f:
    query_to_cluster = json.load(f)

with open("../data/cluster_labels.json") as f:
    cluster_to_queries = json.load(f)


# ---------- Choropleth Generator ----------
def create_map(state_clicked=None):
    df = load_data(df2)
    geojson_to_use = load_base_geojson()
    data_to_plot = df
    feature_id_key = "id"
    location_key = "state"

    if state_clicked:
        state_geojson = load_state_geojson(state_clicked)
        if state_geojson and state_geojson.get("features"):
            state_df = pd.DataFrame(
                [
                    {
                        "state": f.get("id"),
                        "value": int(len(df2[df2["DistrictName"] == f.get("id")])),
                    }
                    for i, f in enumerate(state_geojson["features"])
                ]
            )
            geojson_to_use = state_geojson
            data_to_plot = state_df
            feature_id_key = (
                "id" if "id" in state_geojson["features"][0] else "properties.DISTRICT"
            )
        else:
            # fallback: highlight selected state only
            base = load_base_geojson().get("features", [])
            filtered = [f for f in base if f.get("id") == state_clicked]
            geojson_to_use = {"type": "FeatureCollection", "features": filtered}
            data_to_plot = df[df["state"] == state_clicked] or pd.DataFrame(
                [{"state": state_clicked, "value": 0}]
            )

    if data_to_plot.empty or not geojson_to_use.get("features"):
        fig = px.choropleth()
        fig.update_layout(
            title_text="Map Data Unavailable", margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )
        return fig

    try:
        fig = px.choropleth(
            data_to_plot,
            geojson=geojson_to_use,
            featureidkey=feature_id_key,
            locations=location_key,
            color="value",
            projection="mercator",
            # color_continuous_scale=["orange", "white", "blue", "green"],
            color_continuous_scale="Plasma",
        )
        fig.update_geos(fitbounds="locations", visible=False)
    except Exception as e:
        print(f"Error creating Plotly figure: {e}")
        fig = px.choropleth()
        fig.update_layout(
            title_text="Error Creating Map", margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )

    fig.update_layout(
        clickmode="event+select", margin={"r": 0, "t": 0, "l": 0, "b": 0}, autosize=True
    )
    return fig


def create_section(title, content, width=None):
    if width is None:
        return html.Div(
            [
                html.H2(
                    title,
                    style={
                        "textAlign": "center",
                        "color": "#003366",
                        "marginBottom": "20px",
                    },
                ),
                html.Div(
                    content,
                    style={
                        "height": "100%",
                        "justifyContent": "center",
                        "alignItems": "center",
                    },
                ),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "margin": "20px",
                "borderRadius": "10px",
                "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)",
                "height": "100%",
            },
        )
    else:
        return html.Div(
            [
                html.H2(
                    title,
                    style={
                        "textAlign": "center",
                        "color": "#003366",
                        "marginBottom": "20px",
                    },
                ),
                html.Div(content),
            ],
            style={
                "width": width,
                "backgroundColor": "white",
                "padding": "20px",
                "margin": "20px",
                "borderRadius": "10px",
                "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)",
            },
        )


# ---------- Layout ----------
layout = html.Div(
    [
        html.Div(
            [
                html.H1("KCC Query Analysis Dashboard", style={"margin": "5px"}),
                html.Div(
                    [
                        html.Label("Start Date"),
                        dcc.DatePickerSingle(
                            id="start-date",
                            date=date(2024, 1, 1).strftime("%Y-%m-%d"),
                            style={"width": "100%"},
                        ),
                    ],
                    style={"flex": "1", "padding": "10px"},
                ),
                html.Div(
                    [
                        html.Label("End Date"),
                        dcc.DatePickerSingle(
                            id="end-date",
                            date=date(2025, 4, 30).strftime("%Y-%m-%d"),
                            style={"width": "100%"},
                        ),
                    ],
                    style={"flex": "1", "padding": "10px"},
                ),
                html.Div(
                    [
                        html.Button(
                            "Proceed",
                            id="proceed-button",
                            n_clicks=0,
                            style={
                                "width": "100%",
                                "height": "50px",
                                "backgroundColor": "#0066cc",
                                "color": "white",
                                "border": "none",
                                "borderRadius": "5px",
                            },
                        )
                    ],
                    style={
                        "flex": "0.5",
                        "padding": "10px",
                        "display": "flex",
                        "alignItems": "center",
                    },
                ),
                html.Div(
                    [
                        html.Label("Time Series Type:"),
                        dcc.Dropdown(
                            id="time-series-dropdown",
                            options=[
                                {"label": "Time Series", "value": "ts"},
                                {"label": "Stream Graph", "value": "sg"},
                            ],
                            value="ts",
                            style={"width": "100%"},
                        ),
                    ],
                    style={
                        "width": "47%",
                        "display": "inline-block",
                        "verticalAlign": "center",
                        "padding": "5px",
                    },
                ),
                # html.Div([
                #     html.Label("Node Graph Type:"),
                #     dcc.Dropdown(
                #         id="node-graph-dropdown",
                #         options=[
                #             {"label": "Crops", "value": "crop"},
                #             {"label": "Query Topics", "value": "topic"}
                #         ],
                #         value="crop",
                #         style={"width": "100%"}
                #     ),
                # ], style={"width": "47%", "display": "inline-block", "verticalAlign": "center", "padding": "5px"}),
                dcc.Store(id="selected-state-store", data=None),
                dcc.Store(id="selected-district-store", data=None),
            ],
            style={
                "display": "flex",
                # "flexDirection": "column",
                # "flex": "1",
                # "minWidth": 0,
                # "overflow": "hidden",
                "height": "17%",
                "gap": "20px",
                "padding": "20px",
                "margin": "20px",
                "backgroundColor": "#f9f9f9",
                "border": "1px solid #e0e0e0",
                "borderRadius": "15px",
                "boxShadow": "0 6px 12px rgba(0,0,0,0.15)",
                "justifyContent": "center",
                "alignItems": "center",
            },
        ),
        dcc.Loading(
            id="loading-graphs",
            type="circle",
            fullscreen=True,
            children=html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    create_section(
                                        title="🗺️ Clickable Choropleth Map of Indian States",
                                        content=[
                                            html.Button(
                                                "Reset Map",
                                                id="reset-button",
                                                n_clicks=1,
                                                style={
                                                    "display": "none",
                                                    "marginBottom": "10px",
                                                },
                                            ),
                                            html.P(
                                                "Click on a state to zoom in and view its time series below."
                                            ),
                                            dcc.Graph(
                                                id="choropleth-map",
                                                figure=create_map(),
                                                style=dict(
                                                    height="80%",
                                                    width="100%",
                                                ),
                                                responsive=True,
                                            ),
                                        ],
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "width": "60%",
                                    "flex": "2",
                                    "minWidth": 0,
                                    "overflow": "hidden",
                                    "gap": "20px",
                                    "padding": "20px",
                                    "margin": "20px",
                                    "backgroundColor": "#f9f9f9",
                                    "border": "1px solid #e0e0e0",
                                    "borderRadius": "15px",
                                    "boxShadow": "0 6px 12px rgba(0,0,0,0.15)",
                                },
                            ),
                            html.Div(
                                [
                                    create_section(
                                        title="☁️ Word Cloud of Query Text",
                                        content=[html.Div(id="wordcloud-div")],
                                    ),
                                    create_section(
                                        title="📅 Monthly Query Frequency (Aggregated by Month)",
                                        content=[
                                            dcc.Graph(
                                                id="monthly-graph",
                                                style=dict(width="100%"),
                                            )
                                        ],
                                        width="100%",
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "justifyContent": "center",
                                    "alignItems": "center",
                                    # "flex": "3",
                                    "width": "40%",
                                    "minWidth": 0,
                                    "overflow": "hidden",
                                    "gap": "20px",
                                    "padding": "20px",
                                    "margin": "20px",
                                    "backgroundColor": "#f9f9f9",
                                    "border": "1px solid #e0e0e0",
                                    "borderRadius": "15px",
                                    "boxShadow": "0 6px 12px rgba(0,0,0,0.15)",
                                },
                            ),
                        ],
                        style={
                            "flex": "1",
                            "display": "flex",
                            "overflow": "hidden",
                            # "height": "100vh"
                        },
                    ),
                    html.Div(
                        [
                            create_section(
                                title="🧩 Node Graph",
                                content=[dcc.Graph(id="node-graph")],
                                width="45%",
                            ),
                            create_section(
                                title="🌾 Node Graph (Crop Clusters)",
                                content=[dcc.Graph(id="node-graph-crop")],
                                width="45%",
                            ),
                        ],
                        style={
                            "display": "flex",
                            # "flexDirection": "column",
                            "justifyContent": "center",
                            "alignItems": "center",
                            "flex": "1",
                            "minWidth": 0,
                            "overflow": "hidden",
                            "gap": "20px",
                            "padding": "20px",
                            "margin": "20px",
                            "backgroundColor": "#f9f9f9",
                            "border": "1px solid #e0e0e0",
                            "borderRadius": "15px",
                            "boxShadow": "0 6px 12px rgba(0,0,0,0.15)",
                            # "height": "100vh"
                        },
                    ),
                    # create_section(
                    #     title="📈 Dynamic Time Series Plot",
                    #     content=[dcc.Graph(id="time-series-plot")],
                    # ),
                    html.Div(
                        [
                            html.H2(
                                "📊 Stream Graph",
                                style={
                                    "textAlign": "center",
                                    "color": "#003366",
                                    "marginBottom": "20px",
                                },
                                id="stream-graph-title",
                            ),
                            html.H2(
                                "📈 Time Series Plot",
                                style={
                                    "textAlign": "center",
                                    "color": "#003366",
                                    "marginBottom": "20px",
                                    "display": "none",
                                },
                                id="time-series-plot-title",
                            ),
                            html.Div(
                                [
                                    dcc.Graph(
                                        id="stream-graph",
                                        style=dict(
                                            # height = "90%",
                                            width="100%",
                                        ),
                                        # responsive=True
                                    )
                                ],
                                style={"width": "100%", "display": "none"},
                                id="stream-graph-div",
                            ),
                            html.Div(
                                [
                                    dcc.Graph(
                                        id="time-series-plot",
                                        style=dict(
                                            # height = "90%",
                                            width="100%",
                                        ),
                                        # responsive=True
                                    )
                                ],
                                style={"width": "100%"},
                                id="time-series-plot-div",
                            ),
                        ],
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "justifyContent": "center",
                            "alignItems": "center",
                            "flex": "1",
                            "minWidth": 0,
                            "overflow": "hidden",
                            "gap": "20px",
                            "padding": "20px",
                            "margin": "20px",
                            "backgroundColor": "#f9f9f9",
                            "border": "1px solid #e0e0e0",
                            "borderRadius": "15px",
                            "boxShadow": "0 6px 12px rgba(0,0,0,0.15)",
                        },
                    ),
                ],
                style={
                    "flex": "1",
                    "display": "flex",
                    # "overflow": "hidden",
                    # "height": "100vh",
                    "flexDirection": "column",
                },
            ),
        ),
    ],
    style={
        "height": "100vh",
        "display": "flex",
        "flexDirection": "column",
    },
    #   "overflow": "hidden"}    # style={"backgroundColor": "#f9f9f9", "fontFamily": "Arial, sans-serif"},
)


# ---------- Callback Registration ----------
def register_callbacks(app):
    @app.callback(
        Output("selected-state-store", "data"),
        Output("selected-district-store", "data"),
        Input("choropleth-map", "clickData"),
        Input("reset-button", "n_clicks"),
        State("selected-state-store", "data"),
    )
    def pick_state(clickData, reset_clicks, selected_state):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        prop = ctx.triggered[0]["prop_id"]

        if prop.startswith("reset-button") and reset_clicks:
            return None, None
        if prop.startswith("choropleth-map") and clickData and clickData.get("points"):
            clicked_location = clickData["points"][0]["location"]
            if selected_state is None:
                return clicked_location, None
            else:
                return selected_state, clicked_location

        return dash.no_update, dash.no_update

    @app.callback(
        Output("stream-graph-div", "style"),
        Output("time-series-plot-div", "style"),
        Output("stream-graph-title", "style"),
        Output("time-series-plot-title", "style"),
        Input("time-series-dropdown", "value"),
    )
    def change_time_series(ts_type):
        ts_style = None
        ts_title_style = None
        sg_style = None
        sg_title_style = None
        if ts_type == "sg":
            ts_style = {"display": "none"}
            sg_style = {"width": "100%"}
            ts_title_style = {"display": "none"}
            sg_title_style = {"display": "block"}
        else:
            sg_style = {"display": "none"}
            ts_style = {"width": "100%"}
            sg_title_style = {"display": "none"}
            ts_title_style = {"display": "block"}
        return sg_style, ts_style, sg_title_style, ts_title_style

    @app.callback(
        Output("choropleth-map", "figure"),
        Output("reset-button", "style"),
        Output("time-series-plot", "figure"),
        Output("stream-graph", "figure"),
        # Output("time-series-plot-div", "style"),
        # Output("stream-graph-div", "style"),
        Output("monthly-graph", "figure"),
        Output("node-graph", "figure"),
        Output("wordcloud-div", "children"),
        Output("node-graph-crop", "figure"),
        Input("selected-state-store", "data"),
        Input("selected-district-store", "data"),
        Input("proceed-button", "n_clicks"),
        State("start-date", "date"),
        State("end-date", "date"),
        # Input("time-series-dropdown", "value"),
    )
    def render_all(
        selected_state, selected_district, n_clicks, start_date, end_date  # , ts_type
    ):
        if n_clicks > 0:
            print("DATE TRIGGER CALLED")
            print(start_date)
            print(end_date)

        print("CMAP TRIGGER CALLED")
        start_date_date = date(2024, 1, 1)
        end_date_date = date(2025, 4, 30)
        if start_date is not None:
            start_date_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date is not None:
            end_date_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        filtered_df = df2
        filtered_df = filtered_df[
            (filtered_df["Date"] >= start_date_date)
            & (filtered_df["Date"] <= end_date_date)
        ]
        state_name_caps = selected_state if selected_state else None
        district_name_caps = selected_district if selected_district else None
        print(state_name_caps, district_name_caps)
        title = "Time series for INDIA"
        if state_name_caps is not None:
            filtered_df = df2[df2["StateName"] == state_name_caps]
            title = f"Time Series for {selected_state}"
        if district_name_caps is not None:
            filtered_df = filtered_df[filtered_df["DistrictName"] == district_name_caps]
            title = f"Time Series for {selected_district} of {selected_state}"

        filtered_df["cluster_id"] = filtered_df["QueryType"].map(query_to_cluster)
        filtered_df["cluster_id"] = filtered_df["cluster_id"].astype(str)
        filtered_df["cluster_label"] = filtered_df["cluster_id"].map(cluster_to_queries)

        fig_map = create_map(selected_state)
        btn_style = (
            {
                "width": "100%",
                "height": "50px",
                "backgroundColor": "#0066cc",
                "color": "white",
                "border": "none",
                "borderRadius": "5px",
            }
            if selected_state
            else {"display": "none"}
        )

        # ts_style = None
        # sg_style = None
        # if ts_type == "sg":
        #     ts_style = {"display": "none"}
        #     sg_style = style = {"width": "100%"}
        # else:
        #     sg_style = {"display": "none"}
        #     ts_style = style = {"width": "100%"}

        results = {}

        def generate_time_series():
            s1 = time.time()
            filtered_ts = (
                filtered_df.groupby("Date").size().reset_index(name="Frequency")
            )

            # Apply rolling average smoothing (window size can be tuned)
            filtered_ts["Smoothed_Frequency"] = (
                filtered_ts["Frequency"]
                .rolling(window=15, center=True, min_periods=1)
                .mean()
            )

            fig = px.line(filtered_ts, x="Date", y="Smoothed_Frequency", title=title)
            fig.update_layout(xaxis=dict(rangeslider=dict(visible=True)))
            results["fig_ts"] = fig
            e1 = time.time()
            print(f"Time series figure done {e1 - s1}")

        def generate_stream_graph():
            s1 = time.time()

            stream_graph_df = (
                filtered_df.groupby(["cluster_label", "Date"])
                .size()
                .reset_index(name="count")
            )

            # Apply smoothing for each cluster separately
            stream_graph_df["Smoothed_Count"] = stream_graph_df.groupby(
                "cluster_label"
            )["count"].transform(
                lambda x: x.rolling(window=15, center=True, min_periods=1).mean()
            )

            fig = px.area(
                stream_graph_df,
                x="Date",
                y="Smoothed_Count",  # Use the smoothed count
                color="cluster_label",
                line_group="cluster_label",
                title="Query Clusters Over Time",
                labels={"Smoothed_Count": "Query Count", "Date": "Time"},
            )
            fig.update_traces(mode="lines")
            fig.update_layout(
                xaxis=dict(title="Time"),
                yaxis=dict(title="Total Queries"),
                hovermode="x unified",
            )

            results["fig_sg"] = fig
            e1 = time.time()
            print(f"Stream time {e1 - s1}")

        def generate_monthly_graph():
            s1 = time.time()
            if "Month" not in filtered_df.columns:
                filtered_df["Date"] = pd.to_datetime(filtered_df["Date"])
                filtered_df["Month"] = filtered_df["Date"].dt.month
            monthly_sector_counts = filtered_df.groupby(["Month", "Sector"]).size()
            monthly_sector_counts_pivot = monthly_sector_counts.unstack(
                level="Sector", fill_value=0
            )
            monthly_sector_counts_pivot = monthly_sector_counts_pivot.reindex(
                range(1, 13), fill_value=0
            )
            monthly_sector_counts_pivot["Total"] = monthly_sector_counts_pivot.sum(
                axis=1
            )
            months_abbr = [
                calendar.month_abbr[m] for m in monthly_sector_counts_pivot.index
            ]
            fig = px.line(
                monthly_sector_counts_pivot,
                x=months_abbr,
                y=monthly_sector_counts_pivot.columns,
                title=f"Monthly Query Frequency by Sector for {selected_state if selected_state else 'India'}",
                labels={"x": "Month", "y": "Query Count", "variable": "Sector / Total"},
                markers=True,
            )
            results["fig_monthly"] = fig
            e1 = time.time()
            print(f"Monthly time {e1 - s1}")

        def generate_wordcloud():
            image_path = f'../data/state_wordcloud/{state_name_caps if selected_state else "india"}_wordcloud.png'
            try:
                encoded_image = encode_image(image_path)
                image_component = html.Img(
                    src=encoded_image, style={"width": "100%", "height": "auto"}
                )
            except FileNotFoundError:
                image_component = html.Div("Image not found", style={"color": "red"})
            results["image_component"] = image_component

        def generate_ng1():
            s1 = time.time()
            results["ng1"] = query_node_graph(filtered_df)
            e1 = time.time()
            print(f"ng1 time {e1 - s1}")

        def generate_ng2():
            s1 = time.time()
            results["ng2"] = crop_node_graph(filtered_df)
            e1 = time.time()
            print(f"ng2 time {e1 - s1}")

        # Create and start all threads
        threads = [
            threading.Thread(target=generate_time_series),
            threading.Thread(target=generate_stream_graph),
            threading.Thread(target=generate_monthly_graph),
            threading.Thread(target=generate_wordcloud),
            threading.Thread(target=generate_ng1),
            threading.Thread(target=generate_ng2),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        print("Returning objects")
        return (
            fig_map,
            btn_style,
            results["fig_ts"],
            results["fig_sg"],
            # ts_style,
            # sg_style,
            results["fig_monthly"],
            results["ng1"],
            results["image_component"],
            results["ng2"],
        )
