"""
pietree.py
----------
The PieTree class: a rooted phylogenetic tree built from PieNode / PieBranch
objects. PieTree is the primary public interface for topology queries,
metadata annotation, rendering, and I/O.
"""

from __future__ import annotations

from typing import Optional

from pietree.render.layers.panels import PanelLayer

from .pienode import PieNode

# Import mixins
from .tree_ops import TreeOpsMixin
from .tree_metadata import TreeMetadataMixin
from .tree_query import TreeQueryMixin
from .tree_edit import TreeEditMixin
from .tree_io import TreeIOMixin

from pietree.metadata.piemeta import PieMeta
from pietree.metadata.registry import MetadataRegistry

from pietree.render.layout import build_layout
from pietree.render.options import RenderOptions
from pietree.render.spec import RenderSpec, RenderNode, RenderEdge
from pietree.render.svg import render_svg

from pietree.query.selection import NodeSelection


class PieTree(
    TreeOpsMixin,
    TreeMetadataMixin,
    TreeQueryMixin,
    TreeEditMixin,
    TreeIOMixin
):
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
        """Check if a node (by name or object) is in this tree."""
        if isinstance(item, str):
            return self.find_tip(item) is not None
        elif isinstance(item, PieNode):
            return item._tree is self
        return False

    # ------------------------------------------------------------------
    # Properties (basic node collections)
    # ------------------------------------------------------------------

    @property
    def all_nodes(self) -> NodeSelection:
        """All nodes in the tree (tips + internal nodes)."""
        return NodeSelection(list(self.traverse()), self._highlights)

    @property
    def tips(self) -> NodeSelection:
        """All tip (leaf) nodes."""
        return NodeSelection([n for n in self.traverse() if n.is_tip], self._highlights)

    @property
    def internal_nodes(self) -> NodeSelection:
        """All internal (non-tip) nodes."""
        return NodeSelection([n for n in self.traverse() if not n.is_tip], self._highlights)

    @property
    def highlights(self) -> list:
        """List of registered highlights for rendering."""
        return self._highlights

    @property
    def panels(self) -> list[PanelLayer]:
        """List of registered panels for rendering."""
        return self._panels

    # ------------------------------------------------------------------
    # Tree-level summary properties
    # ------------------------------------------------------------------

    @property
    def n_tips(self) -> int:
        """Number of tips in the tree."""
        return len(self.tips)

    @property
    def n_nodes(self) -> int:
        """Total number of nodes (tips + internal)."""
        return len(self.all_nodes)

    @property
    def n_branches(self) -> int:
        """Number of branches (edges) in the tree."""
        return len(list(self.iter_branches()))

    @property
    def max_depth(self) -> int:
        """Maximum depth from root to any tip."""
        return max((n.depth for n in self.tips), default=0)

    @property
    def total_branch_length(self) -> Optional[float]:
        """
        Sum of all branch lengths, or None if any branch lacks length.
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
    # Rendering
    # ------------------------------------------------------------------

    def to_render_spec(
        self,
        mode: str = "phylogram",
        orientation: str = "horizontal",
        options: Optional[RenderOptions] = None,
        canvas_size: tuple = (1000, 1000),
        **kwargs,
    ) -> RenderSpec:
        """
        Build a :class:`RenderSpec` — the intermediate representation used by
        all rendering backends.

        Parameters
        ----------
        mode : str, default 'phylogram'
            Layout algorithm (e.g. ``'phylogram'``, ``'cladogram'``, ``'ultrametric'``).
        orientation : str, default 'horizontal'
            ``'vertical'`` or ``'horizontal'``.
        options : RenderOptions, optional
            Visual style; falls back to ``self.render_options``.
        canvas_size : tuple, default (1000, 1000)
            Canvas dimensions (width, height) in pixels.

        Returns
        -------
        RenderSpec
            The render specification containing node positions, edges, and styling.
        """
        canvas_size = canvas_size or (1000, 1000)

        # If extra kwargs are provided (e.g. circular_arc, circular_start_angle),
        # apply them as overrides on a copy of the current render options.
        if kwargs:
            import dataclasses
            base = options or self.render_options
            options = dataclasses.replace(base, **{
                k: v for k, v in kwargs.items()
                if hasattr(base, k)
            })
        else:
            options = options or self.render_options

        coords: dict = build_layout(self, mode=mode, orientation=orientation, options=options)

        # Extract circular metadata before iterating over coords
        circular_meta = coords.pop("_circular_meta", None)

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
            canvas_size=canvas_size,
            circular_meta=circular_meta,
        )

    def to_svg(
        self,
        path: Optional[str] = None,
        mode: str = "phylogram",
        orientation: str = "horizontal",
        canvas_size=(1000, 1000),
        **kwargs
    ) -> Optional[str]:
        """
        Render this tree as an SVG string.

        Parameters
        ----------
        path : str, optional
            If provided, the SVG is also written to this file.
        mode : str, default 'phylogram'
            Layout mode (see :meth:`to_render_spec`).
        orientation : str, default 'horizontal'
            ``'vertical'`` or ``'horizontal'``.
        canvas_size : tuple, default (1000, 1000)
            Canvas dimensions (width, height).
        **kwargs
            Additional render options.

        Returns
        -------
        str or None
            SVG string if path is None, otherwise None.
        """
        resolver = None  # TODO: Implement Resolver logic?

        render_options = RenderOptions(**kwargs) if kwargs else self.render_options
        spec = self.to_render_spec(
            mode=mode,
            orientation=orientation,
            options=render_options,
            canvas_size=canvas_size
        )
        svg = render_svg(spec, resolver=resolver)

        if path:
            with open(path, "w") as fh:
                fh.write(svg)
            return None
        return svg
