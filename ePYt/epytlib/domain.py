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
    pass


class HasAttr(BaseType):
    def __init__(self):
        self.properties = list()
        self.methods = list()

    def __str__(self):
        return "HasAttr\n" + \
               "\n".join(["Properties",
                          "\n".join(self.properties),
                          "Methods",
                          "\n".join(map(str, self.methods))])


class Typed(HasAttr):
    def __init__(self, typedef):
        super().__init__()
        self.typedef = typedef


class PrimitiveType(HasAttr):
    prim_types = ["int", "str", "list", "dict"]  # TODO: To be filled

    def __init__(self, type_):
        super().__init__()
        if type_ in self.prim_types:
            self.type_ = type_
            self.type_def = preanalysis.TypeDef(eval(type_))
            self.properties.extend(list(self.type_def.type.properties))
            self.methods.extend(list(self.type_def.type.methods))

    def __str__(self):
        return f"Primitive type [{self.type_}]\n{super().__str__()}"
