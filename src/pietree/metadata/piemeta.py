"""
piemeta.py
----------
PieMeta: the metadata mapping for tree-level and node-level data.
MetadataView: a field-scoped view with fluent high-level operations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pietree.tree.pietree import PieTree


class MetadataView:
    """
    A view over a single metadata field across all nodes in a tree.

    Obtained via:
        tree.metadata("taxonomy")

    Exposes high-level operations on that field — highlighting,
    labeling, panel rendering — as a fluent API.
    """

    def __init__(self, tree: "PieTree", field: str):
        self._tree = tree
        self._field = field

    def __repr__(self) -> str:
        return f"MetadataView(field={self._field!r}, tree={self._tree!r})"

    # --------------------------------------------------
    # Introspection
    # --------------------------------------------------

    @property
    def field(self) -> str:
        """The metadata field name this view is bound to."""
        return self._field

    @property
    def values(self) -> list:
        """All distinct non-None values of this field across all nodes."""
        seen = []
        for node in self._tree.traverse():
            v = node.get(self._field)
            if v is not None and v not in seen:
                seen.append(v)
        return seen

    def __iter__(self):
        """Iterate over (node, value) pairs where value is not None."""
        for node in self._tree.traverse():
            v = node.get(self._field)
            if v is not None:
                yield node, v

    # --------------------------------------------------
    # Inference
    # --------------------------------------------------

    def infer(self) -> dict:
        """
        Infer this field for every node via longest-common-prefix.

        Returns
        -------
        dict
            ``{node_id: list_or_None}`` — does not modify the tree.
        """
        from pietree.metadata.inference import infer_tree
        return infer_tree(self._tree, self._field)

    # --------------------------------------------------
    # Panel
    # --------------------------------------------------

    def panel(self, values=None, show_duplicates: bool = True, **kwargs):
        """Register a side panel for this metadata field on the owning tree."""
        return self._tree.panel(self._field, show_duplicates=show_duplicates, values=values, **kwargs)

    # --------------------------------------------------
    # Highlighting
    # --------------------------------------------------

    def highlight(
        self,
        *,
        show_duplicates: bool = True,
        depth: Optional[int] = None,
        values: Optional[List[str]] = None,
        palette: str = "tab20",
        colors: Optional[Dict[str, str]] = None,
        opacity: float = 0.25,
        label: str | bool = True,
        scattered_label: bool = True,
        label_position: str = "upper_right",
        font_size: float = 11,
        font_color: str = "#444444",
        font_weight: str = "bold",
        padding: float = 10,
        corner_radius: float = 5,
        allow_single_tip: bool = False,
        **kwargs,
    ) -> list:
        """
        Automatically highlight clades grouped by this metadata field.

        Uses hierarchical inference (longest-common-prefix) to determine
        which clade corresponds to each metadata value, then appends one
        :class:`RenderHighlight` per group to the tree.

        Parameters
        ----------
        depth : int, optional
            Hierarchy level to highlight (0 = root taxon).  Omit to use
            the most specific level for each group.
        values : list of str, optional
            Restrict to these taxon names only.
        palette : str
            Named color palette (``'tab20'``, ``'tab10'``, ``'set1'``,
            ``'set2'``, ``'pastel1'``).  Default ``'tab20'``.
        colors : dict, optional
            ``{taxon: hex_color}`` overrides that take precedence over
            the palette.
        opacity : float
            Highlight fill opacity (default 0.25).
        label_position : str
            One of the 9 named grid positions (default ``'upper_right'``).
        font_size, font_color, font_weight
            Label typography.
        padding, corner_radius
            Rect geometry.
        **kwargs
            Forwarded verbatim to :class:`RenderHighlight`.

        Returns
        -------
        list of RenderHighlight
            The highlights that were created and registered.

        Examples
        --------
        >>> tree.metadata("taxonomy").highlight()
        >>> tree.metadata("taxonomy").highlight(depth=1, palette="pastel1")
        >>> tree.metadata("taxonomy").highlight(values=["Mammalia", "Insecta"])
        >>> tree.metadata("taxonomy").highlight(
        ...     colors={"Mammalia": "#4e79a7", "Insecta": "#f28e2b"}
        ... )
        """
        from pietree.metadata.meta_highlight import highlight_metadata

        return highlight_metadata(
            self._tree,
            self._field,
            show_duplicates=show_duplicates,
            depth=depth,
            values=values,
            palette=palette,
            colors=colors,
            opacity=opacity,
            label=label,
            scattered_label=scattered_label,
            label_position=label_position,
            font_size=font_size,
            font_color=font_color,
            font_weight=font_weight,
            padding=padding,
            corner_radius=corner_radius,
            allow_single_tip=allow_single_tip,
            **kwargs,
        )

    # --------------------------------------------------
    # Node labels
    # --------------------------------------------------

    def label_nodes(
        self,
        *,
        show_duplicates: bool = True,
        depth: Optional[int] = None,
        values: Optional[List[str]] = None,
        font_size: float = 10,
        font_color: str = "#444444",
    ) -> list:
        from pietree.metadata.meta_label import label_nodes_metadata
        return label_nodes_metadata(
            self._tree, self._field,
            show_duplicates=show_duplicates,
            depth=depth, values=values,
            font_size=font_size, font_color=font_color,
        )


@dataclass
class PieMeta:

    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, path, default=None):
        current = self.data

        for key in path.split("."):
            if not isinstance(current, dict):
                return default
            current = current.get(key)
            if current is None:
                return default

        return current

    def set(self, path, value):
        keys = path.split(".")
        current = self.data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def update(self, other):
        self._recursive_update(self.data, other)

    def _recursive_update(self, target, source):
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._recursive_update(target[key], value)
            else:
                target[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data
