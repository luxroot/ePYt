import ast
from . import memory, preanalysis, domain


class FuncVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        print(ast.dump(node))
        a = memory.Memory()
        a.add()


class Analyzer:
    prim_types = [*map(domain.PrimitiveType, domain.PrimitiveType.prim_types)]

    def __init__(self, file_path):
        script = open(file_path).read()
        self.user_types = preanalysis.get_typedefs(script)

