class Selector:
    def match(self, branch) -> bool:
        raise NotImplementedError

class MetadataSelector(Selector):

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def match(self, branch) -> bool:
        metadata = branch.metadata

        if self.key not in metadata:
            return False

        candidate = metadata[self.key]

        if callable(self.value):
            return self.value(candidate)

        return candidate == self.value
