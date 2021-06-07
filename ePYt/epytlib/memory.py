from copy import deepcopy
from itertools import chain
from . import domain


class Memory:
    def __init__(self, dict_default=None):
        if dict_default is None:
            self.memory = dict()
        elif isinstance(dict_default, Memory):  # Deep copy
            self.memory = deepcopy(dict_default.memory)
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
        new_mem = Memory(self)
        key, value = item
        if key in self.memory:
            # print(f"Joining {item} with existing:{self.memory[key]}")
            new_mem.memory[key] = value.join(self.memory[key])
        else:
            new_mem.memory[key] = value
        return new_mem
        
    # Join with another memory
    def join(self, other):
        joined_mem = Memory()
        for key, value in chain(self.memory.items(), other.memory.items()):
            if key in joined_mem:
                joined_mem.memory[key] = value.join(joined_mem[key])
            else:
                joined_mem.memory[key] = deepcopy(value)
        return joined_mem

    def __eq__(self, other: 'Memory'):
        return self.memory == other.memory

    def __ne__(self, other: 'Memory'):
        return self.memory != other.memory

    def __str__(self):
        return '\n'.join(map(lambda x: f"{x[0]} : {x[1]}", self.memory.items()))

    def __repr__(self):
        return f"<Memory {str(self)}>"
