import ast
from . import graph
from . import memory
from . import domain


class HasAttrInfo:
    def __init__(self, arg_key, lifted_value):
        self.arg_key = arg_key
        self.lifted_value = lifted_value

    def get_as_tuple(self):
        return self.arg_key, self.lifted_value


class HasMethod(HasAttrInfo):
    pass


class HasProperty(HasAttrInfo):
    pass


class Lifter(ast.NodeVisitor):
    handling_types = (graph.Atomic, graph.Branch)

    op_to_method = {
        ast.UAdd: '__pos__', ast.USub: '__neg__', ast.Invert: '__invert__',
        ast.Not: '__not__', ast.Add: '__add__', ast.Sub: '__sub__',
        ast.Mult: '__mul__', ast.Div: '__div__', ast.Mod: '__mod__',
        ast.Pow: '__pow__', ast.LShift: '__lshift__', ast.RShift: '__rshift__',
        ast.BitOr: '__or__', ast.BitXor: '__xor__', ast.BitAnd: '__and__',
        ast.Eq: '__eq__', ast.NotEq: '__ne__', ast.Lt: '__lt__',
        ast.LtE: '__le__', ast.Gt: '__gt__', ast.GtE: '__ge__',
        ast.In: '__contains__', ast.NotIn: '__contains__'}

    func_to_method = {
        'abs': '__abs__', 'len': '__len__', 'int': '__int__', 'oct': '__oct__',
        'float': '__float__', 'complex': '__complex__', 'str': '__str__',
        'hex': '__hex__', 'bool': '__nonzero__', 'dir': '__dir__',
        'repr': '__repr__', 'unicode': '__unicode__', 'size': '__sizeof__',
        'string.format': '__format__', 'hash': '__hash__'}

    def __init__(self, args):
        self.lifted_values = []
        self.args = args

    def add_method(self, key, value):
        self.lifted_values.append(HasMethod(key, value))

    def add_property(self, key, value):
        self.lifted_values.append(HasProperty(key, value))

    def lift(self, graph_node):
        if len(graph_node.instr_list) == 2:  # for branch
            for_iter = graph_node.instr_list[1]
            if isinstance(for_iter, ast.Name) and \
                    ast.unparse(for_iter) in self.args:
                self.add_method(ast.unparse(for_iter), '__iter__')
        if isinstance(graph_node, self.handling_types):
            for instr in graph_node.instr_list:
                self.visit(instr)
        return self.lifted_values

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        arg_key = ast.unparse(node.operand)
        if arg_key in self.args:
            self.add_method(arg_key, self.op_to_method[type(node.op)])

    def visit_BinOp(self, node):
        self.generic_visit(node)
        arg_key = ast.unparse(node.left)
        if arg_key in self.args:
            self.add_method(arg_key, self.op_to_method[type(node.op)])

    def visit_Compare(self, node):
        self.generic_visit(node)
        arg_key = ast.unparse(node.left)
        if arg_key in self.args:
            self.add_method(arg_key, self.op_to_method[type(node.ops[0])])

    def visit_Call(self, node):
        self.generic_visit(node)
        fun_name = ast.unparse(node.func)
        if isinstance(node.func, ast.Attribute):
            arg_key = ast.unparse(node.func.value)
            if arg_key in self.args:
                self.add_method(arg_key, node.func.attr)
        elif fun_name in self.args:
            self.add_method(fun_name, "__call__")
        elif fun_name in self.func_to_method and node.func.args[0] in self.args:
            self.add_method(node.func.args[0], self.func_to_method[fun_name])

    def visit_Subscript(self, node):
        self.generic_visit(node)
        arg_key = ast.unparse(node.value)
        if arg_key in self.args:
            self.add_method(arg_key, "__index__")
            if not (isinstance(node.slice, ast.Constant) and
                    type(node.slice.value) == int):
                self.add_method(arg_key, "__getitem__")
                self.add_method(arg_key, "__setitem__")

    def visit_Attribute(self, node):  # Todo: Incomplete
        self.generic_visit(node)
        arg_key = ast.unparse(node.value)
        if arg_key in self.args:  # Todo: Urgent!
            pass
            # self.add_method(arg_key, "__getattr__")
            # self.add_method(arg_key, "__setattr__")

    def visit_Assign(self, node):  # Todo: Incomplete
        pass
        # self.generic_visit(node)
        # arg_key = ast.unparse(node.targets[0])
        # if arg_key in self.args:
        #     self.lifted_values.append(HasAttrInfo(arg_key, None))


class Semantic(ast.NodeVisitor):
    @staticmethod
    def convert_to_has_attr_list(has_attr_info_list):
        ret_dict = {}
        for has_attr_info in has_attr_info_list:
            key, value = has_attr_info.get_as_tuple()
            if key not in ret_dict:
                ret_dict[key] = domain.HasAttr()
            if isinstance(has_attr_info, HasMethod):
                ret_dict[key].methods.append(value)
            elif isinstance(has_attr_info, HasProperty):
                ret_dict[key].properties.append(value)
        return list(ret_dict.items())

    def __init__(self):
        self.fixed = False
        self.initial_mem = memory.Memory()
        self.args = []

    def get_annotation_info(self, args):
        for arg in args:
            self.args.append(arg.arg)
            if arg.annotation:
                self.initial_mem = \
                    self.initial_mem.add((arg.arg,
                                          domain.AnnotatedType(arg.annotation)))

    def transfer_node(self, graph_node, mem):
        lifted_value_list = Lifter(self.args).lift(graph_node)
        has_attr_list = self.convert_to_has_attr_list(lifted_value_list)
        new_memory = self.initial_mem.join(mem)
        while has_attr_list:
            arg_key, lifted_value = has_attr_list.pop()
            if arg_key is None:
                lifted_value = domain.FixedType(mem[arg_key])
            new_memory = new_memory.add((arg_key, lifted_value))
        if new_memory != graph_node.memory:
            graph_node.memory = new_memory
            self.fixed = False

    def run(self, func_def):
        self.args = []
        self.fixed = False
        self.get_annotation_info(func_def.args.args)
        while not self.fixed:
            self.fixed = True
            for node in func_def.graph.nodes:
                input_mem = memory.Memory()
                for prev in node.prev:
                    input_mem = input_mem.join(prev.memory)
                self.transfer_node(node, input_mem)
