from dataclasses import dataclass, field
from typing import Optional
from pietree.metadata.piemeta import PieMeta

class PieObject:

    def __init__(self, metadata: Optional[dict] = None):
        self._metadata: PieMeta = PieMeta(metadata or {})
        
    @property
    def metadata(self):
        return self._metadata

    # def annotate(self, key, value=None):
    #     self._metadata.annotations[key] = value