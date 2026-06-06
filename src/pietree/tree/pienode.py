"""
pienode.py
----------
Core node class for PieTree. A PieNode represents either a tip (leaf) or an
internal node in a phylogenetic tree. Trees are collections of PieNodes
connected via PieBranch objects.
"""

from __future__ import annotations

import json
import uuid
from typing import Generator, Iterator, List, Optional, Tuple

from pietree.core.pieobject import PieObject 

from .piebranch import PieBranch
from pietree.metadata.piemeta import PieMeta
from pietree.style.piestyle import PieNodeStyle


class PieNode(PieObject):
    """
    A node in a phylogenetic tree.

    Each node may have zero or more children (making it a tip or internal node,
    respectively) and at most one parent. Metadata — taxonomy, annotations,
    arbitrary key/value pairs — lives on the node via a PieMeta mapping.

    Parameters
    ----------
    name : str, optional
        Label for the node (required for tips; optional for internal nodes).
    branch_length : float, optional
        Length of the branch connecting this node to its parent. Stored on the
        parent branch object; this parameter is kept for convenient construction.
    metadata : dict, optional
        Initial metadata key/value pairs.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        name: Optional[str] = None,
        branch_length: Optional[float] = None,
        metadata: Optional[dict] = None,
    ):
        from pietree.label.pielabel import PieLabel
        
        super().__init__(metadata)
        
        self.id: str = str(uuid.uuid4())

        self._name: Optional[str] = name
        self.label: PieLabel = PieLabel(text=name)
        self._branch_length: Optional[float] = branch_length  # used only at build time

        self._parent: Optional[PieNode] = None
        self._parent_branch: Optional[PieBranch] = None
        self._children: List[Tuple[PieNode, PieBranch]] = []
        self._tree = None  # back-reference to the owning PieTree, if any
        
        self.style = PieNodeStyle()  # visual styling for rendering (not used in tree logic)

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        kind = "Tip" if self.is_tip else "Root" if self.is_root else "Internal"
        name = f"'{self._name}'" if self._name else "unnamed"
        depth = self.depth
        bl = (
            f", branch_length={self.branch_length:.4g}"
            if self.branch_length is not None
            else ""
        )
        return f"PieNode(type={kind}, name={name}, depth={depth}{bl})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PieNode):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    # ------------------------------------------------------------------
    # Basic identity / label
    # ------------------------------------------------------------------

    @property
    def name(self) -> Optional[str]:
        """Node label. ``None`` for anonymous internal nodes."""
        return self._name

    def rename(self, new_name: str) -> None:
        """Update the node's label in-place."""
        self._name = new_name
        self.label.text = new_name

    # ------------------------------------------------------------------
    # Branch / distance
    # ------------------------------------------------------------------

    @property
    def branch_length(self) -> Optional[float]:
        """Length of the branch from this node to its parent, or ``None``."""
        if self._parent_branch is None:
            return None
        return self._parent_branch.length

    # ------------------------------------------------------------------
    # Structural type checks
    # ------------------------------------------------------------------

    @property
    def is_tip(self) -> bool:
        """``True`` when this node has no children (i.e. it is a leaf/tip)."""
        return len(self._children) == 0

    @property
    def is_leaf(self) -> bool:
        """Alias for :attr:`is_tip`."""
        return self.is_tip

    @property
    def is_internal(self) -> bool:
        """``True`` when this node has at least one child."""
        return not self.is_tip

    @property
    def is_root(self) -> bool:
        """``True`` when this node has no parent."""
        return self._parent is None

    # ------------------------------------------------------------------
    # Parent / root navigation
    # ------------------------------------------------------------------

    @property
    def parent(self) -> Optional[PieNode]:
        """The direct parent node, or ``None`` if this is the root."""
        return self._parent

    @property
    def parent_branch(self) -> Optional[PieBranch]:
        """The branch object connecting this node to its parent."""
        return self._parent_branch

    @property
    def root(self) -> PieNode:
        """The root of the tree containing this node."""
        current = self
        while current._parent is not None:
            current = current._parent
        return current

    @property
    def ancestors(self) -> List[PieNode]:
        """
        Ordered list of ancestor nodes from parent up to (and including) root.
        """
        result: List[PieNode] = []
        current = self._parent
        while current is not None:
            result.append(current)
            current = current._parent
        return result

    def path_to_root(self) -> List[PieNode]:
        """
        Ordered list from *this* node up to (and including) the root.
        Includes self; equivalent to ``[self] + self.ancestors``.
        """
        path: List[PieNode] = []
        current: Optional[PieNode] = self
        while current is not None:
            path.append(current)
            current = current._parent
        return path

    # ------------------------------------------------------------------
    # Children / descendants
    # ------------------------------------------------------------------

    @property
    def children(self) -> List[PieNode]:
        """Direct child nodes."""
        return [c for c, _ in self._children]

    @property
    def branches(self) -> List[PieBranch]:
        """Branch objects connecting this node to each of its children."""
        return [b for _, b in self._children]

    @property
    def children_with_branches(self) -> List[Tuple[PieNode, PieBranch]]:
        """List of ``(child, branch)`` pairs."""
        return list(self._children)

    @property
    def descendants(self) -> List[PieNode]:
        """
        All nodes in the subtree rooted at this node, excluding self.
        Returned in pre-order (parent before children).
        """
        result: List[PieNode] = []
        for child in self.children:
            result.append(child)
            result.extend(child.descendants)
        return result

    @property
    def descendant_tips(self) -> List[PieNode]:
        """All tip nodes in the subtree rooted at this node."""
        return [n for n in self.descendants if n.is_tip]

    @property
    def descendant_tip_names(self) -> List[Optional[str]]:
        """Names of all tip nodes in the subtree rooted at this node."""
        return [n.name for n in self.descendant_tips]

    @property
    def clade(self) -> List[PieNode]:
        """This node plus all of its descendants (pre-order)."""
        return [self, *self.descendants]

    @property
    def clade_tree(self):
        """Return a new PieTree rooted at this node (delegates to the owning tree)."""
        if self._tree is None:
            raise RuntimeError("This node is not attached to a PieTree.")
        return self._tree.clade(self)

    # ------------------------------------------------------------------
    # Siblings / sisters
    # ------------------------------------------------------------------

    @property
    def siblings(self) -> List[PieNode]:
        """All other children of this node's parent (empty list for the root)."""
        if self._parent is None:
            return []
        return [c for c in self._parent.children if c.id != self.id]

    @property
    def sisters(self) -> List[PieNode]:
        """Alias for :attr:`siblings` (phylogenetics convention)."""
        return self.siblings

    # ------------------------------------------------------------------
    # Depth / position
    # ------------------------------------------------------------------

    @property
    def depth(self) -> int:
        """Number of edges from the root to this node (root has depth 0)."""
        return len(self.ancestors)

    # ------------------------------------------------------------------
    # Relationship queries
    # ------------------------------------------------------------------

    def is_ancestor_of(self, other: PieNode) -> bool:
        """Return ``True`` if *self* is a strict ancestor of *other*."""
        return self in other.ancestors

    def is_descendant_of(self, other: PieNode) -> bool:
        """Return ``True`` if *self* is a strict descendant of *other*."""
        return other in self.ancestors

    def mrca(self, other: PieNode) -> PieNode:
        """
        Most Recent Common Ancestor of this node and *other*.

        Raises
        ------
        ValueError
            If the two nodes belong to different trees (no shared ancestor).
        """
        self_ancestors = {n.id: n for n in self.path_to_root()}
        for node in other.path_to_root():
            if node.id in self_ancestors:
                return self_ancestors[node.id]
        raise ValueError(
            f"Nodes '{self.name}' and '{other.name}' share no common ancestor."
        )

    def distance_to(self, other: PieNode) -> float:
        """
        Sum of branch lengths along the path between *self* and *other*.

        Raises
        ------
        ValueError
            If any branch on the path has no length, or nodes are unrelated.
        """
        ancestor = self.mrca(other)

        def length_to_ancestor(node: PieNode, anc: PieNode) -> float:
            total = 0.0
            current = node
            while current.id != anc.id:
                bl = current.branch_length
                if bl is None:
                    raise ValueError(
                        f"Branch above '{current.name}' has no length; "
                        "cannot compute distance."
                    )
                total += bl
                current = current._parent  # type: ignore[assignment]
            return total

        return length_to_ancestor(self, ancestor) + length_to_ancestor(other, ancestor)

    # ------------------------------------------------------------------
    # Tree modification
    # ------------------------------------------------------------------

    def add_child(
        self,
        child: PieNode,
        branch: Optional[PieBranch] = None,
        length: Optional[float] = None,
    ) -> None:
        """
        Attach *child* as a direct child of this node.

        Parameters
        ----------
        child : PieNode
            The node to attach.
        branch : PieBranch, optional
            An existing branch object. If omitted, one is created using *length*.
        length : float, optional
            Branch length; used only when *branch* is not supplied.

        Raises
        ------
        ValueError
            If *child* is the same node as self, or is already a child.
        """
        if child.id == self.id:
            raise ValueError("A node cannot be its own child.")
        if child.id in {c.id for c in self.children}:
            raise ValueError(f"Node '{child.name}' is already a child of '{self.name}'.")

        if branch is None:
            branch = PieBranch(
                parent_id=self.id,
                child_id=child.id,
                length=length,
            )

        child._parent = self
        child._parent_branch = branch
        child._tree = self._tree

        self._children.append((child, branch))

    def remove_child(self, child: PieNode) -> None:
        """
        Detach *child* from this node's child list.

        Raises
        ------
        ValueError
            If *child* is not a direct child of this node.
        """
        before = len(self._children)
        self._children = [(c, b) for c, b in self._children if c.id != child.id]
        if len(self._children) == before:
            raise ValueError(f"Node '{child.name}' is not a child of '{self.name}'.")

        child._parent = None
        child._parent_branch = None

    def detach(self) -> None:
        """
        Remove this node from its parent, making it a free-standing root.
        No-op if already the root.
        """
        if self._parent is not None:
            self._parent.remove_child(self)

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    def walk(self, order: str = "preorder") -> Iterator[PieNode]:
        """
        Iterate over all nodes in the subtree rooted at this node.

        Parameters
        ----------
        order : {'preorder', 'postorder'}
            Traversal order.
            - ``'preorder'``  — parent visited before children (default).
            - ``'postorder'`` — children visited before parent.
        """
        if order == "preorder":
            yield self
            for child, _ in self._children:
                yield from child.walk(order=order)
        elif order == "postorder":
            for child, _ in self._children:
                yield from child.walk(order=order)
            yield self
        else:
            raise ValueError(f"Unknown traversal order: '{order}'. Use 'preorder' or 'postorder'.")

    def iter_tips(self) -> Generator[PieNode, None, None]:
        """Yield only tip (leaf) nodes in the subtree, in pre-order."""
        for node in self.walk():
            if node.is_tip:
                yield node

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    def metadata(self) -> PieMeta:
        """The node's PieMeta mapping."""
        return self._metadata

    def annotate(
        self,
        key: str,
        value,
        overwrite: bool = True,
        normalize: bool = True,
    ) -> None:
        """
        Attach a metadata value to this node.

        Parameters
        ----------
        key : str
            Metadata field name.
        value : any
            Value to store (str, list, dict, numeric, …).
        overwrite : bool
            If ``False``, skip the assignment when *key* already exists.
        normalize : bool
            When ``True`` and *key* is ``'taxonomy'`` and *value* is a raw
            JSON string, the string is parsed into a Python object first.
        """
        if normalize and key == "taxonomy" and isinstance(value, str):
            value = json.loads(value)

        if overwrite or key not in self._metadata:
            self._metadata[key] = value

    def get(self, key: str, default=None):
        """
        Retrieve a metadata value by key, returning *default* if absent.

        Shorthand for ``node.metadata.get(key, default)``.
        """
        return self._metadata.get(key, default)

    def get_taxonomy(self) -> list:
        """Return the stored taxonomy list, or an empty list if unset."""
        return self._metadata.get("taxonomy") or []

    def clear_metadata(self) -> None:
        """Remove all metadata entries from this node."""
        self._metadata.clear()

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self, include_metadata: bool = True) -> dict:
        """
        Serialise this node (but *not* its subtree) to a plain dict.

        Useful for debugging and JSON export.
        """
        d: dict = {
            "id": self.id,
            "name": self._name,
            "is_tip": self.is_tip,
            "depth": self.depth,
            "branch_length": self.branch_length,
            "num_children": len(self._children),
        }
        if include_metadata:
            d["metadata"] = dict(self._metadata)
        return d