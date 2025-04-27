import pandas as pd
import requests
import csv
import re
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA

# ---------- CROP DATA PREPARATION ----------
data = """
1. Grains
    - Wheat - 1
    - Paddy - 2
    - Jowar - 5
    - Bajra - 28
    - Barley (Jau) - 29
    - Ragi - 30
2. Fruits
    - Methi(Leaves) - 46
    - Peas_cod - 308
    - Peas_Wet - 174
    - Spinach - 342
    - Pointed_gourd_Parval - 303
    - Coriander(Leaves) - 43
    - Onion - 23
    - Apple - 17
    - Banana - Green - 90
    - Grapes - 22
    - Mango - 20
    - Papaya - 72
    - Orange - 18
    - Pineapple - 21
    - Pomegranate - 190
    - Guava - 185
    - Jack Fruit - 182
    - Lemon - 310
    - Chikoos(Sapota) - 71
    - Lime - 180
    - Pear - 330
    - Plum - 329
    - Litchi - 351
    - Custard Apple - 352
3. Pulses and Legumes
    - Arhar Dal(Tur Dal) - 260
    - Bengal Gram Dal(Chana Dal) - 263
    - Black Gram Dal(Urd Dal) - 264
    - Green Gram(Moong) - 9
    - Green Gram Dal(Moong Dal) - 265
    - Lentil(Masur) - 63
    - Horse Gram(Kulthi) - 114
"""

# ---------- PARSE CROPS ----------
crop_mapping = {}
for line in data.split("\n"):
    item_match = re.match(r"^\s+-\s+(.+)\s+-\s+(\d+)", line)
    if item_match:
        crop_name = item_match.group(1).strip()
        crop_number = int(item_match.group(2))
        crop_mapping[crop_number] = crop_name


def parse_sections(data):
    sections = {}
    current_section = None
    for line in data.split("\n"):
        section_match = re.match(r"^\d+\.\s+(.+)", line)
        item_match = re.match(r"^\s+-\s+.+-\s+(\d+)", line)

        if section_match:
            current_section = section_match.group(1).strip()
            sections[current_section] = []
        elif item_match and current_section:
            sections[current_section].append(int(item_match.group(1)))
    return sections


parsed_data = parse_sections(data)

# ---------- LOAD CROPS DATA ----------
df = pd.DataFrame()
df2 = df.copy()
column_names = [
    "SrNo",
    "District",
    "Market",
    "Commodity",
    "Variety",
    "Standard",
    "MinPrice",
    "MaxPrice",
    "ModalPrice",
    "PriceDate",
]

for section, items in parsed_data.items():
    for item in items:
        crop_data = pd.DataFrame()
        if item in [1, 2, 17, 23]:
            for year in range(2015, 2025):
                foo = pd.read_csv(f"../data/rainy/{item}_prices_{year}.csv")
                crop_data = pd.concat([crop_data, foo])
        else:
            crop_data = pd.read_csv(f"../data/{item}_prices.csv")

        crop_data.columns = column_names

        crop_data_copy = crop_data.copy()
        crop_data_copy["CropName"] = item

        df2 = pd.concat([df2, crop_data_copy])

        crop_data = crop_data.groupby(
            ["District", "Commodity", "Variety", "Standard"]
        ).filter(lambda x: len(x) > 1500)
        crop_data = (
            crop_data.groupby(["PriceDate", "District"])["ModalPrice"]
            .mean()
            .reset_index()
        )
        crop_data["PriceDate"] = pd.to_datetime(crop_data["PriceDate"], errors="coerce")
        crop_data = crop_data.dropna(subset=["PriceDate"])
        crop_data["ModalPrice"] = pd.to_numeric(
            crop_data["ModalPrice"], errors="coerce"
        )
        crop_data = crop_data.dropna(subset=["ModalPrice"])
        crop_data["Month"] = crop_data["PriceDate"].dt.month
        crop_data["Year"] = crop_data["PriceDate"].dt.year
        crop_data = (
            crop_data.groupby(["Month", "Year", "District"])["ModalPrice"]
            .mean()
            .reset_index()
        )
        crop_data["CropName"] = item
        df = pd.concat([df, crop_data])

df["PriceDate"] = pd.to_datetime(df[["Year", "Month"]].assign(DAY=1))
df["ModalPrice"] = pd.to_numeric(df["ModalPrice"], errors="coerce")
df = df.dropna(subset=["ModalPrice"])

df2["PriceDate"] = pd.to_datetime(df2["PriceDate"], errors="coerce")
df2 = df2.dropna(subset=["PriceDate"])
df2["ModalPrice"] = pd.to_numeric(df2["ModalPrice"], errors="coerce")
df2 = df2.dropna(subset=["ModalPrice"])


