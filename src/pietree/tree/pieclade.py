from dataclasses import dataclass


@dataclass(slots=True)
class PieClade:

    root: object
    nodes: list
    tips: list
    
