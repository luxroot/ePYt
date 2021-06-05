import ast

specialType = [ast.If, ast.For, ast.While, ast.FunctionDef]

class NodeType:
    def __init__(self, name_):
        self.name = name_

class Atomic(NodeType):
    def __init__(self):
        super().__init__('atomic')

    def __str__(self):
        return self.name

class Branch(NodeType):
    def __init__(self, truth_):
        super().__init__('branch')
        self.truth = truth_
    
    def __str__(self):
        return f'{self.name} - {self.truth}'

class FunDef(NodeType):
    def __init__(self, name_, args_):
        super().__init__(name_)
        self.args = args_

    def __str__(self):
        return f'def {self.name}({self.args})'


class Node:
    def __init__(self, type_, instr_, prev_, lineno_):
        self.type = type_
        self.instr = instr_
        self.prev = prev_
        self.lineno = lineno_

    def fork(self):
        node = Node(Branch(False), self.instr, self.prev, self.lineno)
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
    def __init__(self):
        self.nodes = []
        self.prev = []

    def parse(self, stmts):
        for stmt in stmts:
            if type(stmt) in specialType:
                self.visit(stmt)
            else:
                node = Node(Atomic(), ast.unparse(stmt), self.prev, stmt.lineno)
                self.nodes.append(node)
                self.prev = [node]

    def visit_If(self, node):
        nt = Node(Branch(True), f'if {ast.unparse(node.test)}', self.prev, node.lineno)
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
        nt = Node(Branch(True), f'for {cond}', self.prev, node.lineno)
        nf = nt.fork()

        self.nodes.append(nt)
        self.nodes.append(nf)

        self.prev = [nt]
        self.parse(node.body)

        self.prev.extend([nf])
        return node
    
    def visit_While(self, node):
        nt = Node(Branch(True), f'while {ast.unparse(node.test)}', self.prev, node.lineno)
        nf = nt.fork()

        self.nodes.append(nt)
        self.nodes.append(nf)
        
        self.prev = [nt]
        self.parse(node.body)

        self.prev.extend([nf])
        return node
    
    def visit_FunctionDef(self, node):
        self.prev = []
        fun_type = FunDef(node.name ,ast.unparse(node.args))
        n = Node(fun_type, str(fun_type), self.prev, node.lineno)

        self.nodes.append(n)
        self.prev = [n]
        self.parse(node.body)
        
        self.prev = []
        return node
    
def from_file(filename):
    code = open(filename, 'r').read()
    root = ast.parse(code, filename)
    graph = Graph()
    graph.parse(root.body)
    return graph
