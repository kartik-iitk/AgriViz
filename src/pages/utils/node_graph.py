import pandas as pd
from scipy.spatial.distance import pdist, squareform
import networkx as nx
import plotly.graph_objects as go
from sklearn.manifold import MDS


def generate_ng_from_dist_matrix(dist_matrix, titletext):
    G = nx.Graph()
    for node in dist_matrix.columns:
        G.add_node(node)

    threshold = dist_matrix.values.mean()
    for i in dist_matrix.index:
        for j in dist_matrix.columns:
            if i != j and dist_matrix.loc[i, j] < threshold:
                G.add_edge(i, j, weight=dist_matrix.loc[i, j])

    mds = MDS(
        n_components=2,
        dissimilarity="precomputed",
        random_state=42,
        normalized_stress="auto",
    )
    coords = mds.fit_transform(dist_matrix.values)

    pos = {
        node: (coords[i, 0], coords[i, 1]) for i, node in enumerate(dist_matrix.index)
    }

    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    node_x, node_y, node_text = [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(node))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="bottom center",
        hoverinfo="text",
        marker=dict(showscale=False, color="blue", size=20, line_width=2),
    )

    fig_ng = go.Figure(
        data=[edge_trace, node_trace],
        # layout=go.Layout(
        #     title=f'<br>{titletext} Similarity Graph',
        #     titlefont_size=16,
        #     showlegend=False,
        #     hovermode='closest',
        #     margin=dict(b=20, l=5, r=5, t=40),
        #     xaxis=dict(showgrid=False, zeroline=False),
        #     yaxis=dict(showgrid=False, zeroline=False))
        layout=go.Layout(
            # title=dict(
            #     text=f"<br>{titletext} Similarity Graph",
            #     font=dict(size=16),  # Adjust the font size as needed
            # ),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
        ),
    )
    return fig_ng


def query_node_graph(df):
    assert "Date" in df.columns and "cluster_label" in df.columns

    # print(df["cluster_label"].unique())
    ts_df = df.groupby(["Date", "cluster_label"]).size().unstack(fill_value=0)
    ts_df = ts_df.asfreq("D", fill_value=0)

    # --- Normalize ---
    ts_normalized = (ts_df - ts_df.min()) / (ts_df.max() - ts_df.min())
    dist_array = pdist(ts_normalized.T, metric="euclidean")
    dist_matrix = pd.DataFrame(
        squareform(dist_array),
        index=ts_normalized.columns,
        columns=ts_normalized.columns,
    )

    return generate_ng_from_dist_matrix(dist_matrix, "QueryType")


def crop_node_graph(df, top_x=15):
    assert "Date" in df.columns and "Crop" in df.columns

    top_col2_values = (
        df[df["Crop"] != "Others"]
        .groupby("Crop")
        .size()
        .sort_values(ascending=False)
        .head(top_x)
        .index
    )

    df_top = df[df["Crop"].isin(top_col2_values)]
    ts_df = df_top.groupby(["Date", "Crop"]).size().unstack(fill_value=0)
    ts_df = ts_df.asfreq("D", fill_value=0)

    ts_normalized = (ts_df - ts_df.min()) / (ts_df.max() - ts_df.min())
    dist_array = pdist(ts_normalized.T, metric="euclidean")
    dist_matrix = pd.DataFrame(
        squareform(dist_array),
        index=ts_normalized.columns,
        columns=ts_normalized.columns,
    )

    return generate_ng_from_dist_matrix(dist_matrix, "Crop")
