import pandas as pd
from pietree import *

samples = pd.read_csv("data/spider_samples.csv", sep=";")
tree = PieTree.from_newick(path="data/spiders.newick")

tree.annotate(samples, on="mitogenome_id")

tree.nodes(node_type="tip").rename("{species} {mitogenome_id}")
tree.nodes(node_type="tip", group="this_study").suffix(" *")

tree.nodes(group="this_study").style(fill="red", radius=5)
tree.tip_labels(group="this_study").style(font_weight="bold")

for taxon, color in [("Lycosoidea", "blue"),
                    ("Dictynoidea", "grey"), 
                    ("Araneoidea", "pink"), 
                    ("Dysderoidea", "yellow"), 
                    ("Scytodoidea", "green"), 
                    ("Pholcoidea", "red")]:
    tree.clade_by_taxon(taxon).highlight(fill=color, label=taxon)

# tree.metadata("taxonomy").highlight(values=["Lycosoidea", "Dictynoidea", "Araneoidea", "Dysderoidea", "Scytodoidea", "Pholcoidea"])
# tree.metadata("group").panel(values=["outgroup"])
tree.metadata("group").panel()

tree.to_svg(
    "spiders_tree.svg"
)