from . import preanalysis, semantic, memory, domain
from functools import reduce


class TypeInferrer:
    prim_types = [*map(domain.PrimitiveType, domain.PrimitiveType.prim_types)]

    def __init__(self, dir_path):
        self.prim_type_dicts = {}
        for prim_type in domain.PrimitiveType.prim_types:
            v = domain.PrimitiveType(prim_type)
            self.prim_type_dicts[prim_type] = v.typedef
        self.type_candidates = preanalysis.get_typedefs(dir_path)
        self.type_candidates.update(self.prim_type_dicts)
        self.table = None

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
            if arg_key == 'self':
                continue
            inferred_user_types[arg_key] = list(
                filter(
                    lambda x: self.match(x.type.attributes,
                                         lifted_value.attributes),
                    self.type_candidates.values()))
        return inferred_user_types

    def infer(self, func_def):
        self.table = semantic.Semantic(func_def).table
        return self.infer_table(self.table)
