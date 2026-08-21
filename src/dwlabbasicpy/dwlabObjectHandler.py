
class dictToObject:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                # Recursively convert nested dictionaries
                setattr(self, key, dictToObject(value))
            else:
                setattr(self, key, value)
