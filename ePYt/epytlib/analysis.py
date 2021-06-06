import ast
from . import memory, preanalysis, domain, type_infer


class FuncVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        print(ast.dump(node))
        a = memory.Memory()
        a.add()


class Analyzer:
    prim_types = [*map(domain.PrimitiveType, domain.PrimitiveType.prim_types)]

    def __init__(self, file_path):
        self.user_types = preanalysis.get_typedefs(file_path)
        self.type_infer = type_infer.TypeInfer(file_path) # Access by type_infer.get_type(lineno, colno)

