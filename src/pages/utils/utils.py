import os
import base64
import json
import pandas as pd
from pathlib import Path


def encode_image(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


# ---------- GeoJSON Loaders ----------
# @lru_cache(maxsize=1)
def load_base_geojson():
    filepath = (
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "states.json"
    ).as_posix()
    try:
        with open(filepath) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Base geojson file not found at {filepath}")
        return {"type": "FeatureCollection", "features": []}


# @lru_cache(maxsize=32)
def load_state_geojson(state_name):
    path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "data"
        / "statewise"
        / f"{state_name}.json"
    ).as_posix()
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading state geojson for {state_name}: {e}")
            return None
    return None


# @lru_cache(maxsize=1)
def load_data(df2):
    geojson = load_base_geojson()
    features = geojson.get("features", [])
    dr = pd.DataFrame(
        [
            {"state": f["id"], "value": int(len(df2[df2["StateName"] == f["id"]]))}
            for f in features
            if "id" in f
        ]
    )
    return dr