def csv_to_dict_of_tuples(file_path):
    # Initialize an empty dictionary
    result = {}

    # Open the CSV file
    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)

        # Initialize the dictionary with empty lists for each column
        for column in reader.fieldnames:
            result[column] = []

        # Populate the dictionary by appending each value in the respective column
        for row in reader:
            for column in reader.fieldnames:
                try:
                    result[column].append(float(row[column]))
                except:
                    if column in result.keys():
                        result.pop(column)

        # Convert each list to a tuple
        for column in result:
            if column in result.keys():
                result[column] = tuple(result[column])

    if "" in result.keys():
        result.pop("")
    return result


global_geocode_cache = csv_to_dict_of_tuples("../data/geocode_cache.csv")


def get_geocode(location):
    API_KEY = "8ba1888d6fb2f9c1fe2aed472e129529"
    base_url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {"q": f"{location},IN", "limit": 1, "appid": API_KEY}

    if location == "Yamuna Nagar":
        location = "Yamuna Nagar, Haryana"

    if location in global_geocode_cache.keys():
        return global_geocode_cache[location]

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data:
            lat = data[0]["lat"]
            lon = data[0]["lon"]
            global_geocode_cache[location] = (lat, lon)
            return lat, lon
        else:
            global_geocode_cache[location] = (None, None)
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None, None


