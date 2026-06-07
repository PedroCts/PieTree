from pietree.query.selection import NodeSelection

class PieClade(NodeSelection):

    def __init__(self, root, nodes, tips, highlights):
        super().__init__(nodes, highlights)
        self.root = root
        self.nodes = nodes
        self.tips = tips
        self._highlights = highlights

    @property
    def name(self) -> str | None:
        """The name of the clade root node, used as default highlight label."""
        return getattr(self.root, "name", None)