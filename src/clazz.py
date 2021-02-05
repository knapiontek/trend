from typing import Any, Dict


class Clazz(dict):

    def __init__(self, *args, **kwargs):
        args = [Clazz(**a) if type(a) == dict else a for a in args]
        kwargs = {k: Clazz(**v) if type(v) == dict else v for k, v in kwargs.items()}
        super().__init__(*args, **kwargs)

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __setattr__(self, key, value):
        return self.__setitem__(key, value)

    def entry(self, *fields) -> 'Clazz':
        """Prepares dictionary for database update"""
        return Clazz(**{f: super(Clazz, self).__getitem__(f) for f in ('_id',) + fields})

    def clean(self, *args):
        for a in args:
            if self.__contains__(a):
                self.__delitem__(a)

    def from_dict(self, dt: Dict) -> 'Clazz':
        self.__dict__.update(dt)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {k: v if type(v) != Clazz else v.to_dict() for k, v in self.items()}
