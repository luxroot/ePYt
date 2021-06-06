import ast
from inspect import signature
from . import graph
from . import memory
from . import domain

class Item():
    def __init__(self, var, val):
        self.var = var
        self.val = val

class Semantic(ast.NodeVisitor):
    transfer_type = (graph.Atomic, graph.Branch)
    op_to_method = {ast.Add: '__add__',
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
    fun_to_method = {'len': '__len__',
        'str': '__str__',
        'int': '__int__',
        'float': '__float__'}

    def __init__(self):
        self.fixed = False
        self.args = []
        self.items = []

    def lift(self, node):
        for instr in node.instr_list:
            if isinstance(instr, self.transfer_type):
                self.visit(instr)

    def transfer_node(self, node, mem: memory.Memory):
        self.lift(node)
        new_memory = memory.Memory(mem)
        while self.items:
            item = self.items.pop()
            new_memory = memory.Memory.add(new_memory, item)
        if new_memory != node.memory:
            node.memory = new_memory
            self.fixed = False

    def run(self, funcDef: graph.FuncDef):
        self.args = funcDef.args
        while not self.fixed:
            self.fixed = True
            for node in funcDef.graph.nodes:
                input_mem = memory.Memory()
                for prev in node.prev:
                    input_mem = input_mem.join(prev.memory)
                self.transfer_node(node, input_mem)
    
    def visit_BinOp(self, node):
        var = ast.unparse(node.left)
        if var in self.args:
            val = domain.HasAttr()
            val.methods.append(self.op_to_method(type(node.op)))
            self.items.append(Item(var, val))
            return node
        return self.generic_visit()

    def visit_Compare(self, node):
        var = ast.unparse(node.left)
        if var in self.args:
            val = domain.HasAttr()
            val.methods.append(self.op_to_method(type(node.op)))
            self.items.append(Item(var, val))
            return node
        return self.generic_visit()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            var = ast.unparse(node.func.value)
            if var in self.args:
                val = domain.HasAttr()
                val.methods.append(node.func.attr)
                self.items.append(Item(var, val))
                return node
        else:
            fun_name = ast.unparse(node.func)
            if fun_name in self.func_to_method:
                val = domain.HasAttr()
                val.methods.append(self.func_to_method[fun_name])
                self.items.append(Item(fun_name, val))
                return node
        return self.generic_visit()

    def visit_Attribute(self, node):
        var = ast.unparse(node.value)
        if var in self.args:
            val = domain.HasAttr()
            val.properties.append(node.attr)
            self.items.append(Item(var, val))
            return node
        return self.generic_visit()
        
    # class constructer
    # x = 1
    def visit_Assign(self, node):
        pass