# ---------- LAYOUT ----------
layout = html.Div(
    [
        # Header and dropdowns container
        html.Div(
            [
                html.H1(
                    "🌾 Modal Price Dashboard",
                    style={"textAlign": "center", "margin": "5px"},
                ),
                html.Div(
                    [
                        html.Label("Select Crop:"),
                        dcc.Dropdown(
                            id="crop-dropdown",
                            options=[
                                {"label": name, "value": crop_id}
                                for crop_id, name in crop_mapping.items()
                            ],
                            value=1,
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
                html.Div(
                    [
                        html.Label("Select Statistic for India Map:"),
                        dcc.Dropdown(
                            id="mean-variance-dropdown",
                            options=[
                                {"label": "Mean", "value": "mean"},
                                {"label": "Variance", "value": "variance"},
                            ],
                            value="variance",
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
                # dcc.Store(id="selected-state-store", data=None),
            ],
            style={
                "display": "flex",
                "height": "17%",
                "gap": "20px",
                "padding": "20px",
                "margin": "20px",
                "backgroundColor": "#f9f9f9",
                "border": "1px solid #e0e0e0",
                "borderRadius": "15px",
                "boxShadow": "0 6px 12px rgba(0,0,0,0.15)",
            },
        ),
        # Main content area using Flexbox for two columns
        html.Div(
            [
                # Left column: Map and Variety Histogram (enhanced styling)
                html.Div(
                    [
                        dcc.Graph(
                            id="india-map",
                            style={
                                "flex": "6",
                                "minHeight": 0,
                                "width": "100%",
                                "borderRadius": "15px",
                            },
                        ),
                        dcc.Graph(
                            id="variety-histogram",
                            style={
                                "flex": "4",
                                "minHeight": 0,
                                "width": "100%",
                                "borderRadius": "15px",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
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
                # Right column: Forecast, Seasonality and Trend
                html.Div(
                    [
                        dcc.Graph(
                            id="forecast-plot",
                            style={
                                "flex": "6",
                                "minHeight": 0,
                                "width": "100%",
                                "borderRadius": "15px",
                            },
                        ),
                        dcc.Graph(
                            id="seasonal-plot",
                            style={
                                "flex": "5",
                                "minHeight": 0,
                                "width": "100%",
                                "borderRadius": "15px",
                            },
                        ),
                        dcc.Graph(
                            id="trend-plot",
                            style={
                                "flex": "5",
                                "minHeight": 0,
                                "width": "100%",
                                "borderRadius": "15px",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
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
                "overflow": "hidden",
                "height": "calc(100vh - 150px)",
            },
        ),
    ],
    style={
        "height": "100vh",
        "display": "flex",
        "flexDirection": "column",
        "overflow": "hidden",
    },
)


# ---------- CALLBACK REGISTRATION ----------
def register_callbacks(app):
    @app.callback(
        Output("india-map", "figure"),
        Output("trend-plot", "figure"),
        Output("seasonal-plot", "figure"),
        Output("forecast-plot", "figure"),
        Output("variety-histogram", "figure"),
        # Input("selected-state-store", "data"),
        Input("crop-dropdown", "value"),
        Input("mean-variance-dropdown", "value"),
    )
    def update_time_series(crop_id, stat_choice):
        crop_name = crop_mapping[crop_id]
        print(crop_name)
        crop_data = df[df["CropName"] == crop_id]
        crop_data = (
            crop_data.groupby(["PriceDate", "Month", "Year"])["ModalPrice"]
            .mean()
            .reset_index()
        )

        crop_data["PriceDate"] = pd.to_datetime(crop_data["PriceDate"])
        crop_data = crop_data.set_index("PriceDate").asfreq("MS")
        crop_data = crop_data[["ModalPrice"]].fillna(crop_data.mean())

        # ---------- Histogram: Top 10 Varieties by count in original df2 ----------
        variety_data = df2[df2["CropName"] == crop_id]
        # Get top 10 varieties based on count
        top_varieties = variety_data["Variety"].value_counts().head(10).index
        grouped_by_variety = (
            variety_data.groupby("Variety")["ModalPrice"].mean().reset_index()
        )
        filtered_grouped = grouped_by_variety[
            grouped_by_variety["Variety"].isin(top_varieties)
        ]
        fig_histogram = px.bar(
            filtered_grouped,
            x="Variety",
            y="ModalPrice",
            title=f"Average Modal Price by Variety for {crop_name} (Top 10 by count)",
            labels={"ModalPrice": "Average Modal Price", "Variety": "Variety"},
            color="ModalPrice",
            color_continuous_scale="Plasma",
            text="Variety",
        )
        # show tick‐marks only at each bar, hide any labels underneath
        fig_histogram.update_xaxes(
            ticks="outside", tickson="labels", showticklabels=False
        )
        fig_histogram.update_traces(textposition="inside")

        df3 = df2[df2["CropName"] == crop_id]
        district_counts = df3["District"].value_counts()
        valid_districts = district_counts[district_counts > 200].index
        df_filtered = df3[df3["District"].isin(valid_districts)]

        if stat_choice == "variance":
            data_agg = (
                df_filtered.groupby("District")["ModalPrice"]
                .std()
                .reset_index()
                .dropna()
            )
            data_agg.rename(columns={"ModalPrice": "Value"}, inplace=True)
            map_title = "Variance of Modal Prices by District"
        else:
            data_agg = (
                df_filtered.groupby("District")["ModalPrice"]
                .mean()
                .reset_index()
                .dropna()
            )
            data_agg.rename(columns={"ModalPrice": "Value"}, inplace=True)
            map_title = "Mean Modal Prices by District"

        # 1. Get latitudes and longitudes
        data_agg["Latitude"], data_agg["Longitude"] = zip(
            *data_agg["District"].map(get_geocode)
        )

        # 2. Filter out any rows where location wasn't found
        data_agg = data_agg.dropna(subset=["Latitude", "Longitude"])

        # ---------- Map: Focus on India with Boundaries ----------
        fig = px.scatter_geo(
            data_agg,
            lat="Latitude",
            lon="Longitude",
            color="Value",
            hover_name="District",
            color_continuous_scale=(
                "Viridis" if stat_choice == "variance" else "Plasma"
            ),
            projection="natural earth",
            title=map_title,
            scope="asia",
        )

        # keep the map bounds locked to India
        fig.update_geos(
            visible=True,
            showcountries=True,
            countrycolor="black",
            showsubunits=True,
            subunitcolor="gray",
            fitbounds="locations",
            lataxis_range=[6, 38],
            lonaxis_range=[68, 98],
        )

        # set figure size in percentage
        fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            autosize=True,
        )

        # ---------- DECOMPOSITION ----------
        components = seasonal_decompose(crop_data["ModalPrice"], model="additive")

        # ---------- SARIMAX FUTURE PREDICTION ----------
        sarimax_model = ARIMA(
            endog=crop_data["ModalPrice"], order=(0, 1, 1), seasonal_order=(1, 1, 1, 12)
        )
        sarimax_results = sarimax_model.fit()

        future_steps = 12  # Forecast next 12 months
        predictions = sarimax_results.get_forecast(steps=future_steps)
        future_dates = pd.date_range(
            crop_data.index[-1] + pd.DateOffset(months=1),
            periods=future_steps,
            freq="MS",
        )

        fig_trend = px.line(components.trend, title=f"Trend Component for {crop_name}")
        fig_seasonal = px.line(
            components.seasonal, title=f"Seasonality Component for {crop_name}"
        )

        # Forecast Plot
        fig_forecast = go.Figure()
        fig_forecast.add_trace(
            go.Scatter(
                x=crop_data.index,
                y=crop_data["ModalPrice"],
                name="Historical Price",
                line=dict(color="blue"),
            )
        )
        fig_forecast.add_trace(
            go.Scatter(
                x=future_dates,
                y=predictions.predicted_mean,
                name="Forecasted Price",
                line=dict(color="red", dash="dash"),
            )
        )
        fig_forecast.update_layout(
            title=f"Forecasted Modal Price for next {len(future_dates)} months",
            xaxis_title="Date",
            yaxis_title="Modal Price",
        )

        fig_forecast.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
            ),
        )

        fig_trend.update_layout(margin=dict(l=0, r=0, t=50, b=0), autosize=True)
        fig_seasonal.update_layout(margin=dict(l=0, r=0, t=50, b=0), autosize=True)
        fig_forecast.update_layout(margin=dict(l=0, r=0, t=50, b=0), autosize=True)
        fig_histogram.update_layout(margin=dict(l=0, r=0, t=50, b=0), autosize=True)

        return fig, fig_trend, fig_seasonal, fig_forecast, fig_histogram
