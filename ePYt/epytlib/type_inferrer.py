from . import preanalysis, semantic, memory
from functools import reduce


class TypeInferrer:
    def __init__(self, dir_path):
        self.user_types = preanalysis.get_typedefs(dir_path)

    @staticmethod
    def match(user_type_attrs, lifted_value_attrs):
        return set(user_type_attrs).issuperset(lifted_value_attrs)

    # Override me on your inference strategy
    def infer_table(self, table):
        joined_memory = reduce(lambda x, y: x.join(y),
                               table.table.values(),
                               memory.Memory())
        inferred_user_types = {}
        for arg_key, lifted_value in joined_memory.memory.items():
            inferred_user_types[arg_key] = list(
                filter(
                    lambda x: self.match(x.type.attributes,
                                         lifted_value.attributes),
                    self.user_types.values()))
        return inferred_user_types

    def infer(self, func_def):
        table = semantic.Semantic(func_def).table
        return self.infer_table(table)
