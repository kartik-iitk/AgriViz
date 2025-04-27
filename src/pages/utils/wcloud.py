from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import io
import base64
import plotly.graph_objects as go

my_stopwords = [
    "farmer",
    "asked",
    "query",
    "information",
    "call",
    "ask",
    "asking",
    "regarding",
    "kisan",
    "samman",
    "nidhi",
    "yojana",
    "pm",
    "hai",
    "ka",
    "ke",
    "test",
    "status",
    "mein",
    "me",
    "k",
    "ki",
    "se",
    "related",
    "regarding",
    "give",
    "control",
    "help",
    "please",
    "want",
    "know",
    "details",
    "number",
    "sir",
    "madam",
    "farmer",
    "problem",
    "report",
    "management",
    "information",
    "application",
    "status",
    "update",
    "check",
    "want",
    "need",
    "madad",
    "scheme",
    "District",
    "jankari",
    "tell",
    "mausam",
    "mosam",
    "crop",
    "minister",
    "pradhan",
    "time",
    "much",
    "plant",
    "govt",
    "government",
    "state",
    "mantri",
    "yojna",
    "mausam",
    "measure",
    "jankari",
    "general",
    "TELL",
    "Mausam",
    "lag",
    "kare",
    "rahe",
    "lag",
    "hain",
    "raha",
    "aa",
    "kab",
    "de",
    "ho",
    "MANIPURI",
    "EXPERT",
    "expert",
]

custom_stopwords = set(STOPWORDS)
custom_stopwords.update(my_stopwords)


def get_wcloud(df):
    assert "QueryText" in df.columns
    print("WordCLOUD func called")
    combined_text = " ".join(df["QueryText"])
    df_sampled = df.sample(n=min(len(df), 5000))
    print("sampling done")
    wordcloud = WordCloud(
        width=1600,
        height=800,
        background_color="white",
        stopwords=custom_stopwords,
        min_font_size=10,
        max_words=150,
        collocations=False,
    ).generate(combined_text)
    print("wcloud generated")
    buf = io.BytesIO()
    plt.figure(figsize=(16, 8))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=300)
    plt.close()

    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    fig = go.Figure()
    fig.add_layout_image(
        dict(
            source="data:image/png;base64," + img_base64,
            xref="paper",
            yref="paper",
            x=0,
            y=1,
            sizex=1,
            sizey=1,
            xanchor="left",
            yanchor="top",
            sizing="stretch",
        )
    )

    fig.update_layout(
        width=1000,
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig
