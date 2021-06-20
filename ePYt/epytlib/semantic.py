import ast
from . import graph
from . import memory
from . import domain
from . import table


class LiftedValue:
    type_string = ""

    def __init__(self, arg_key):
        self.arg_key = arg_key

    def get_key(self):
        return self.arg_key


class HasAttrInfo(LiftedValue):
    def __init__(self, arg_key, lifted_value):
        super().__init__(arg_key)
        self.lifted_value = lifted_value

    def get_as_tuple(self):
        return self.arg_key, self.lifted_value

    def __str__(self):
        return self.type_string + ' ' + str((self.arg_key, self.lifted_value))

    def __repr__(self):
        return f"<{str(self)}>"


class HasMethod(HasAttrInfo):
    type_string = "HasMethod"


class HasProperty(HasAttrInfo):
    type_string = "HasProperty"


class HasAssigned(LiftedValue):
    type_string = "HasAssigned"


class Lifter(ast.NodeVisitor):
    handling_types = (graph.Atomic, graph.Branch)

    op_to_method = {
        ast.UAdd: '__pos__', ast.USub: '__neg__', ast.Invert: '__invert__',
        ast.Not: '__not__', ast.Is: '__is__', ast.IsNot: '__isnot__',
        ast.Add: '__add__', ast.Sub: '__sub__', ast.Mult: '__mul__',
        ast.Div: 'truediv', ast.Mod: '__mod__', ast.Pow: '__pow__',
        ast.LShift: '__lshift__', ast.RShift: '__rshift__',
        ast.BitOr: '__or__', ast.BitXor: '__xor__', ast.BitAnd: '__and__',
        ast.Eq: '__eq__', ast.NotEq: '__ne__', ast.Lt: '__lt__',
        ast.LtE: '__le__', ast.Gt: '__gt__', ast.GtE: '__ge__',
        ast.In: '__contains__', ast.NotIn: '__contains__',
        ast.FloorDiv: 'floordiv'}

    func_to_method = {
        'abs': '__abs__', 'len': '__len__', 'int': '__int__', 'oct': '__oct__',
        'float': '__float__', 'complex': '__complex__', 'str': '__str__',
        'hex': '__hex__', 'bool': '__nonzero__', 'dir': '__dir__',
        'repr': '__repr__', 'unicode': '__unicode__', 'size': '__sizeof__',
        'hash': '__hash__', 'divmod': 'divmod'}

    def __init__(self, args):
        self.lifted_values = []
        self.args = args

    def _add_method(self, key, value):
        self.lifted_values.append(HasMethod(key, value))

    def _add_property(self, key, value):
        self.lifted_values.append(HasProperty(key, value))

    def _has_assigned(self, key):
        self.lifted_values.append(HasAssigned(key))

    def lift(self, graph_node):
        if len(graph_node.instr_list) == 2:  # for branch
            for_iter = graph_node.instr_list[1]
            if isinstance(for_iter, ast.Name) and \
                    ast.unparse(for_iter) in self.args:
                self._add_method(ast.unparse(for_iter), '__iter__')
        if isinstance(graph_node, self.handling_types):
            for instr in graph_node.instr_list:
                self.visit(instr)
        return self.lifted_values

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        arg_key = ast.unparse(node.operand)
        if arg_key in self.args:
            self._add_method(arg_key, self.op_to_method[type(node.op)])

    def visit_BinOp(self, node):
        self.generic_visit(node)
        arg_key = ast.unparse(node.left)
        if arg_key in self.args:
            self._add_method(arg_key, self.op_to_method[type(node.op)])

    def visit_Compare(self, node):
        self.generic_visit(node)
        arg_key = ast.unparse(node.left)
        if arg_key in self.args:
            self._add_method(arg_key, self.op_to_method[type(node.ops[0])])

    def visit_Call(self, node):
        fun_name = ast.unparse(node.func)
        if isinstance(node.func, ast.Attribute):
            arg_key = ast.unparse(node.func.value)
            if arg_key in self.args:
                self._add_method(arg_key, node.func.attr)
                return
        self.generic_visit(node)
        if fun_name in self.args:
            self._add_method(fun_name, "__call__")
        elif fun_name in self.func_to_method and \
                ast.unparse(node.args[0]) in self.args:
            self._add_method(ast.unparse(node.args[0]),
                             self.func_to_method[fun_name])

    # __index__ is called when list[x]
    # __index__ is not called when dict[x]
    def visit_Subscript(self, node):
        self.generic_visit(node)
        arg_key = ast.unparse(node.value)
        if arg_key in self.args:
            if isinstance(node.ctx, ast.Load):
                self._add_method(arg_key, "__getitem__")
            elif isinstance(node.ctx, ast.Store):
                self._add_method(arg_key, "__setitem__")

    # __getattribute__ is called both object has property or not
    # __getattr__ is called when object does not have property
    # __getattr__ call __setattr__
    def visit_Attribute(self, node):
        self.generic_visit(node)
        arg_key = ast.unparse(node.value)
        if arg_key in self.args:
            self._add_property(arg_key, node.attr)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self._has_assigned(node.id)


class Semantic:
    @staticmethod
    def convert_to_has_attr_list(lifted_value_list):
        ret_dict = {}
        has_fixed_list = []
        for has_attr_info in lifted_value_list:
            key = has_attr_info.get_key()
            if key not in ret_dict:
                ret_dict[key] = domain.HasAttr()
            if isinstance(has_attr_info, HasMethod):
                ret_dict[key].methods.append(has_attr_info.lifted_value)
            elif isinstance(has_attr_info, HasProperty):
                ret_dict[key].properties.append(has_attr_info.lifted_value)
            elif isinstance(has_attr_info, HasAssigned):
                has_fixed_list.append(key)
        return list(ret_dict.items()), has_fixed_list

    def __init__(self, func_def):
        self.reached_fixed_point = False
        self.initial_mem = memory.Memory()
        self.args = []
        for arg in func_def.args.args:
            self.args.append(arg.arg)
            if arg.annotation:
                initial_arg = (arg.arg, domain.AnnotatedType(arg.annotation))
                self.initial_mem = self.initial_mem.add(initial_arg)
        self.table = table.Table(func_def.graph.nodes, self.initial_mem)
        while not self.reached_fixed_point:
            self.reached_fixed_point = True
            for table_key in self.table.table.keys():
                input_mem = memory.Memory()
                for prev in table_key.prev:
                    input_mem = input_mem.join(self.table[prev])
                self.transfer_node(table_key, input_mem)

    def transfer_node(self, table_key, input_mem):
        lifted_value_list = Lifter(self.args).lift(table_key)
        has_attr_list, has_fixed_list = \
            self.convert_to_has_attr_list(lifted_value_list)
        new_memory = self.initial_mem.join(input_mem)
        for arg_key, lifted_value in has_attr_list:
            new_memory = new_memory.add((arg_key, lifted_value))
            if arg_key in has_fixed_list:
                new_memory.fix(arg_key)
        if new_memory != self.table[table_key]:
            self.table[table_key] = new_memory
            self.reached_fixed_point = False
