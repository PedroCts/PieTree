import pandas as pd
from pietree import PieTree

samples = pd.read_csv("data/spider_samples.csv", sep=";")
tree = PieTree.from_newick(path="data/spiders.newick")

tree.annotate(samples, on="mitogenome_id")
tree.tips.rename("{species} {mitogenome_id}")

tree.nodes(group="this_study").style(fill="red", radius=5)
tree.tip_labels(group="this_study").style(font_weight="bold")

tree.metadata("taxonomy").highlight(depth=9, label_position="center_right", palette="tab10")
tree.metadata("taxonomy").label_nodes(show_duplicates=False)

tree.metadata("group").highlight(values=["this_study"], font_size=8, label_position="center_right", label="This study", colors={"this_study": "#7e7e7e"})
tree.metadata("group").panel(values=["Outgroup"])

tree.to_svg("spiders_tree.svg", canvas_size=(900, 900))

