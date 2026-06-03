import pandas as pd
import json
from pietree import *
from pietree.style import *

samples = pd.read_csv("data/spider_samples.csv", sep=";")
tree = PieTree.from_newick(path="data/spiders.newick")

for _, sample in samples.iterrows():
    tip = tree.find_tip(sample["mitogenome_id"])
    tip.rename(f"{sample['species']} {sample['mitogenome_id']}")
    if not tip: continue
    for column in sample.index:
        tip.annotate(column, sample[column])

tree.nodes(group="this_study").style(fill="red", radius=7)
tree.branches(group="this_study").style(stroke_width=3)

for taxon, color in [("Lycosoidea", "blue"), 
                     ("Dictynoidea", "grey"), 
                     ("Araneoidea", "pink"), 
                     ("Dysderoidea", "yellow"), 
                     ("Scytodoidea", "green"), 
                     ("Pholcoidea", "red")]:
    tree.clade_by_taxon(taxon).highlight(fill=color)

tree.to_svg(
    "spiders_tree.svg", 
    mode="ultrametric", 
    orientation="horizontal"
)