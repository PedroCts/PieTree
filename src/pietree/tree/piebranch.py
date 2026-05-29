from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from pietree.metadata.piemeta import PieMeta

@dataclass
class PieBranch:
    parent_id: str
    child_id: str
    length: Optional[float] = None
    label: Optional[str] = None
    support: Optional[float] = None
    substitutions: Optional[int] = None
    _metadata: PieMeta = field(default_factory=PieMeta)
    
    @property
    def metadata(self):
        return self._metadata