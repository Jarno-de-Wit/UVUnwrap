class EnumerationDict(dict):
    """
    A data structure for storing sequential indices for hashable items.
    If an entry does not exist, this entry is automatically assigned a new index and cached for future reuse.
    """
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            value = len(self)
            self[key] = value
            return value
