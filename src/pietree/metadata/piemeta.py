from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PieMeta:

    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, path, default=None):

        current = self.data

        for key in path.split("."):

            if not isinstance(current, dict):
                return default

            current = current.get(key)

            if current is None:
                return default

        return current

    def set(self, path, value):

        keys = path.split(".")

        current = self.data

        for key in keys[:-1]:

            if key not in current:
                current[key] = {}

            current = current[key]

        current[keys[-1]] = value

    def update(self, other):

        self._recursive_update(self.data, other)


    def _recursive_update(self, target, source):

        for key, value in source.items():

            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):

                self._recursive_update(
                    target[key],
                    value,
                )

            else:

                target[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data