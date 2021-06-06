from copy import deepcopy
from . import preanalysis


class BaseType:
    @staticmethod
    def _join(a, b):
        new_type = deepcopy(a)
        new_type.properties.extend(b.properties)
        new_type.methods.extend(b.methods)
        return new_type

    def join(self, other):
        if isinstance(self, AnyType):
            return AnyType()
        if isinstance(other, AnyType):
            return AnyType()
        return self._join(self, other)

    def meet(self, other):
        if isinstance(self, AnyType):
            return deepcopy(other)
        if isinstance(other, AnyType):
            return deepcopy(self)
        return self._join(self, other)


class AnyType(BaseType):
    def __str__(self):
        return "AnyType"

    def __repr__(self):
        return "<Type AnyType>"


class HasAttr(BaseType):
    def __init__(self):
        self.properties = list()
        self.methods = list()

    def has_property(self, prop: str):
        return prop in self.properties

    def has_method(self, method: str):
        return method in map(lambda x: x[0], self.methods)

    def __str__(self):
        return "HasAttr\n" + \
               "\n".join(["Properties", "\n".join(self.properties),
                          "Methods", "\n".join(map(str, self.methods))])

    def __repr__(self):
        return '<HasAttr [Prop:' + ','.join(self.properties)[:50] + '\t' + \
               'Method:' + ','.join(map(lambda x: x[0], self.methods))[:50] + \
               ']>'

    def __le__(self, other: 'HasAttr'):
        return self.properties <= other.properties and \
               self.methods <= other.methods

    def __ge__(self, other: 'HasAttr'):
        return other <= self


class Typed(HasAttr):
    def __init__(self, typedef: preanalysis.TypeDef):
        super().__init__()
        self.typedef = typedef
        self.properties.extend(typedef.type.properties)
        self.methods.extend(typedef.type.methods)

    def __str__(self):
        return f"Typed type [{self.typedef.class_name}]\n{super().__str__()}"


class PrimitiveType(Typed):
    prim_types = ["int", "str", "float", "bool", "list", "dict"]  # TODO: To be filled

    def __init__(self, type_: str):  # Gets string not class
        if type_ in self.prim_types:
            super().__init__(preanalysis.TypeDef(eval(type_)))

    def __str__(self):
        return f"Primitive " + super().__str__()
