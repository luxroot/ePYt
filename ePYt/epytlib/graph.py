import ast
import sys
from copy import deepcopy

branchType = [ast.If, ast.For, ast.While]


class Node:
    def __init__(self, type_, instr_, prev_, lineno_):
        self.type = type_
        self.instr = instr_
        self.prev = prev_
        self.lineno = lineno_

    def fork(self):
        node = Node(self.type, self.instr, self.prev, self.lineno)
        branch = node.type.split('-')
        if branch[1] == 't':
            node.type = 'branch-f'
        else:
            node.type = 'branch-t'
        return node

    def print(self):
        print('=====================')
        print(f'instr: {self.instr} [{self.lineno}]')
        print(f'type : {self.type}')
        print('prevs')
        for p in self.prev:
            print(f' - {p.instr} [{p.lineno}]')
        print('=====================\n')


class Graph(ast.NodeVisitor):
    def __init__(self, root=None):
        self.nodes = list()
        self.prev = []
        if root:
            self.parse(root.body)

    def parse(self, stmts):
        for stmt in stmts:
            if type(stmt) in branchType:
                self.visit(stmt)
            else:
                node = Node('atomic', ast.unparse(stmt), self.prev, stmt.lineno)
                self.nodes.append(node)
                self.prev = [node]

    def visit_If(self, node):
        nt = Node('branch-t', f'if {ast.unparse(node.test)}', self.prev, node.lineno)
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
        nt = Node('branch-t', f'for {cond}', self.prev, node.lineno)
        nf = nt.fork()

        self.nodes.append(nt)
        self.nodes.append(nf)

        self.prev = [nt]
        self.parse(node.body)

        self.prev.extend(nf)
        return node
    
    def visit_While(self, node):
        nt = Node('branch-t', f'while {node.tset}', self.prev, node.lineno)
        nf = nt.fork()

        self.nodes.append(nt)
        self.nodes.append(nf)
        
        self.prev = [nt]
        self.parse(node.body)

        self.prev.extend(nf)
        return node


x = open(sys.argv[1]).read()
root = ast.parse(x)
x = Graph(root)
for node in x.nodes:
    node.print()
