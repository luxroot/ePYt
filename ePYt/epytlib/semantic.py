import ast
from . import graph, memory

class Semantic(ast.NodeVisitor):
    def __init__(self):
        self.to_method = {ast.Add: '__add__',
            ast.Sub: '__sub__',
            ast.Mult: '__mul__',
            ast.Div: '__div__',
            ast.Mod: '__mod__',
            ast.Pow: '__pow__',
            ast.LShift: '__lshift__',
            ast.RShift: '__rshift__',
            ast.BitOr: '__or__',
            ast.BitXor: '__xor__',
            ast.BitAnd: '__and__',
            ast.Eq: '__eq__',
            ast.NotEq: '__ne__',
            ast.Lt: '__lt__',
            ast.LtE: '__le__',
            ast.Gt: '__gt__',
            ast.GtE: '__ge__',
            ast.In: '__contains__',
            ast.NotIn: '__contains__'}
        self.fixed = False
        self.args = []
        self.locals = []
        self.items = []

    def lift(self, node):
        self.items = []
        for instr in node.instr_list:
            self.visit(instr)

    def transfer_node(self, node, mem: memory.Memory):
        self.lift(node)
        new_memory = memory.Memory(mem)
        for item in self.items:
            new_memory = memory.Memory.add(new_memory, item)
        if new_memory != node.memory:
            node.memory = new_memory
            self.fixed = False

    def run(self, funcDef: graph.FuncDef):
        cfg = funcDef.graph
        self.args = funcDef.args

        while not self.fixed:
            self.fixed = True
            for node in cfg.nodes:
                input_mem = memory.Memory()
                for prev in node.prev:
                    input_mem = memory.Memory.join(input_mem, prev.memory)
                self.transfer_node(node, input_mem)
    
    def visit_BinOp(self, node):
        if ast.unparse(node.left) in self.args:
            self.items.append((ast.unparse(node.left), self.to_method[type(node.op)]))

    def visit_Compare(self, node):
        if ast.unparse(node.left) in self.args:
            self.items.append((ast.unparse(node.left), self.to_method[type(node.ops[0])]))
    
    def visit_Call(self, node):
        if ast.unparse(node.func.value) in self.args and hasattr(node.func, 'attr'):
            self.items.append((ast.unparse(node.func.value), node.func.attr))

        
