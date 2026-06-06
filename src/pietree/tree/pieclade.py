from dataclasses import dataclass, field
from typing import List


@dataclass(slots=False)   # slots=True blocks adding __post_init__ easily
class PieClade:
    root: object
    nodes: list
    tips: list
    _highlights: list = field(default_factory=list, repr=False)

    def highlight(self, **kwargs):
        from pietree.render.layers.highlights import Highlight
        h = Highlight(clade=self, **kwargs)
        self._highlights.append(h)
        return h