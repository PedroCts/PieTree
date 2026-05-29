from dataclasses import dataclass, field

from .rules import StyleRule

@dataclass
class StyleSheet:
    rules: list[StyleRule] = field(default_factory=list)