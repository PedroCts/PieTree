"""
pietree.py
----------
The PieTree class: a rooted phylogenetic tree built from PieNode / PieBranch
objects. PieTree is the primary public interface for topology queries,
metadata annotation, rendering, and I/O.
"""

from __future__ import annotations

import copy
from typing import Callable, Dict, Iterable, Iterator, List, Literal, Optional, Union

import pandas as pd

from pietree.render.layers.panels import PanelLayer

from .pienode import PieNode
from .piebranch import PieBranch
from .pieclade import PieClade

from pietree.io.treeio import parse_newick, build_newick
from pietree.metadata.piemeta import PieMeta
from pietree.metadata.registry import MetadataRegistry

from pietree.render.layout import build_layout
from pietree.render.options import RenderOptions
from pietree.render.spec import RenderSpec, RenderNode, RenderEdge
from pietree.render.svg import render_svg

from pietree.query.selection import NodeSelection, BranchSelection, LabelSelection


# Type aliases
NodeFilter = Callable[[PieNode], bool]
BranchFilter = Callable[[PieBranch], bool]
NodeOrName = Union[PieNode, str]


class PieTree:
    """
    A rooted phylogenetic tree.

    The tree owns a single root :class:`PieNode`; all other nodes and branches
    are reachable from it. PieTree provides the high-level interface for:

    - **Node / branch access** — tips, internals, all nodes, branches.
    - **Lookup** — by name, id, or arbitrary predicate.
    - **Topology queries** — MRCA, distance, clade extraction.
    - **Metadata annotation** — from dicts or DataFrames, to any/all nodes.
    - **Editing** — reroot, prune, induced subtree.
    - **I/O** — Newick in/out.
    - **Rendering** — SVG via a layout + style pipeline.

    Parameters
    ----------
    root : PieNode
        The root node of the tree. All nodes must be reachable from it.
    metadata : dict, optional
        Tree-level metadata (not node metadata).
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, root: PieNode, metadata: Optional[dict] = None):
        self.root: PieNode = root
        self._metadata: PieMeta = PieMeta(metadata or {})
        # Rendering
        self.render_options: RenderOptions = RenderOptions()
        self._highlights: list = []
        self._panels: list = []
        self._meta_labels: list = []   # ephemeral; set by metadata().label_nodes()
        self._meta_registry: MetadataRegistry = MetadataRegistry()
        # Wire every reachable node back to this tree
        self._register_tree(root)

    def _register_tree(self, node: PieNode) -> None:
        """Recursively set ``node._tree = self`` for the whole subtree."""
        node._tree = self
        for child in node.children:
            self._register_tree(child)

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"PieTree("
            f"tips={len(self.tips)}, "
            f"internal_nodes={len(self.internal_nodes)}, "
            f"nodes={len(self.all_nodes)}"
            f")"
        )

    def __len__(self) -> int:
        """Number of tips (the conventional size of a phylogenetic tree)."""
        return len(self.tips)

    def __contains__(self, item: object) -> bool:
        """``node in tree`` — ``True`` if the node (or name) belongs to this tree."""
        if isinstance(item, PieNode):
            return any(n.id == item.id for n in self.traverse())
        if isinstance(item, str):
            return self.find_tip(item) is not None or self.find_node_by_name(item) is not None
        return False

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def metadata(self, field: Optional[str] = None):
        """
        With no argument: return the raw PieMeta object (tree-level metadata).
        With a field name: return a MetadataView for that field across all nodes.

        Usage:
            tree.metadata()            # → PieMeta
            tree.metadata("taxonomy")  # → MetadataView
        """
        if field is None:
            return self._metadata
        from pietree.metadata.piemeta import MetadataView
        return MetadataView(tree=self, field=field)

    # ------------------------------------------------------------------
    # Node access
    # ------------------------------------------------------------------

    @property
    def all_nodes(self) -> NodeSelection:
        """All nodes in pre-order traversal (root first)."""
        return NodeSelection(list(self.traverse()), highlights=self._highlights)

    @property
    def tips(self) -> NodeSelection:
        """All tip (leaf) nodes."""
        return NodeSelection([n for n in self.traverse() if n.is_tip], highlights=self._highlights)

    @property
    def tip_names(self) -> List[Optional[str]]:
        """Names of all tip nodes."""
        return [n.name for n in self.tips]

    @property
    def internal_nodes(self) -> NodeSelection:
        """All internal (non-leaf) nodes."""
        return NodeSelection([n for n in self.traverse() if n.is_internal], highlights=self._highlights)

    def nodes(
        self,
        node_type: Literal["all", "tip", "internal"] = "all",
        **metadata_filters
    ) -> NodeSelection:
        """
        Return nodes filtered by type.

        Parameters
        ----------
        node_type : {'all', 'tip', 'internal'}
            Which subset to return.
        """
        if node_type == "tip":
            candidates = self.tips
        elif node_type == "internal":
            candidates = self.internal_nodes
        else:
            candidates = self.all_nodes

        if metadata_filters:
            def matches(node):
                for key, value in metadata_filters.items():
                    if node.get(key) != value:
                        return False
                return True
            candidates = [n for n in candidates if matches(n)]

        return NodeSelection(candidates, highlights=self._highlights)

    # ------------------------------------------------------------------
    # Branch access
    # ------------------------------------------------------------------

    def branches(self, **metadata_filters) -> BranchSelection:
        candidates = list(self.iter_branches())

        if metadata_filters:
            def matches(branch):
                for key, value in metadata_filters.items():
                    meta = branch._metadata
                    if meta.get(key) != value:
                        return False
                return True
            candidates = [b for b in candidates if matches(b)]

        return BranchSelection(candidates)

    def iter_branches(self) -> Iterator[PieBranch]:
        """Yield every branch object in pre-order (by parent node)."""
        for node in self.traverse():
            for _, branch in node._children:
                # Guard: create a branch on the fly if somehow missing
                if branch is None:
                    branch = PieBranch(
                        parent_id=node.id,
                        child_id=None,
                        length=None,
                    )
                yield branch
                
    # ------------------------------------------------------------------
    # Label access
    # ------------------------------------------------------------------
    def labels(
        self,
        target: str = "all",   # "all" | "tip" | "internal"
        **metadata_filters,
    ) -> LabelSelection:
        if target == "tip":
            candidates = self.tips
        elif target == "internal":
            candidates = self.internal_nodes
        else:
            candidates = self.all_nodes

        if metadata_filters:
            def matches(node):
                return all(node.get(k) == v for k, v in metadata_filters.items())
            candidates = [n for n in candidates if matches(n)]

        return LabelSelection(n.label for n in candidates)
    
    def tip_labels(self, **metadata_filters) -> LabelSelection:
        return self.labels(target="tip", **metadata_filters)

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    def traverse(self, order: str = "preorder") -> Iterator[PieNode]:
        """
        Iterate over every node in the tree.

        Parameters
        ----------
        order : {'preorder', 'postorder'}
            Traversal order passed through to :meth:`PieNode.walk`.
        """
        yield from self.root.walk(order=order)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def find_tip(self, name: str) -> Optional[PieNode]:
        """Return the first tip node whose name matches *name*, or ``None``."""
        for tip in self.tips:
            if tip.name == name:
                return tip
        return None

    def find_node_by_id(self, node_id: str) -> Optional[PieNode]:
        """Return the node with the given UUID string, or ``None``."""
        for node in self.traverse():
            if node.id == node_id:
                return node
        return None

    def find_node_by_name(self, name: str) -> Optional[PieNode]:
        """
        Return the first node (tip or internal) whose name matches *name*.

        Prefer :meth:`find_tip` when you know the target is a leaf.
        """
        for node in self.traverse():
            if node.name == name:
                return node
        return None

    def find_nodes(self, predicate: NodeFilter) -> List[PieNode]:
        """Return all nodes for which *predicate(node)* is ``True``."""
        return [n for n in self.traverse() if predicate(n)]

    def find_branches(self, predicate: BranchFilter) -> List[PieBranch]:
        """Return all branches for which *predicate(branch)* is ``True``."""
        return [b for b in self.iter_branches() if predicate(b)]

    def query(
        self,
        func: Optional[NodeFilter] = None,
        **kwargs,
    ) -> List[PieNode]:
        """
        Flexible node query.

        Pass a callable *func* to filter by any logic, or keyword arguments
        to match node attributes by equality.

        Examples
        --------
        >>> tree.query(is_tip=True)
        >>> tree.query(func=lambda n: "brazil" in (n.get("country") or ""))
        """
        results = []
        for node in self.traverse():
            if func is not None:
                if func(node):
                    results.append(node)
            elif all(getattr(node, k, None) == v for k, v in kwargs.items()):
                results.append(node)
        return results

    # ------------------------------------------------------------------
    # MRCA & distance
    # ------------------------------------------------------------------

    def mrca(self, nodes: List[PieNode]) -> Optional[PieNode]:
        """
        Most Recent Common Ancestor of a list of nodes.

        Returns ``None`` for an empty list; returns the node itself for a
        singleton. For two or more nodes, returns the deepest node that is
        an ancestor of all of them.

        Parameters
        ----------
        nodes : list of PieNode
        """
        if not nodes:
            return None
        if len(nodes) == 1:
            return nodes[0]

        # Intersection of ancestor sets; start from the first node's path
        common: set = set(nodes[0].path_to_root())
        for node in nodes[1:]:
            common &= set(node.path_to_root())

        if not common:
            return None

        # Deepest = first node in path_to_root that is in common
        for n in nodes[0].path_to_root():
            if n in common:
                return n

        return None  # unreachable, but satisfies type-checker

    def distance(
        self,
        node1: PieNode,
        node2: PieNode,
        weighted: bool = False,
    ) -> float:
        """
        Path distance between two nodes.

        Parameters
        ----------
        node1, node2 : PieNode
        weighted : bool
            If ``True``, sum branch lengths; if ``False``, count edges.

        Raises
        ------
        ValueError
            If *weighted* is ``True`` but a branch on the path has no length.
        """
        ancestor = self.mrca([node1, node2])
        if ancestor is None:
            raise ValueError("Nodes share no common ancestor in this tree.")

        def dist_to_ancestor(node: PieNode, anc: PieNode) -> float:
            total = 0.0
            current = node
            while current != anc:
                if current.parent is None:
                    break
                if weighted:
                    branch = current.parent_branch
                    if branch is None or branch.length is None:
                        raise ValueError(
                            f"Branch above '{current.name}' has no length; "
                            "set weighted=False or add branch lengths."
                        )
                    total += branch.length
                else:
                    total += 1.0
                current = current.parent  # type: ignore[assignment]
            return total

        return dist_to_ancestor(node1, ancestor) + dist_to_ancestor(node2, ancestor)

    # ------------------------------------------------------------------
    # Clade / subtree
    # ------------------------------------------------------------------

    def clade(self, nodes: Union[PieNode, List[PieNode]], allow_single_tip: bool = False) -> PieClade:
        """
        Return the clade (subtree) defined by *nodes*.

        If *nodes* is a list, the clade is rooted at their MRCA.
        If *nodes* is a single :class:`PieNode`, that node is the clade root.

        Parameters
        ----------
        nodes : PieNode or list of PieNode
        """
        root = self.mrca(nodes) if isinstance(nodes, list) else nodes
        if allow_single_tip:  
            tips = [root] if root.is_tip else root.descendant_tips
        else:
            tips = root.descendant_tips
        
        return PieClade(
            root=root,
            nodes=[root] + root.descendants,
            tips=tips,
            highlights=self._highlights,
        )

    def find_tips_by_taxon(self, taxon: str) -> List[PieNode]:
        """Return all tip nodes whose taxonomy list contains *taxon*."""
        return self.find_nodes(
            lambda n: n.is_tip and taxon in n.get_taxonomy()
        )

    def clade_by_taxon(self, taxon: str) -> PieClade:
        """Return the clade spanning all tips annotated with *taxon*."""
        tips = self.find_tips_by_taxon(taxon)
        return self.clade(tips)

    def induced_subtree(self, tips: List[PieNode]) -> Optional[PieTree]:
        """
        Build the minimal subtree that connects *tips* to each other and the
        root, preserving topology and metadata but cloning all nodes.

        Returns ``None`` if *tips* is empty.
        """
        if not tips:
            return None

        # Collect every node on any path from a tip to the root
        included: set = set()
        for t in tips:
            included.update(t.path_to_root())

        # The subtree root is the included node closest to the overall root
        root_candidates = [n for n in included if n.parent not in included]
        subtree_root = root_candidates[0]

        def clone(node: PieNode) -> Optional[PieNode]:
            if node not in included:
                return None
            new = PieNode(
                name=node.name,
                branch_length=node.branch_length,
                metadata=dict(node._metadata),
            )
            for child in node.children:
                child_clone = clone(child)
                if child_clone is not None:
                    new.add_child(child_clone, length=child.branch_length)
            return new

        cloned = clone(subtree_root)
        return PieTree(cloned) if cloned else None

    def subtree_from_tip_names(self, names: List[str]) -> Optional[PieTree]:
        """
        Convenience wrapper: build an induced subtree from a list of tip names.

        Names that don't match any tip are silently ignored.
        """
        tips = [t for t in (self.find_tip(n) for n in names) if t is not None]
        return self.induced_subtree(tips)

    def prune(self, tips: List[NodeOrName]) -> None:
        """
        Remove *tips* from the tree in-place.

        Each tip is detached from its parent. If detaching leaves the parent
        with only one remaining child (and the parent is not the root), that
        parent is also collapsed to keep the tree properly resolved.

        Parameters
        ----------
        tips : list of PieNode or str
            Tips to remove. Strings are resolved via :meth:`find_tip`.

        Raises
        ------
        ValueError
            If a name cannot be resolved or a non-tip node is given.
        """
        resolved: List[PieNode] = []
        for item in tips:
            if isinstance(item, str):
                node = self.find_tip(item)
                if node is None:
                    raise ValueError(f"No tip named '{item}'.")
                resolved.append(node)
            elif item.is_tip:
                resolved.append(item)
            else:
                raise ValueError(f"Node '{item.name}' is not a tip; can only prune tips.")

        for tip in resolved:
            parent = tip.parent
            tip.detach()

            # Collapse a now-unary internal node (skip root)
            if parent is not None and parent.parent is not None and len(parent.children) == 1:
                grandparent = parent.parent
                only_child = parent.children[0]
                # Transfer child up, summing branch lengths where possible
                old_bl = parent.branch_length
                child_bl = only_child.branch_length
                new_bl: Optional[float] = None
                if old_bl is not None and child_bl is not None:
                    new_bl = old_bl + child_bl
                grandparent.remove_child(parent)
                grandparent.add_child(only_child, length=new_bl)

    # ------------------------------------------------------------------
    # Access highlights and panels
    # ------------------------------------------------------------------
    @property
    def highlights(self) -> list:
        return self._highlights

    @property
    def panels(self) -> list[PanelLayer]:
        return self._panels

    def panel(self, field: str, values: None | list[str], **kwargs) -> PanelLayer:
        """
        Register a metadata side panel for the given field.

        Each call adds one panel column. Columns are automatically
        indexed left to right in registration order.

        Usage:
            tree.panel("taxonomy")
            tree.panel("clade", color="steelblue", font_size=10)
        """
        from pietree.render.layers.panels import PanelLayer
        p = PanelLayer(field=field, index=len(self._panels), values=values, **kwargs)
        self._panels.append(p)
        return p
    
    # ------------------------------------------------------------------
    # Rerooting
    # ------------------------------------------------------------------

    def reroot(self, new_root: Optional[PieNode], inplace: bool = True) -> PieTree:
        """
        Reroot the tree at *new_root*.

        Keeps the same :class:`PieNode` and :class:`PieBranch` objects
        (identity-preserving). Reverses parent pointers along the path from
        *new_root* to the old root.

        Parameters
        ----------
        new_root : PieNode or None
            The node that should become the new root. No-op if ``None``.
        inplace : bool
            If ``False``, returns a deep clone rerooted at the equivalent node.
        """
        if new_root is None:
            return self

        if not inplace:
            cloned = self._deep_clone()
            # Find the equivalent node in the clone by id
            equiv = cloned.find_node_by_id(new_root.id)
            return cloned.reroot(equiv, inplace=True)

        # Walk from new_root up to the old root, reversing pointers
        current: Optional[PieNode] = new_root
        prev: Optional[PieNode] = None
        prev_branch: Optional[PieBranch] = None

        while current is not None:
            parent = current._parent
            original_branch = current._parent_branch

            # Reverse parent pointer
            current._parent = prev
            current._parent_branch = prev_branch

            if prev is not None:
                # Remove 'prev' from current's children (it was already there
                # from an earlier iteration before the pointer flip)
                current._children = [
                    (c, b) for c, b in current._children if c is not prev
                ]
                # Re-add current as a child of prev, reusing the branch
                reused = prev_branch or original_branch or PieBranch(
                    parent_id=prev.id,
                    child_id=current.id,
                    length=None,
                )
                prev._children.append((current, reused))

            prev = current
            prev_branch = original_branch
            current = parent

        self.root = new_root
        self.root._parent = None
        self.root._parent_branch = None

        return self

    def _deep_clone(self) -> PieTree:
        """Return a structurally independent deep copy of this tree."""
        def clone_node(node: PieNode) -> PieNode:
            new = PieNode(
                name=node.name,
                branch_length=node.branch_length,
                metadata=copy.deepcopy(dict(node._metadata)),
            )
            new.id = node.id  # preserve identity so callers can look up by id
            for child, branch in node._children:
                child_clone = clone_node(child)
                child_clone._parent = new
                child_clone._parent_branch = branch  # reuse branch reference
                new._children.append((child_clone, branch))
            return new

        cloned_root = clone_node(self.root)
        return PieTree(cloned_root, metadata=copy.deepcopy(dict(self._metadata)))

    # ------------------------------------------------------------------
    # Metadata annotation
    # ------------------------------------------------------------------

    def annotate(
        self,
        metadata_df: pd.DataFrame,
        on: str = "name",
        overwrite: bool = True,
    ) -> "PieTree":
        """
        Annotate tree nodes from a :class:`pandas.DataFrame`.

        Each row is matched to a node by comparing the *on* column value
        against each node's ``name`` (default), ``id``, or any metadata
        field already stored on the node.

        Parameters
        ----------
        metadata_df : DataFrame
            Must contain a column named *on*. All other columns become
            node metadata keys.
        on : str
            The DataFrame column whose values are matched against node
            names.  Pass ``"name"`` (default) to match against
            ``node.name``; pass ``"id"`` to match against the UUID;
            or pass any other column name (e.g. ``"mitogenome_id"``) to
            match against a metadata field of the same name already
            stored on each node **or** against ``node.name`` when the
            column name happens to equal ``"name"``.

            The most common pattern — where the join column is whatever
            the newick tip labels are — works with any column name:

                tree.annotate(samples, on="mitogenome_id")

        overwrite : bool
            Whether incoming values overwrite existing metadata keys.

        Returns
        -------
        PieTree
            ``self``, for optional method chaining.
        """
        if on not in metadata_df.columns:
            raise ValueError(
                f"Column '{on}' not found in DataFrame. "
                f"Available columns: {list(metadata_df.columns)}"
            )

        mapping: Dict[str, dict] = {}
        for _, row in metadata_df.iterrows():
            row_dict = row.to_dict()
            key = row_dict.get(on, None)
            if key is not None:
                mapping[str(key)] = row_dict

        self.annotate_dict(mapping, on=on, overwrite=overwrite)
        return self

    def annotate_dict(
        self,
        metadata: Dict[str, dict],
        on: str = "name",
        overwrite: bool = True,
    ) -> "PieTree":
        """
        Annotate tree nodes from a plain dictionary.

        Parameters
        ----------
        metadata : dict
            Mapping of node identifier → ``{field: value, …}``.

            Example::

                {
                    "sample_1": {"haplogroup": "H1a1", "country": "Brazil"},
                    "sample_2": {"haplogroup": "U5"},
                }

        on : str
            The field used to look up nodes.

            * ``"name"`` (default) — match against ``node.name``.
            * ``"id"`` — match against the node's UUID string.
            * Any other string — match against a metadata field of that
              name already stored on each node (e.g. ``"mitogenome_id"``
              or ``"accession"``).

        overwrite : bool
            Whether incoming values overwrite existing metadata keys.

        Returns
        -------
        PieTree
            ``self``, for optional method chaining.
        """
        lookup: Dict[str, PieNode] = {}
        named_nodes: List[PieNode] = []  # candidates for substring fallback
        for node in self.traverse():
            if on == "name":
                if node.name is not None:
                    lookup[node.name] = node
            elif on == "id":
                lookup[node.id] = node
            else:
                # Arbitrary metadata field — e.g. "mitogenome_id"
                val = node.get(on)
                if val is not None:
                    lookup[str(val)] = node
                elif node.name is not None:
                    # Collect for substring fallback: newick labels often
                    # embed the join value as a token, e.g.
                    # "Agelena silvatica NC_033971.1" contains "NC_033971.1"
                    named_nodes.append(node)

        for key, values in metadata.items():
            node = lookup.get(str(key))
            if node is None and named_nodes:
                # Substring fallback
                for candidate in named_nodes:
                    if str(key) in candidate.name:
                        node = candidate
                        lookup[str(key)] = candidate  # cache hit
                        break
            if node is None:
                continue
            for k, v in values.items():
                node.annotate(k, v, overwrite=overwrite)

        return self

    def annotate_all(
        self,
        key: str,
        value,
        node_type: Literal["all", "tip", "internal"] = "all",
    ) -> None:
        """
        Set the same metadata *key*/*value* on every node of the given type.

        Useful for broadcasting a tree-wide flag or resetting a field.
        """
        for node in self.nodes(node_type):
            node.annotate(key, value)

    def clear_all_metadata(
        self,
        node_type: Literal["all", "tip", "internal"] = "all",
    ) -> None:
        """Clear all metadata from every node of the given type."""
        for node in self.nodes(node_type):
            node.clear_metadata()

    def to_dataframe(
        self,
        node_type: Literal["all", "tip", "internal"] = "tip",
        include_topology: bool = True,
    ) -> pd.DataFrame:
        """
        Export node metadata (and optionally topology fields) to a DataFrame.

        Parameters
        ----------
        node_type : {'all', 'tip', 'internal'}
            Which nodes to include (default: tips only).
        include_topology : bool
            If ``True``, prepend columns: ``id``, ``name``, ``depth``,
            ``branch_length``, ``is_tip``.
        """
        rows = []
        for node in self.nodes(node_type):
            row: dict = {}
            if include_topology:
                row["id"] = node.id
                row["name"] = node.name
                row["depth"] = node.depth
                row["branch_length"] = node.branch_length
                row["is_tip"] = node.is_tip
            row.update(dict(node.metadata))
            rows.append(row)
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Statistics / summary
    # ------------------------------------------------------------------

    @property
    def n_tips(self) -> int:
        """Number of tips."""
        return len(self.tips)

    @property
    def n_nodes(self) -> int:
        """Total number of nodes (tips + internal)."""
        return len(self.all_nodes)
    
    @property
    def n_branches(self) -> int:
        """Number of branches."""
        return len(self.branches())

    @property
    def max_depth(self) -> int:
        """Maximum depth of any node (i.e. height of the tree in edges)."""
        return max(n.depth for n in self.traverse())

    @property
    def total_branch_length(self) -> Optional[float]:
        """
        Sum of all branch lengths, or ``None`` if any branch lacks a length.
        """
        total = 0.0
        for branch in self.iter_branches():
            if branch.length is None:
                return None
            total += branch.length
        return total

    def is_bifurcating(self) -> bool:
        """``True`` if every internal node has exactly two children."""
        return all(len(n.children) == 2 for n in self.internal_nodes)

    def is_ultrametric(self, tol: float = 1e-6) -> bool:
        """
        ``True`` if all tips are equidistant from the root (within *tol*).

        Requires all branches to have lengths.
        """
        distances = []
        for tip in self.tips:
            try:
                distances.append(self.distance(self.root, tip, weighted=True))
            except ValueError:
                return False
        if not distances:
            return True
        return (max(distances) - min(distances)) < tol

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    @classmethod
    def from_newick(
        cls,
        newick_str: Optional[str] = None,
        path: Optional[str] = None,
    ) -> PieTree:
        """
        Parse a Newick string or file into a :class:`PieTree`.

        Parameters
        ----------
        newick_str : str, optional
            A Newick-formatted string.
        path : str, optional
            Path to a file containing a Newick string.
        """
        root = parse_newick(newick_str=newick_str, path=path)
        return cls(root)  # __init__ calls _register_tree

    def to_newick(self, path: Optional[str] = None) -> str:
        """
        Serialise this tree to a Newick string.

        Parameters
        ----------
        path : str, optional
            If given, also write the string to this file path.
        """
        return build_newick(self, path=path)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def to_render_spec(
        self,
        mode: str = "phylogram",
        orientation: str = "vertical",
        options: Optional[RenderOptions] = None,
        canvas_size: tuple = (1000, 1000)
    ) -> RenderSpec:
        """
        Build a :class:`RenderSpec` — the intermediate representation used by
        all rendering backends.

        Parameters
        ----------
        mode : str
            Layout algorithm (e.g. ``'phylogram'``, ``'cladogram'``).
        orientation : str
            ``'vertical'`` or ``'horizontal'``.
        options : RenderOptions, optional
            Visual style; falls back to ``self.render_options``.
        """
        coords: dict = build_layout(self, mode=mode, orientation=orientation)
        options = options or self.render_options

        nodes = [
            RenderNode(
                id=n.id,
                x=coords[n.id][0],
                y=coords[n.id][1],
                label=n.name,
                node=n,
            )
            for n in self.all_nodes
        ]

        edges = [
            RenderEdge(
                source=b.parent_id,
                target=b.child_id,
                length=b.length,
                label=b.label,
                metadata=b.metadata if b.metadata else None,
                branch=b,
            )
            for b in self.branches()
        ]

        return RenderSpec(
            nodes=nodes,
            edges=edges,
            width=max(x for x, _ in coords.values()) + 1,
            height=max(y for _, y in coords.values()) + 1,
            mode=mode,
            orientation=orientation,
            options=options,
            scale_bar={
                "position": "bottom_left",
                "padding": 30
            },
            highlights=self._highlights,
            panels=self._panels,
            meta_labels=self._meta_labels,
            registry=self._meta_registry,
            canvas_size=canvas_size
        )

    def to_svg(
        self,
        path: Optional[str] = None,
        mode: str = "phylogram",
        orientation: str = "horizontal",
        canvas_size=(1000, 1000),
        **kwargs
    ) -> str:
        """
        Render this tree as an SVG string.

        Parameters
        ----------
        path : str, optional
            If provided, the SVG is also written to this file.
        mode : str
            Layout mode (see :meth:`to_render_spec`).
        orientation : str
            ``'vertical'`` or ``'horizontal'``.
        options : RenderOptions, optional
            Overrides ``self.render_options`` for this render only.
        """
        
        # TODO: Implement Resolver logic
        resolver = None
        
        render_options = RenderOptions(**kwargs) if kwargs else self.render_options
        spec = self.to_render_spec(mode=mode, orientation=orientation, options=render_options, canvas_size=canvas_size)
        svg = render_svg(spec, resolver=resolver)

        if path:
            with open(path, "w") as fh:
                fh.write(svg)

        return svg