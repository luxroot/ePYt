import ast
from jedi import Script
from . import domain
from . import preanalysis


class _Instrumenter (ast.NodeTransformer):
    def __init__(self, script: Script, user_types):
        self.script = script
        self.user_types = user_types

    def find_user_type(self, name):
        for t in self.user_types:
            if t.class_name == name:
                return t
        return None

    # Changes jedi type to epyt type
    def jedi_to_epyt (self, j_type):
        t = j_type[0]
        if t.full_name.startswith("builtin"):
            return domain.PrimitiveType(t.get_type_hint())
        elif t.description.startswith("instance"):
            class_name = t.description.split(" ")[1]
            type = self.find_user_type(class_name)
            return type


    def visit_Assign(self, node: ast.Assign):
        node.type = None
        line, column = node.lineno, node.col_offset
        inferred_type = self.script.infer(line, column)
        if inferred_type:
            node.type = self.jedi_to_epyt(inferred_type)
        return node


''' 
    Parse a python file and returns ast with inferred type information for Assign nodes.
    The inferred type can be accessed using node.type for Assign's.
    Todo: Change inferred type format to our own type kind
'''
def parse_with_type_info (filename):
    user_types = preanalysis.get_typedefs(filename)
    script = Script(path=filename)
    instrumenter = _Instrumenter(script, user_types)
    lines = open(filename, "r").readlines()
    root = ast.parse ("".join(lines), filename)
    return instrumenter.visit(root)






