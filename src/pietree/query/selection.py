from ast import List
from typing import Optional

from pietree.tree.pienode import PieNode
from collections.abc import Callable

class PieObjectSelection:
    """Base class for filtered selections of PieObjects, with fluent styling methods."""
    def __init__(self, objects):
        self._objs = list(objects)

    def __iter__(self):
        return iter(self._objs)

    def __len__(self):
        return len(self._objs)

    def style(self, **kwargs):
        for obj in self._objs:
            obj.style(**kwargs)
        return self

class NodeSelection(PieObjectSelection):
    """A filtered list of PieNodes with fluent styling."""

    def __init__(self, nodes, highlights):
        super().__init__(nodes)
        self._highlights = highlights

    def highlight(self, **kwargs):
        from pietree.render.layers.highlights import RenderHighlight

        # Auto-label: use clade.name if the caller didn't supply one
        if "label" not in kwargs:
            name = getattr(self, "name", None)
            if name:
                kwargs["label"] = name

        h = RenderHighlight(clade=self, **kwargs)
        self._highlights.append(h)
        return h

    def rename(self, template: str | Callable) -> "NodeSelection":
        """
        Rename all selected nodes using a format string or callable.

        Parameters
        ----------
        template : str or callable
            * **str** — a ``str.format``-style template whose placeholders
              are metadata field names, e.g. ``"{species} {mitogenome_id}"``.
              Nodes whose metadata is missing any placeholder key are
              silently skipped.
            * **callable** — receives ``node.metadata.data`` (a plain dict)
              and must return the new name string.

        Returns
        -------
        NodeSelection
            ``self``, so calls can be chained.

        Examples
        --------
        # Basic rename from metadata fields
        tree.nodes(node_type="tip").rename("{species} {mitogenome_id}")

        # Conditional suffix via lambda
        tree.nodes(node_type="tip").rename(
            lambda m: f"{m['species']} {m['mitogenome_id']}"
                      + (" *" if m.get("group") == "this_study" else "")
        )
        """
        for obj in self._objs:
            try:
                if callable(template):
                    new_name = template(obj.metadata.data)
                else:
                    new_name = template.format(**obj.metadata.data)
                obj.rename(new_name)
            except KeyError:
                continue
        return self

    def suffix(self, text: str) -> "NodeSelection":
        """
        Append *text* to the current name of every selected node.

        Nodes with no name yet are skipped.

        Examples
        --------
        # Mark all this-study tips with an asterisk
        tree.nodes(node_type="tip", group="this_study").suffix(" *")
        """
        for obj in self._objs:
            if obj.name is not None:
                obj.rename(obj.name + text)
        return self

    def prefix(self, text: str) -> "NodeSelection":
        """
        Prepend *text* to the current name of every selected node.

        Nodes with no name yet are skipped.

        Examples
        --------
        tree.nodes(node_type="tip", group="outgroup").prefix("[OG] ")
        """
        for obj in self._objs:
            if obj.name is not None:
                obj.rename(text + obj.name)
        return self

    def mrca(self) -> Optional[PieNode]:
        """Return the most recent common ancestor of the selected nodes."""
        if not self._objs:
            return None
        return self._objs[0].tree.mrca(*self._objs)

class BranchSelection(PieObjectSelection):
    """A filtered list of PieBranches with fluent styling."""
    pass

class LabelSelection(PieObjectSelection):
    """A filtered list of PieLabels with fluent styling."""

    def rename(self, new_name: str) -> "LabelSelection":
        """Update the label's text in-place."""
        for obj in self._objs:
            obj.text = new_name
        return self