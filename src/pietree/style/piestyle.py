from dataclasses import dataclass


@dataclass
class PieStyle:

    fill: str | None = None

    stroke: str | None = None
    stroke_width: float | None = None

    radius: float | None = None

    font_size: float | None = None
    font_color: str | None = None

    width: float | None = None

    opacity: float = 1.0

    visible: bool = True

    orientation: bool = True
    
    def __call__(self, **kwargs):

        for key, value in kwargs.items():

            if not hasattr(self, key):
                raise AttributeError(
                    f"Unknown style attribute '{key}'"
                )

            setattr(self, key, value)

        return self