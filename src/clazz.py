from typing import Any, Dict


class Clazz(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, key):
        return super().__getitem__(key)

    def __setattr__(self, key, value):
        return super().__setitem__(key, value)

    def entry(self, dt: Dict):
        """Prepares dictionary for database update"""
        result = {'_id': super().__getitem__('_id')}
        result.update(dt)
        return result

    def from_dict(self, dt: Dict) -> 'Clazz':
        self.__dict__.update(dt)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return dict(self)
