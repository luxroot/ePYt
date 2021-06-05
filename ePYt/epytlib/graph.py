import ast

class Node:
    def __init__(self, instr_, prev_, lineno_):
        self.instr = instr_
        self.prev = prev_
        self.lineno = lineno_

    def print(self):
        print('=====================')
        print(f'instr: {self.instr} [{self.lineno}]')
        print(f'type : {str(self)}')
        print('prevs:')
        for p in self.prev:
            print(f' - {p.instr} [{p.lineno}]')
        print('=====================\n')

class Atomic(Node):
    def __init__(self, instr, prev, lineno):
        super().__init__(instr, prev, lineno)
    
    def __str__(self):
        return 'atomic'

class Branch(Node):
    def __init__(self, truth_, instr, prev, lineno):
        super().__init__(instr, prev, lineno)
        self.truth = truth_
    
    def __str__(self):
        return f'branch - {self.truth}'
    
    def fork(self):
        return Branch(not self.truth, self.instr, self.prev, self.lineno)

class FunDef(Node):
    def __init__(self, name_, args_, prev, lineno):
        self.name = name_
        self.args = args_
        super().__init__(f'def {self.name}({self.args})', prev, lineno)

    def __str__(self):
        return f'FunctionDef of {self.name}'

class ClassDef(Node):
    def __init__(self, name_, prev, lineno):
        self.name = name_
        super().__init__(f'class {self.name}', prev, lineno)
    
    def __str__(self):
        return f'ClassDef of {self.name}'
    
class Try(Node):
    def __init__(self, is_except, prev, lineno, exception_=None):
        super().__init__('try-except', prev, lineno)
        self.is_except = is_except
        if self.is_except:
            self.exception = exception_
        else:
            self.exception = None
    
    def __str__(self):
        if self.is_except:
            return f'except {self.exception}'
        else:
            return 'try'

class Graph(ast.NodeVisitor):
    def __init__(self):
        self.specialType = [ast.If, ast.For, ast.While, ast.FunctionDef, ast.ClassDef, ast.Try]
        self.nodes = []
        self.prev = []

    def parse(self, stmts):
        for stmt in stmts:
            if type(stmt) in self.specialType:
                self.visit(stmt)
            else:
                node = Atomic(ast.unparse(stmt), self.prev, stmt.lineno)
                self.nodes.append(node)
                self.prev = [node]

    def visit_If(self, node):
        nt = Branch(True, ast.unparse(node.test), self.prev, node.lineno)
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
        nt = Branch(True, cond, self.prev, node.lineno)
        nf = nt.fork()

        self.nodes.append(nt)
        self.nodes.append(nf)

        self.prev = [nt]
        self.parse(node.body)
        self.prev.extend([nf])
        return node
    
    def visit_While(self, node):
        nt = Branch(True, ast.unparse(node.test), self.prev, node.lineno)
        nf = nt.fork()

        self.nodes.append(nt)
        self.nodes.append(nf)
        
        self.prev = [nt]
        self.parse(node.body)
        self.prev.extend([nf])
        return node
    
    def visit_FunctionDef(self, node):
        self.prev = []
        n = FunDef(node.name, ast.unparse(node.args), self.prev, node.lineno)
        
        self.nodes.append(n)
        self.prev = [n]
        self.parse(node.body)
        
        self.prev = []
        return node
    
    def visit_ClassDef(self, node):
        self.prev = []
        n = ClassDef(node.name, self.prev, node.lineno)

        for method in node.body:
            self.prev = [n]
            self.parse([method])

        self.prev = []
        return node
    
    def visit_Try(self, node):
        n = Try(False, self.prev, node.lineno)

        self.nodes.append(n)
        self.parse(node.body)
        try_prev = self.prev

        for i in range(len(node.handlers)):
            self.prev = [n]
            except_n = Try(True, self.prev, node.handlers[i].lineno, ast.unparse(node.handlers[i].type))
            self.nodes.append(except_n)
            self.prev = [except_n]
            self.parse(node.handlers[i].body)
            try_prev.extend(self.prev)

        self.prev = try_prev
        return node

def parse_from_file(filename):
    code = open(filename, 'r').read()
    root = ast.parse(code, filename)
    graph = Graph()
    graph.parse(root.body)
    return graph