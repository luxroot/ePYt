import ast
from . import memory


class FuncVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        print(ast.dump(node))
        a = memory.Memory()
        a.add()


class Analyzer:
    pass
