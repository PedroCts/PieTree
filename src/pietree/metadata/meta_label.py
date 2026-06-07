from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree

from pietree.metadata.inference import infer_tree


@dataclass
class MetaNodeLabel:
    node_id: str
    text: str
    font_size: float = 10
    font_color: str = "#444444"


def label_nodes_metadata(
    tree: "PieTree",
    field: str,
    *, 
    show_duplicates=True,
    depth: Optional[int] = None,
    values: Optional[List[str]] = None,
    font_size: float = 10,
    font_color: str = "#444444",
) -> List[MetaNodeLabel]:
    
    tree._meta_labels = []

    inferred: Dict = infer_tree(tree, field)
    values_set = set(values) if values is not None else None
    created = []

    for node in tree.traverse():
        if node.is_tip:
            continue

        path = inferred.get(node.id)
        if not path:
            continue

        if depth is not None:
            if depth >= len(path):
                continue
            text = path[depth]
        else:
            text = path[-1]  # deepest inferred level

        if values_set is not None and text not in values_set:
            continue

        label = MetaNodeLabel(
            node_id=node.id,
            text=text,
            font_size=font_size,
            font_color=font_color,
        )
        
        if not show_duplicates and tree._meta_registry.is_claimed(field, text):
            continue
        tree._meta_registry.claim(field, text, "label_nodes")
        
        tree._meta_labels.append(label)
        created.append(label)
        
    # Remove redundant ancestor labels: if a node and an ancestor share the
    # same label text, keep only the ancestor.
    labeled_ids = {ml.node_id: ml for ml in created}

    node_lookup = {n.id: n for n in tree.traverse()}

    to_remove = set()
    for ml in created:
        node = node_lookup[ml.node_id]
        for ancestor in node.ancestors:
            desc_label = labeled_ids.get(ancestor.id)
            if desc_label and desc_label.text == ml.text:
                to_remove.add(ml.node_id)
                break

    created = [ml for ml in created if ml.node_id not in to_remove]
    tree._meta_labels = [ml for ml in tree._meta_labels if ml.node_id not in to_remove]

    return created