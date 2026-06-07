from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class MetadataRegistry:
    """
    Tracks which metadata values have already been claimed by a renderer.
    Prevents duplicate display across highlights, panels, and node labels.
    """
    _claimed: Dict[str, Dict[str, str]] = field(default_factory=dict)
    # {field → {value → renderer}} e.g. {"taxonomy": {"Chordata": "highlight"}}

    def claim(self, field: str, value: str, renderer: str) -> bool:
        """
        Attempt to claim a value for a renderer.
        Returns True if claim succeeded (value was unclaimed).
        """
        self._claimed.setdefault(field, {})
        if value in self._claimed[field]:
            return False
        self._claimed[field][value] = renderer
        return True

    def is_claimed(self, field: str, value: str) -> bool:
        return value in self._claimed.get(field, {})

    def claimed_by(self, field: str, value: str) -> Optional[str]:
        return self._claimed.get(field, {}).get(value)

    def reset(self, field: Optional[str] = None) -> None:
        if field is None:
            self._claimed.clear()
        else:
            self._claimed.pop(field, None)