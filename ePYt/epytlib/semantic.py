import ast
from . import graph
from . import memory
from . import domain

class Item:
    def __init__(self, var, val):
        self.var = var
        self.val = val

    def tuple(self):
        return self.var, self.val

class Semantic(ast.NodeVisitor):
    transfer_type = (graph.Atomic, graph.Branch)
    op_to_method = {
        ast.UAdd: '__pos__',
        ast.USub: '__neg__',
        ast.Invert: '__invert__',
        ast.Not: '__not__',
        ast.Add: '__add__',
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
    func_to_method = {
        'abs': '__abs__',
        'len': '__len__',
        'int': '__int__',
        'float': '__float__',
        'complex': '__complex__',
        'oct': '__oct__',
        'hex': '__hex__',
        'bool': '__nonzero__',
        'str': '__str__',
        'repr': '__repr__',
        'unicode': '__unicode__',
        'string.format': '__format__',
        'hash': '__hash__',
        'dir': '__dir__',
        'size': '__sizeof__'}

    def __init__(self):
        self.fixed = False
        self.initial_mem = memory.Memory()
        self.args = []
        self.items = []

    def get_annotation_info(self, args):
        for arg in args:
            self.args.append(arg.arg)
            if arg.annotation:
                self.initial_mem = self.initial_mem.add((arg.arg, domain.AnnotatedType(arg.annotation)))

    def lift(self, node):
        if len(node.instr_list) == 2: # for branch
            if isinstance(node.instr_list[1], ast.Name) and\
                 ast.unparse(node.instr_list[1]) in self.args:
                self.items.append(ast.unparse(node.instr_list[1]), '__iter__')
        if isinstance(node, self.transfer_type):
            for instr in node.instr_list:
                self.visit(instr)

    def transfer_node(self, node, mem):
        self.lift(node)
        new_memory = self.initial_mem.join(mem)
        while self.items:
            item = self.items.pop()
            var, val = item.tuple()
            if val is None:
                val = domain.FixType(mem[var])
            new_memory = new_memory.add((var ,val))
        if new_memory != node.memory:
            node.memory = new_memory
            self.fixed = False

    def run(self, funcDef):
        self.args = []
        self.fixed = False
        self.get_annotation_info(funcDef.args.args)
        while not self.fixed:
            self.fixed = True
            for node in funcDef.graph.nodes:
                input_mem = memory.Memory()
                for prev in node.prev:
                    input_mem = input_mem.join(prev.memory)
                self.transfer_node(node, input_mem)
    
    def visit_UnaryOp(self, node):
        var = ast.unparse(node.operand)
        if var in self.args:
            val = domain.HasAttr()
            val.methods.append(self.op_to_method[type(node.op)])
            self.items.append(Item(var, val))
        else:
            self.generic_visit(node)

    def visit_BinOp(self, node):
        var = ast.unparse(node.left)
        if var in self.args:
            val = domain.HasAttr()
            val.methods.append(self.op_to_method[type(node.op)])
            self.items.append(Item(var, val))
        else:
            self.generic_visit(node)

    def visit_Compare(self, node):
        var = ast.unparse(node.left)
        if var in self.args:
            val = domain.HasAttr()
            val.methods.append(self.op_to_method[type(node.ops[0])])
            self.items.append(Item(var, val))
            return node
        else:
            self.generic_visit(node)

    def visit_Call(self, node):
        fun_name = ast.unparse(node.func)
        if isinstance(node.func, ast.Attribute):
            var = ast.unparse(node.func.value)
            if var in self.args:
                val = domain.HasAttr()
                val.methods.append(node.func.attr)
                self.items.append(Item(var, val))
            else:
                self.generic_visit(node)
        elif fun_name in self.args:
            val = domain.HasAttr()
            val.methods.append('__call__')
            self.items.append(Item(fun_name, val))
        elif fun_name in self.func_to_method and node.func.args[0] in self.args:
            val = domain.HasAttr()
            val.methods.append(self.func_to_method[fun_name])
            self.items.append(Item(node.func.args[0], val))
        else:
            self.generic_visit(node)

    def visit_Subscript(self, node):
        var = ast.unparse(node.value)
        if var in self.args:
            val = domain.HasAttr()
            val.methods.append('__index__')
            if not (isinstance(node.slice, ast.Constant) and type(node.slice.value) == int):
                val.methods.append('__getitem__')
                val.methods.append('__setitme__')
            self.items.append(Item(var, val))
        else:
            self.generic_visit(node)

    def visit_Attribute(self, node):
        var = ast.unparse(node.value)
        if var in self.args:
            val = domain.HasAttr()
            val.properties.append(node.attr)
            val.properties.append('__getattr__')
            val.properties.append('__setattr__')
            self.items.append(Item(var, val))
        else:
            self.generic_visit(node)

    def visit_Assign(self, node):
        var = ast.unparse(node.targets[0])
        if var in self.args:
            self.items.append(Item(var, None))
        else:
            self.generic_visit(node)


