import ast
from pathlib import Path
from . import memory


class Node:
    def __init__(self, instr_list, prev):
        self.instr_list = instr_list
        self.prev = prev
        self.memory = memory.Memory()

    def __str__(self):
        return f"{','.join(map(ast.unparse, self.instr_list))} <- " + \
               (','.join(list(map(lambda x: x.str_without_prev(),
                                  self.prev))) if self.prev != [] else "")

    def str_without_prev(self):
        return ast.unparse(self.instr_list)

    def __repr__(self):
        return f"<Node {str(self)}>"


class Atomic(Node):
    pass


class Branch(Node):
    def __init__(self, truth, instr_list, prev):
        super().__init__(instr_list, prev)
        self.truth = truth

    def __str__(self):
        return f'Branch taken {self.truth} ' + \
               f"test: {','.join(map(ast.unparse, self.instr_list))}" + \
               f" <- {','.join(map(str, self.prev))}"

    def fork(self):
        return Branch(not self.truth, self.instr_list, self.prev)


class FuncDefNode(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args
        super().__init__([], [])

    def __str__(self):
        return f'FunctionDef of {self.name}'

    def str_without_prev(self):
        return str(self)


# class ClassDef(Node):
#     def __init__(self, name, prev):
#         self.name = name
#         super().__init__(f'class {self.name}', prev)
#
#     def __str__(self):
#         return f'ClassDef of {self.name}'
#
#
# class TryNode(Node):
#     def __init__(self, is_except, prev, exception=None):
#         super().__init__('try-except', prev)
#         self.is_except = is_except
#         if self.is_except:
#             self.exception = exception
#         else:
#             self.exception = None
#
#     def __str__(self):
#         if self.is_except:
#             return f'except {self.exception}'
#         else:
#             return 'try'


class Graph(ast.NodeVisitor):
    handling_types = (ast.If, ast.For, ast.While, ast.FunctionDef,
                      ast.ClassDef, ast.Try)

    def __init__(self):
        self.nodes = []
        self.current_prev = []
        self.func_defs = {}

    def parse(self, stmts):
        for stmt in stmts:
            if isinstance(stmt, self.handling_types):
                self.visit(stmt)
            else:
                node = Atomic([stmt], self.current_prev)
                self.nodes.append(node)
                self.current_prev = [node]

    def visit_If(self, node):
        nt = Branch(True, node.test, self.current_prev)
        nf = nt.fork()

        self.nodes.extend([nt, nf])

        self.current_prev = [nt]
        self.parse(node.body)
        prev_t = self.current_prev

        self.current_prev = [nf]
        self.parse(node.orelse)
        self.current_prev.extend(prev_t)
        return node

    # def visit_For(self, node):
    #     cond = f'{ast.unparse(node.target)} in {ast.unparse(node.iter)}'
    #     nt = Branch(True, cond, self.current_prev, node.lineno)
    #     nf = nt.fork()
    #
    #     self.nodes.append(nt)
    #     self.nodes.append(nf)
    #
    #     self.current_prev = [nt]
    #     self.parse(node.body)
    #     self.current_prev.extend([nf])
    #     return node
    #
    # def visit_While(self, node):
    #     nt = Branch(True, ast.unparse(node.test), self.current_prev, node.lineno)
    #     nf = nt.fork()
    #
    #     self.nodes.append(nt)
    #     self.nodes.append(nf)
    #
    #     self.current_prev = [nt]
    #     self.parse(node.body)
    #     self.current_prev.extend([nf])
    #     return node
    #
    def visit_FunctionDef(self, node):
        n = FuncDefNode([node.name], node.args)
        self.nodes.append(n)
        self.func_defs[n.name[0]] = n
        current_prev_backup = self.current_prev
        self.current_prev = [n]
        self.parse(node.body)
        self.current_prev = current_prev_backup
        return node

    # def visit_ClassDef(self, node):
    #     self.current_prev = []
    #     n = ClassDef(node.name, self.current_prev, node.lineno)
    #
    #     for method in node.body:
    #         self.current_prev = [n]
    #         self.parse([method])
    #
    #     self.current_prev = []
    #     return node
    #
    # def visit_Try(self, node):
    #     n = TryNode(False, self.current_prev, node.lineno)
    #
    #     self.nodes.append(n)
    #     self.parse(node.body)
    #     try_prev = self.current_prev
    #
    #     for i in range(len(node.handlers)):
    #         self.current_prev = [n]
    #         except_n = TryNode(True, self.current_prev, node.handlers[i].lineno,
    #                            ast.unparse(node.handlers[i].type))
    #         self.nodes.append(except_n)
    #         self.current_prev = [except_n]
    #         self.parse(node.handlers[i].body)
    #         try_prev.extend(self.current_prev)
    #
    #     self.current_prev = try_prev
    #     return node


def parse_from_file(script_path):
    script_path = Path(script_path)
    tree = ast.parse(script_path.read_text(), script_path.name)
    graph = Graph()
    graph.parse(tree.body)
    return graph
