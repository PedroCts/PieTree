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
    pass

class BranchSelection(PieObjectSelection):
    """A filtered list of PieBranches with fluent styling."""
    pass

class LabelSelection(PieObjectSelection):
    """A filtered list of PieLabels with fluent styling."""
    pass