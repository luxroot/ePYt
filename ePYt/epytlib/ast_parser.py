import ast
from jedi import Script


class _Instrumenter (ast.NodeTransformer):
    def __init__(self, script: Script):
        self.script = script

    def visit_Assign(self, node: ast.Assign):
        node.type = None
        line, column = node.lineno, node.col_offset
        inferred_type = self.script.infer(line, column)
        if inferred_type:
            node.type = inferred_type[0]
        return node



''' 
    Parse a python file and returns ast with inferred type information for Assign nodes.
    The inferred type can be accessed using node.type for Assign's.
    Todo: Change inferred type format to our own type kind
'''
def parse_with_type_info (filename):
    script = Script(path=filename)
    instrumenter = _Instrumenter(script)
    lines = open(filename, "r").readlines()
    root = ast.parse ("".join(lines), filename)
    return instrumenter.visit(root)


# root = parse_with_type_info("../../../example1.py")
# print("Root =", ast.dump(root, True, indent = 4))




