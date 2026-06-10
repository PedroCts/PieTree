import pandas as pd
from pietree import PieTree

samples = pd.read_csv("data/insects_samples.csv", sep=";")
tree = PieTree.from_newick(path="data/insects.newick", 
                           support_format="{bootstrap}/{alrt}")


tree.annotate(samples, on="mitogenome_id")
tree.tips.rename("{species} {mitogenome_id}")


# tree.metadata("taxonomy").highlight(values=["Apis"], allow_single_tip=True, label_position="center_right", palette="tab10")
# tree.metadata("taxonomy").highlight(values=["Pheidole"], label_position="center_right", palette="tab10")
tree.metadata("taxonomy").highlight(depth=17, label_position="center_right", palette="tab10")
tree.metadata("taxonomy").highlight(values=["Scymnus"], label_position="center_right", palette="tab10")

tree.metadata("taxonomy").label_nodes(show_duplicates=False)

tree.metadata("group").panel(values=["control"])

tree.savefig("insects_tree.png", size=(1200, 1200))

tree.to_dataframe().to_csv("insects_tree.csv", index=False)

# # Legend Prototype
# mode = "phylogram"
# alignment_mode = "concatenated alignment of 13 mitochondrial PCGs"

# tree_inference = {
#     "software": "IQTree",
#     "method": "Maximum Likelihood",
#     "model": "GTR + I",
#     "bootstrap_mode": "ultrafast bootstrap",
#     "bootstrap": 1000,
#     "alrt": 1000
# }

# pietree_credits = "Figure drawn using PieTree (https://github.com/PedroCts/PieTree)."

# legend = f"""
# {mode.capitalize()} of {len(samples)} arachnid species (accession numbers in Supplementary Table 1) based on the {alignment_mode}. The tree was inferred using {tree_inference["method"]} with the {tree_inference["model"]} substitution model with {tree_inference["bootstrap"]} {tree_inference["bootstrap_mode"]} replicates and {tree_inference["alrt"]} aLRT values. Spiders analyzed in this study (Phoneutria sp., and Loxosceles laeta) grouped within their respective clades, Entelegynae and Haplogynae, as part of the suborder Araneomorphae. Scorpions served as an outgroup. Bootstrap values highlight strong support for spider monophyly (100) and instances of paraphyly in Dictynoidea and Hypochylus thorelli. {pietree_credits}
# """

# print(legend)
