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

sheet = StyleSheet([
    (
        [
            MetadataSelector("group", "this_study")
        ],
        [
            StyleRule(target="node", fill="red", radius=7),
            StyleRule(target="branch", stroke_width=3)
        ]
    )
])
resolver = StyleResolver(sheet)

for taxon, color in [("Lycosoidea", "blue"), 
                     ("Dictynoidea", "grey"), 
                     ("Araneoidea", "pink"), 
                     ("Dysderoidea", "yellow"), 
                     ("Scytodoidea", "green"), 
                     ("Pholcoidea", "red")]:
    tree.style.highlight(
        tree.clade_by_taxon(taxon),
        fill=color,
    )

tree.to_svg(
    "spiders_tree.svg", 
    mode="ultrametric", 
    orientation="horizontal",
    resolver=resolver
)