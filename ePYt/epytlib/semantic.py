import ast
from inspect import signature
from . import graph
from . import memory
from . import domain
from . import analysis
from . import type_infer

class Item():
    def __init__(self, var:str, val:str):
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

    def __init__(self, typeinfer: type_infer.TypeInfer):
        self.fixed = False
        self.initial_mem = memory.Memory()
        self.typeinfer = typeinfer
        self.args = []
        self.items = []
        self.constructer = []

    def get_annotation_info(self, args):
        for arg in args:
            self.args.append(arg.arg)
            annotation = self.get_type(arg.lineno, arg.col_offset)
            if annotation:
                self.initial_mem = self.initial_mem.add(arg.arg, annotation)

    def lift(self, node):
        for instr in node.instr_list:
            if isinstance(instr, self.transfer_type):
                self.visit(instr)

    def transfer_node(self, node, mem):
        self.lift(node)
        new_memory = self.initial_mem.join(mem)
        while self.items:
            item = self.items.pop()
            new_memory = new_memory.add(item)
        if new_memory != node.memory:
            node.memory = new_memory
            self.fixed = False

    def run(self, funcDef):
        self.get_annotation_info(funcDef.args.args)
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
        else:
            self.generic_visit()

    def visit_Compare(self, node):
        var = ast.unparse(node.left)
        if var in self.args:
            val = domain.HasAttr()
            val.methods.append(self.op_to_method(type(node.op)))
            self.items.append(Item(var, val))
            return node
        else:
            self.generic_visit()

    def visit_Call(self, node):
        fun_name = ast.unparse(node.func)
        var = ast.unparse(node.func.value)
        if isinstance(node.func, ast.Attribute) and var in self.args:
            val = domain.HasAttr()
            val.methods.append(node.func.attr)
            self.items.append(Item(var, val))
        elif fun_name in self.func_to_method:
            val = domain.HasAttr()
            val.methods.append(self.func_to_method[fun_name])
            self.items.append(Item(fun_name, val))
        else:
            self.generic_visit()

    def visit_Attribute(self, node):
        var = ast.unparse(node.value)
        if var in self.args:
            val = domain.HasAttr()
            val.properties.append(node.attr)
            self.items.append(Item(var, val))
        else:
            self.generic_visit()

    # optional type using primitive type
    # def visit_Assign(self, node):
    #     var = ast.unparse(node.target)
    #     if var in self.args:
    #         if isinstance(node.value, ast.Constant):
    #             prim_type = str(type(node.value.value)).split("'")[1]
    #             val = domain.PrimitiveType(prim_type) 
    #             self.items.append(Item(var, val))
    #             return node
    #         elif isinstance(node.value, ast.Call):
    #             fun_name = ast.unparse(node.value.func)
    #             if fun_name in self.constructer:
    #                 class_type = 'some class constructer'
    #                 val = domain.PrimitiveType(class_type)
    #                 self.items.append(Item(var, val))
    #                 return node
    #     return self.generic_visit()


