# File: examples/example.py
#
# This is a full working example using the current PieTree API.
#
# Run with:
# python examples/example.py

from pietree import *

# ============================================================
# CREATE TREE
# ============================================================

# Create the root node
root = PieNode(name="LUCA")

# Create the tree
tree = PieTree(root)

# ============================================================
# BUILD TREE STRUCTURE
# ============================================================

# Domains
bacteria = PieNode(name="Bacteria")
archaeplastida = PieNode(name="Archaeplastida")
archaea = PieNode(name="Archaea")
eukarya = PieNode(name="Eukarya")

root.add_child(bacteria, length=0.1)
root.add_child(archaeplastida, length=0.2)
archaeplastida.add_child(eukarya, length=0.1)
archaeplastida.add_child(archaea, length=0.2)

# Eukaryotic kingdoms
animals = PieNode(name="Animals")
plants = PieNode(name="Plants")
fungi = PieNode(name="Fungi")

eukarya.add_child(animals, length=0.3)
eukarya.add_child(plants, length=0.2)
eukarya.add_child(fungi, length=0.1)

# Animal groups
vertebrates = PieNode(name="Vertebrates")
arthropods = PieNode(name="Arthropods")

animals.add_child(vertebrates, length=0.2)
animals.add_child(arthropods, length=0.1)

# Vertebrate species
human = PieNode(name="Homo sapiens")
dog = PieNode(name="Canis lupus familiaris")
cat = PieNode(name="Felis catus")

vertebrates.add_child(human, length=0.3)
vertebrates.add_child(dog, length=0.1)
vertebrates.add_child(cat, length=0.2)

# Arthropods
spider = PieNode(name="Phoneutria nigriventer")
fly = PieNode(name="Drosophila melanogaster")

arthropods.add_child(spider, length=0.3)
arthropods.add_child(fly, length=0.1)

# ============================================================
# BASIC NODE INFORMATION
# ============================================================

print("\n=== ROOT ===")
print(root)

print("\n=== CHILDREN OF EUKARYA ===")
for child in eukarya.children:
    print(child)

# ============================================================
# TREE STATISTICS
# ============================================================

print("\n=== TREE STATS ===")
print(f"Tips: {tree.n_tips}")
print(f"Nodes: {tree.n_nodes}")
print(f"Branches: {tree.n_branches}")

# ============================================================
# NAVIGATION
# ============================================================

print("\n=== NAVIGATION ===")
print(f"Human parent: {human.parent.name}")
print(f"Root children: {[child.name for child in root.children]}")
print(f"Animals children: {[child.name for child in animals.children]}")

# ============================================================
# TIP DETECTION
# ============================================================

print("\n=== TIPS ===")
for node in [human, dog, cat, spider, fly, animals]:
    print(f"{node.name}: is_tip = {node.is_tip}")

# ============================================================
# SUBTREE EXAMPLE
# ============================================================

print("\n=== VERTEBRATE CLADE TREE ===")

# vertebrate_tree = vertebrates.clade_tree
# print(vertebrate_tree)
# walk(vertebrate_tree.root)

# ============================================================
# QUERY TREE
# ============================================================

# ============================================================
# METADATA ANNOTATION
# ============================================================

human.metadata.update({
    "taxonomy": {
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Mammalia",
        "order": "Primates",
        "family": "Hominidae",
        "genus": "Homo",
    },
    "country": "Global",
    "group": "Mammal",
})

dog.metadata.update({
    "taxonomy": {
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Mammalia",
        "order": "Carnivora",
        "family": "Canidae",
        "genus": "Canis",
    },
    "country": "Domestic",
    "group": "Mammal",
})

cat.metadata.update({
    "taxonomy": {
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Mammalia",
        "order": "Carnivora",
        "family": "Felidae",
        "genus": "Felis",
    },
    "country": "Domestic",
    "group": "Mammal",
})

