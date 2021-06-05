from copy import deepcopy
from itertools import chain
from . import domain


class Memory:
    def __init__(self, dict_default=None):
        if dict_default is None:
            self.memory = dict()
        elif isinstance(dict_default, Memory):  # Deep copy
            self.memory = dict(dict_default.memory)
        elif isinstance(dict_default, dict):  # Shallow copy
            self.memory = dict_default
        else:
            raise TypeError(f"Wrong type {type(dict_default)} passed to Memory")

    def __contains__(self, item):
        return item in self.memory

    def __getitem__(self, key):
        if key in self.memory:
            return self.memory[key]
        else:  # Value.bottom (for our case, it's Any)
            return domain.AnyType()

    # Add (key, value) to memory
    def add(self, item):
        new_dict = Memory(self)
        key, value = item
        if key in self.memory:
            print(f"Joining {item} with existing:{self.memory[key]}")
            new_dict.memory[key] = value.join(self.memory[key])
        else:
            new_dict.memory[key] = value

    # Join with another memory
    def join(self, other):
        joined_mem = dict()
        for key, value in chain(self.memory.items(), other.memory.items()):
            if key in joined_mem:
                joined_mem[key] = value.join(joined_mem[key])
            else:
                joined_mem[key] = deepcopy(value)
        return joined_mem

    def __eq__(self, other: 'Memory'):
        return self.memory == other.memory
