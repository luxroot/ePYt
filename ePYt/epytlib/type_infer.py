import ast
from jedi import Script
from . import domain
from . import preanalysis

class TypeInfer:
    def __init__ (self, path):
        self.user_types = preanalysis.get_typedefs(path)
        self.script = Script(path=path)

    def find_user_type(self, name):
        for t in self.user_types:
            if t.class_name == name:
                return t
        return None

    def jedi_to_epyt (self, j_type):
        t = j_type[0]
        if t.full_name.startswith("builtin"):
            return domain.PrimitiveType(t.get_type_hint())
        elif t.description.startswith("instance"):
            class_name = t.description.split(" ")[1]
            type = self.find_user_type(class_name)
            return type

    def get_type(self, lineno, colno):
        inferred_type = self.script.infer(lineno, colno)
        type = None
        if inferred_type:
            type = self.jedi_to_epyt(inferred_type)
        return type
