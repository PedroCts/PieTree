import pandas as pd
from pietree import *

samples = pd.read_csv("data/spider_samples.csv", sep=";")
tree = PieTree.from_newick(path="data/spiders.newick")

for _, sample in samples.iterrows():
    tip = tree.find_tip(sample["mitogenome_id"])
    tip.rename(f"{sample['species']} {sample['mitogenome_id']}")
    if not tip: continue
    for column in sample.index:
        tip.annotate(column, sample[column])

tree.nodes(group="this_study").style(fill="red", radius=7)
tree.branches(group="this_study").style(stroke_width=5)
tree.tip_labels(group="this_study").style(font_weight="bold")

for taxon, color in [("Lycosoidea", "blue"), 
                     ("Dictynoidea", "grey"), 
                     ("Araneoidea", "pink"), 
                     ("Dysderoidea", "yellow"), 
                     ("Scytodoidea", "green"), 
                     ("Pholcoidea", "red")]:
    tree.clade_by_taxon(taxon).highlight(fill=color)

tree.to_svg(
    "spiders_tree.svg", 
    mode="ultrametric"
)