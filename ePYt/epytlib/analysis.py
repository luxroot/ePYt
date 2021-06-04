import ast


class FuncVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        print(ast.dump(node))
