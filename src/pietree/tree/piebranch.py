from typing import Optional, Dict

from pietree.core.pieobject import PieObject
from pietree.label.pielabel import PieLabel
from pietree.style.piestyle import PieBranchStyle

class PieBranch(PieObject):

    def __init__(
        self,
        parent_id: str,
        child_id: str,
        length: Optional[float] = None,
        label: Optional[str] = None,
        support: Optional[Dict[str, float]] = None,
        metadata: Optional[dict] = None
        ):

        super().__init__(metadata)
        self.parent_id = parent_id
        self.child_id = child_id
        self.length = length
        self.support = support
        self.label = PieLabel(text=label or support)
        self.style = PieBranchStyle()
