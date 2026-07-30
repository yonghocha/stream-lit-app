from pyvis.network import Network
import os, json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from urllib.request import urlopen

D3_SCRIPT_TAG = "<script src='https://cdnjs.cloudflare.com/ajax/libs/d3/4.5.0/d3.min.js'></script>"

@st.cache_data
def getD3():
    with urlopen("https://cdnjs.cloudflare.com/ajax/libs/d3/4.5.0/d3.min.js", timeout=10) as response:
        return response.read().decode("utf-8")

def getJson(df):

    # collect all nodes
    nodes = {}
    for _, row in df.iterrows():
        name = row.iloc[0]
        nodes[name] = { "name": name }

    # move children under parents, and detect root
    root = None
    for _, row in df.iterrows():
        node = nodes[row.iloc[0]]
        isRoot = pd.isna(row.iloc[1])
        if isRoot: root = node
        else:
            parent = nodes[row.iloc[1]]
            if "children" not in parent: parent["children"] = []
            parent["children"].append(node)

    return root

def makeCollapsibleTree(df):

    # create HTML file from template customized with our JSON
    with open("animated/templates/collapsible-tree.html", "r", encoding="utf-8") as file:
        content = file.read()

    root = getJson(df)
    content = content.replace(D3_SCRIPT_TAG, f"<script>{getD3()}</script>")
    content = content.replace('"{{data}}"', json.dumps(root, indent=4))
    filename = "animated/collapsible-tree.html"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    return os.path.abspath(filename)

def makeNetworkGraph(df):

    data = Network(notebook=False, heading='', cdn_resources='in_line')
    data.barnes_hut(
        gravity=-80000,
        central_gravity=0.3,
        spring_length=10.0,
        spring_strength=1.0,
        damping=0.09,
        overlap=0)

    for _, row in df.iterrows():
        src = str(row.iloc[0])
        dst = str(row.iloc[1])
        data.add_node(src)
        data.add_node(dst)
        data.add_edge(src, dst)

    # set node size to number of child nodes
    map = data.get_adj_list()
    for node in data.nodes:
        node["value"] = len(map[node["id"]])

    filename = "animated/network-graph.html"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(data.generate_html(notebook=False))
    return os.path.abspath(filename)


st.title("Hierarchical Data Formats")
df = pd.read_csv("data/employees.csv", header=0).convert_dtypes()

tree, net = st.tabs(["Collapsible Tree", "Network Graph"])
with tree:
    with open(makeCollapsibleTree(df), 'r', encoding='utf-8') as f:
        components.html(f.read(), height=2200, width=1000)
with net:
    with open(makeNetworkGraph(df), 'r', encoding='utf-8') as f:
        components.html(f.read(), height=2200, width=1000)
