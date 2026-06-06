# pietree/tree/pielabel.py

from pietree.style.piestyle import PieLabelStyle


class PieLabel:
    """
    A label attached to a PieObject. Holds the display text and its own style.
    Access via node.label (the PieLabel object, not a string).
    """

    def __init__(self, text: str | None = None):
        self.text: str | None = text
        self.style: PieLabelStyle = PieLabelStyle()

    def __repr__(self):
        return f"PieLabel(text={self.text!r})"

    def __bool__(self):
        return bool(self.text)