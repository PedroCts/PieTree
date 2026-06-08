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
