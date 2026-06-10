from dataclasses import dataclass, fields

@dataclass
class PieStyle:

    opacity: float = 1.0
    visible: bool = True
    orientation: int = 0

    def __call__(self, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(
                    f"Unknown style attribute '{key}'"
                )
            setattr(self, key, value)
        return self

    def apply_to_rule(self, rule):
        """Merge this PieStyle's non-None values onto a StyleRule, as final overrides."""
        for field in fields(self):
            value = getattr(self, field.name)
            if value is not None:
                setattr(rule, field.name, value)
        return rule

@dataclass
class PieNodeStyle(PieStyle):
    fill: str | None = None
    radius: float | None = None
    width: float | None = None
    stroke: str | None = None
    stroke_width: float | None = None

    def __call__(self, **kwargs):
        super().__call__(**kwargs)
        return self

@dataclass
class PieBranchStyle(PieStyle):
    stroke: str | None = None
    stroke_width: float | None = None

    def __call__(self, **kwargs):
        super().__call__(**kwargs)
        return self

@dataclass
class PieLabelStyle(PieStyle):

    font_size: float | None = None
    font_color: str | None = None
    font_weight: str | None = None   # "bold", "normal", "600", etc.
    font_style: str | None = None    # "italic", "normal"
    text_decoration: str | None = None  # "underline", "none"

    def __call__(self, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"Unknown label style attribute '{key}'")
            setattr(self, key, value)
        return self
