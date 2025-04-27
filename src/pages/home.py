from dash import html

layout = html.Div(
    [
        html.Div(
            [
                html.H1(
                    "AgriViz: Analysing Farmer Queries with Data",
                    style={
                        "textAlign": "center",
                        "fontSize": "36px",
                        "marginBottom": "10px",
                        "color": "#2c3e50",
                    },
                ),
                html.H4(
                    "CS661 Project 2024‑25‑II",
                    style={"textAlign": "center", "margin": "5px", "color": "#34495e"},
                ),
                html.H4(
                    "Group 3",
                    style={
                        "textAlign": "center",
                        "marginBottom": "30px",
                        "color": "#34495e",
                    },
                ),
                html.Table(
                    # Table header
                    [
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th("Name", style={"padding": "8px"}),
                                    html.Th("Roll No.", style={"padding": "8px"}),
                                ],
                                style={"backgroundColor": "#2980b9", "color": "white"},
                            )
                        ),
                        # Table body
                        html.Tbody(
                            [
                                html.Tr(
                                    [
                                        html.Td(
                                            "Chitwan Goel", style={"padding": "8px"}
                                        ),
                                        html.Td("210295", style={"padding": "8px"}),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td(
                                            "Kartik Anant Kulkarni",
                                            style={"padding": "8px"},
                                        ),
                                        html.Td("210493", style={"padding": "8px"}),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td(
                                            "Siddharth Kalra", style={"padding": "8px"}
                                        ),
                                        html.Td("211032", style={"padding": "8px"}),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td(
                                            "Aniket Suhas Borkar",
                                            style={"padding": "8px"},
                                        ),
                                        html.Td("210135", style={"padding": "8px"}),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Geetika", style={"padding": "8px"}),
                                        html.Td("210392", style={"padding": "8px"}),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td(
                                            "Vikas Yadav", style={"padding": "8px"}
                                        ),
                                        html.Td("211166", style={"padding": "8px"}),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Divyansh", style={"padding": "8px"}),
                                        html.Td("210355", style={"padding": "8px"}),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td(
                                            "Shrey Bansal", style={"padding": "8px"}
                                        ),
                                        html.Td("210997", style={"padding": "8px"}),
                                    ]
                                ),
                            ]
                        ),
                    ],
                    style={
                        "margin": "auto",
                        "border": "1px solid #ddd",
                        "borderCollapse": "collapse",
                        "width": "60%",
                        "fontSize": "16px",
                    },
                ),
            ],
            style={"maxWidth": "800px", "margin": "60px auto", "padding": "20px"},
        )
    ]
)
