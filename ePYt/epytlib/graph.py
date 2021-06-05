import ast
import jedi
from . import domain

specialType = [ast.If, ast.For, ast.While, ast.FunctionDef]

# temporary types
class Branch(domain.BaseType):
    def __init__(self):
        super().__init__()
    
class FunDef(domain.BaseType):
    def __init__(self):
        super().__init__()
    
class Atomic(domain.BaseType):
    def __init__(self):
        super().__init__()


class Node:
    def __init__(self, type_, instr_, prev_, lineno_):
        self.type = type_
        self.instr = instr_
        self.prev = prev_
        self.lineno = lineno_

    def fork(self):
        node = Node(Branch(), self.instr, self.prev, self.lineno)
        return node

    def print(self):
        print('=====================')
        print(f'instr: {self.instr} [{self.lineno}]')
        print(f'type : {self.type}')
        print('prevs:')
        for p in self.prev:
            print(f' - {p.instr} [{p.lineno}]')
        print('=====================\n')


class Graph(ast.NodeVisitor):
    def __init__(self, script:jedi.Script):
        self.script = script
        self.nodes = []
        self.prev = []

    def parse(self, stmts):
        for stmt in stmts:
            if type(stmt) in specialType:
                self.visit(stmt)
            else:
                node = Node(Atomic(), ast.unparse(stmt), self.prev, stmt.lineno)
                inferred_type = self.script.infer(stmt.lineno, stmt.col_offset)
                if inferred_type:
                    node.type = inferred_type[0]
                self.nodes.append(node)
                self.prev = [node]

    def visit_If(self, node):
        nt = Node(Branch(), f'if {ast.unparse(node.test)}', self.prev, node.lineno)
        nf = nt.fork()

        self.nodes.append(nt)
        self.nodes.append(nf)

        self.prev = [nt]
        self.parse(node.body)
        prev_t = self.prev

        self.prev = [nf]
        self.parse(node.orelse)

        self.prev.extend(prev_t)
        return node

    def visit_For(self, node):
        cond = f'{ast.unparse(node.target)} in {ast.unparse(node.iter)}'
        nt = Node(Branch(), f'for {cond}', self.prev, node.lineno)
        nf = nt.fork()

        self.nodes.append(nt)
        self.nodes.append(nf)

        self.prev = [nt]
        self.parse(node.body)

        self.prev.extend([nf])
        return node
    
    def visit_While(self, node):
        nt = Node(Branch(), f'while {ast.unparse(node.test)}', self.prev, node.lineno)
        nf = nt.fork()

        self.nodes.append(nt)
        self.nodes.append(nf)
        
        self.prev = [nt]
        self.parse(node.body)

        self.prev.extend([nf])
        return node
    
    def visit_FunctionDef(self, node):
        self.prev = []
        n = Node(FunDef(), f'def {node.name}({ast.unparse(node.args)})', self.prev, node.lineno)

        self.nodes.append(n)
        self.prev = [n]
        self.parse(node.body)
        
        self.prev = []
        return node
    
def from_file(file_path):
    script = jedi.Script(path=file_path)
    graph = Graph(script)
    code = open(file_path, "r").read()
    root = ast.parse(code, file_path)
    graph.parse(root.body)
    return graph
