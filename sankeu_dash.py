# df is a pandas dataframe which contains 2 columns: From Application, and Downstream. This dataframe comes from custom_api. 'From Application' gives us the name of a particular component, 'Downstream' gives us the corresponding downstream app dependencies for the app in 'From Application'.
# I need to generate a sankey diagram which will help me visualize all the upstream and downstream dependencies. I also have a filter which helps me look at the dependencies for a single node.

# app_list is a list of all available apps

import plotly.io as py
import plotly.graph_objects as go
import custom_api

df = custom_api.get_data()

G = nx.DiGraph()
subset_mapping = {}
subset_count = 0
check = 0

for app in df['From Application']:
    G.add_node(app)
    subset_mapping[app] = subset_count

for idx, row in df.iterrows():
    application = row['From Application']
    downstream_apps = row['Downstream']

    if len(downstream_apps) > 0:
        for downstream_app in downstream_apps:
            G.add_edge(application, downstream_app.strip())
    
    else:
        G.add_edge(application, application)


for _, _, d in G.edges(data = True):
    d['weight'] = 1

for u in G.nodes():
    for v in G.nodes():
        if u != v and not G.has_edge(u, v):
            try:
                shortest_path_length = nx.shortest_path_length(G, source = u, target = v)
                if shortest_path_length > 0:
                    G.add_edge(u, v, weight = 1 / shortest_path_length)
            except nx.NetworkXNoPath:
                continue

degree_dict = dict(G.degree())
# heatmap_df = pd.DataFrame(list(degree_dict.items()), columns = ['Component', 'Degree'])
upstream_count = {node: 0 for node in G.nodes()}
downstream_count = {node: 0 for node in G.nodes()}

for u, v in G.edges():
    downstream_count[u] += 1
    upstream_count[v] += 1

stacked_barchart_df = pd.DataFrame({
    "Component": list(G.nodes()),
    "Upstream": [upstream_count[node] for node in G.nodes()],
    "Downstream": [downstream_count[node] for node in G.nodes()]
})

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Sankey Diagram"),
    dcc.Dropdown(
        id = 'node-dropdown',
        options = [{ 'label' : node, 'value' : node} for node in G.nodes()],
        value = None,
        multi = False,
        placeholder = "Select a node to filter"
    ),
    dcc.Graph(id = "sankey-graph"),
    html.H1("Connection based heatmap"),
    dcc.Graph(id = 'heatmap')
])

@app.callback(
    Output('sankey-graph', 'figure'),
    [Input('node-dropdown', 'value')]
)

def update_graph(selected_node):
    degree_dict = dict(G.degree())
    sorted_nodes = sorted(degree_dict.keys(), key = degree_dict.get, reverse = True)

    source, target, value = [], [], []

    for u, v, d in G.edges(data = True):
        if selected_node and (u == selected_node or v == selected_node):
            source.append(sorted_nodes.index(u))
            target.append(sorted_nodes.index(v))
            value.append(d['weight'])
        elif not selected_node:
            source.append(sorted_nodes.index(u))
            target.append(sorted_nodes.index(v))
            value.append(d['weight'])  

    node_colors = ["Red" if node.lower() in [appName.lower() for appName in app_list] else "Grey" for node in sorted_nodes]
    if selected_node:
        link_colors = ["Blue" if source[i] == sorted_nodes.index(selected_node) else "Green" for i in range(len(source))]
    else:
        link_colors = ["Grey" for _ in range(len(source))]

    data = go.Sankey(
        node = dict(
            pad = 100,
            thickness = 100,
            line = dict(color = 'black', width = 2),
            label = sorted_nodes,
            color = node_colors
        ),
        link = dict(
            source = source,
            target = target,
            value = value
            color = link_colors
        )
    )

    fig = go.Figure([data])

    fig.update_layout(
        title_text = "Sankey Diagram with deps",
        font_size = 15,
        width = 200,
        height = 2000
    )
    
    return fig

@app.callback(
        Output('barchart', 'figure'),
        [Input('sankey-graph', 'figure')]
)

def update_barchart(_):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        heatmap_df,
        x = stacked_barchart_df['Component'],
        y = stacked_barchart_df["Downstream"],
        name = "Upstream",
        marker_color = "#6174EA"
    ))

    fig.add_trace(go.Bar(
        x = stacked_barchart_df["Component"],
        y = stacked_barchart_df["Downstream"],
        name = "Downstream",
        marker_color = "#e5552f"
    ))

    fig.update_layout(
        xaxis_title = "Component",
        yaxis_title = "Number of Dependencies",
        barmode = "relative",
        height = 1000,
        width = 2000
    )

    return fig


if __name__ == 'main':
    app.run_server(debug = True)