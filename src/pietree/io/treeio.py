import re
from Bio import Phylo

from ..tree.pienode import PieNode
from ..tree.piebranch import PieBranch

# def _tokenize(s: str):
#     return [t for t in re.findall(r"[(),;]|[^(),;]+", s) if t.strip()]

# def _parse_subtree(tokens, i, parent=None):

#     node = PieNode()
#     children = []

#     # -------------------------
#     # INTERNAL NODE
#     # -------------------------
#     if tokens[i] == "(":
#         i += 1

#         while True:

#             child, i = _parse_subtree(tokens, i, parent=node)
#             children.append(child)

#             if i >= len(tokens):
#                 break

#             if tokens[i] == ",":
#                 i += 1
#                 continue

#             if tokens[i] == ")":
#                 i += 1
#                 break

#         # optional label
#         if i < len(tokens) and tokens[i] not in [":", ",", ")", ";"]:
#             node._name = tokens[i]
#             i += 1

#     # -------------------------
#     # LEAF NODE
#     # -------------------------
#     else:
#         node._name = tokens[i]
#         i += 1

#     # -------------------------
#     # BRANCH LENGTH
#     # -------------------------
#     branch_length = None

#     if i < len(tokens) and tokens[i] == ":":
#         i += 1
#         branch_length = float(tokens[i])
#         i += 1

#     # -------------------------
#     # ATTACH TO PARENT
#     # -------------------------
#     if parent is not None:

#         branch = PieBranch(
#             parent_id=parent.id,
#             child_id=node.id,
#             length=branch_length
#         )

#         parent.add_child(node, branch)

#     # IMPORTANT: attach children AFTER parent link exists
#     for c in children:
#         if c not in node.children:
#             # ensure consistency if add_child already handled it
#             pass

#     return node, i

# def parse_newick(newick_str=None, path=None):

#     if newick_str is None:

#         if path is None:
#             raise ValueError("Provide newick_str or path")

#         with open(path) as f:
#             newick_str = f.read().strip()

#     newick_str = newick_str.strip().rstrip(";")

#     tokens = _tokenize(newick_str)

#     root, _ = _parse_subtree(tokens, 0, parent=None)

#     # DO NOT create tree here
#     return root

def _convert_clade(clade, parent_node=None):

    node = PieNode(
        name=clade.name,
        metadata={}
    )

    # attach node metadata if present (support etc.)
    if hasattr(clade, "confidence") and clade.confidence is not None:
        node._metadata["support"] = clade.confidence

    if parent_node is not None:

        branch = PieBranch(
            parent_id=parent_node.id,
            child_id=node.id,
            length=clade.branch_length
        )

        parent_node.add_child(node, branch)

    for child in clade.clades:
        _convert_clade(child, node)

    return node

def parse_newick(newick_str=None, path=None):

    if path is not None:
        bio_tree = Phylo.read(path, "newick")
    else:
        from io import StringIO
        bio_tree = Phylo.read(StringIO(newick_str), "newick")

    root_clade = bio_tree.root

    root = PieNode(name=root_clade.name, metadata={})

    for child in root_clade.clades:
        _convert_clade(child, root)

    return root


def build_newick(tree, path): 
    def _get_branch_length(parent, child): 
        for c, branch in parent._children: 
            if c is child: 
                return branch.length if branch else 0.0 
        return 0.0 

    def _build(node): 
        if node.is_tip: 
            bl = 0.0 
            if node.parent: 
                bl = _get_branch_length(node.parent, node) 
            return f"{node.name or ''}:{bl}" 

        children_str = ",".join(_build(c) for c, _ in node._children) 
        bl = 0.0 
        if node.parent: 
            bl = _get_branch_length(node.parent, node) 
        label = node.name or "" 
        return f"({children_str}){label}:{bl}" 

    if (path): 
        with open(path, "w") as f: 
            f.write(_build(tree.root) + ";") 
    return _build(tree.root) + ";"