spider.metadata.update({
    "taxonomy": {
        "kingdom": "Animalia",
        "phylum": "Arthropoda",
        "class": "Arachnida",
        "order": "Araneae",
    },
    "country": "Brazil",
    "group": "Arachnid",
})

fly.metadata.update({
    "taxonomy": {
        "kingdom": "Animalia",
        "phylum": "Arthropoda",
        "class": "Insecta",
        "order": "Diptera",
    },
    "country": "Laboratory",
    "group": "Insect",
})


# ============================================================
# QUERY EXAMPLES
# ============================================================

print("\n=== QUERY: ALL MAMMALS ===")

mammals = tree.nodes(group="Mammal")
for node in mammals:
    print(node.name)


print("\n=== QUERY: ALL BRAZILIAN SAMPLES ===")
brazilian = tree.nodes(country="Brazil")

for node in brazilian:
    print(node.name)


print("\n=== QUERY: ALL CARNIVORA ===")

# TODO: Include nodes.where("Carnivora in taxonomy") syntax
carnivora = tree.find_nodes(
    lambda n: "Carnivora" in n.metadata.get("taxonomy", [])
)
for node in carnivora:
    print(node.name)

print("\n=== QUERY: ALL MAMMALIA ===")
mammalia = tree.find_nodes(
    lambda n: "Mammalia" in n.metadata.get("taxonomy", [])
)
for node in mammalia:
    print(node.name)

print("\n=== QUERY: TIPS ONLY ===")

for tip in tree.tips:
    print(tip.name)

print("\n=== QUERY: INTERNAL NODES ONLY ===")

for node in tree.nodes("internal"):
    print(node.name)

print("\n=== QUERY: LONG BRANCHES ===")
# TODO: Implement something better here
long_branches = tree.find_branches(
    lambda b: (
        b.length is not None
        and b.length >= 0.3
    )
)
for branch in long_branches:
    print(
        f"{branch.parent_id} -> "
        f"{branch.child_id} "
        f"(length={branch.length})"
    )
    
# ============================================================
# HIGHLIGHTING
# ============================================================

mammalia = tree.clade(mammals)
mammalia.highlight(fill="blue")
    
# ============================================================
# EXPORT TREE
# ============================================================

# print(vertebrate_tree.to_newick())

mammals.style(fill="red", radius=7)

# vertebrate_tree.to_svg(
#     "vertebrate_tree.svg", 
#     mode="phylogram", 
#     orientation="vertical"
# )

tree.to_svg(
    "life_tree.svg", 
    mode="ultrametric"
)
print("SVGs generated!")


# ============================================================
# EXPECTED OUTPUT
# ============================================================

# === ROOT ===
# PieNode(name=Life, children=3)
#
# === CHILDREN OF EUKARYA ===
# PieNode(name=Animals, children=2)
# PieNode(name=Plants, children=0)
# PieNode(name=Fungi, children=0)
#
# === TREE STATS ===
# Tips: 7
# Nodes: 12
# Branches: 11
#
# === NAVIGATION ===
# Human parent: Vertebrates
# Root children: ['Bacteria', 'Archaea', 'Eukarya']
# Animals children: ['Vertebrates', 'Arthropods']
#
# === TIPS ===
# Homo sapiens: is_tip = True
# Canis lupus familiaris: is_tip = True
# Felis catus: is_tip = True
# Phoneutria nigriventer: is_tip = True
# Drosophila melanogaster: is_tip = True
# Animals: is_tip = False
#
# === SIMPLE RECURSIVE WALK ===
# - Life
#   - Bacteria
#   - Archaea
#   - Eukarya
#     - Animals
#       - Vertebrates
#         - Homo sapiens
#         - Canis lupus familiaris
#         - Felis catus
#       - Arthropods
#         - Phoneutria nigriventer
#         - Drosophila melanogaster
#     - Plants
#     - Fungi

# === VERTEBRATE CLADE TREE ===
# PieTree(tips=3, internal_nodes=1, nodes=4)
