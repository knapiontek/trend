from typing import Any, Dict


class Clazz(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, key):
        return super().__getitem__(key)

    def __setattr__(self, key, value):
        return super().__setitem__(key, value)

    def entry(self, dt: Dict, **kwargs):
        """Prepares dictionary for database update"""
        result = {'_id': self.__dict__['_id']}
        result.update(dt)
        if kwargs:
            result.update(kwargs)
        return result

    def from_dict(self, dt: Dict) -> 'Clazz':
        self.__dict__.update(dt)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return dict(self)
