from copy import deepcopy
from . import preanalysis


class BaseType:
    @staticmethod
    def _join(a, b):
        new_type = deepcopy(a)
        new_type.properties.extend(b.properties)
        new_type.methods.extend(b.methods)
        new_type.properties = list(set(new_type.properties))
        new_type.methods = list(set(new_type.methods))
        return new_type

    def join(self, other):
        if isinstance(self, FixedType):
            return self
        if isinstance(other, FixedType):
            return other
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

    @property
    def attributes(self):
        return self.methods + self.properties

    def has_property(self, prop: str):
        return prop in self.properties

    def has_method(self, method: str):
        return method in self.methods

    def __str__(self):
        return "HasAttr of " + \
               " ".join(["Properties: " + ("EMPTY" if self.properties == [] else
                                           ", ".join(self.properties)),
                         "Methods: " + ("EMPTY" if self.methods == [] else
                                        ", ".join(map(str, self.methods)))])

    def __repr__(self):
        return f'<{str(self)}>'

    def __le__(self, other: 'HasAttr'):
        return self.properties <= other.properties and \
               self.methods <= other.methods

    def __ge__(self, other: 'HasAttr'):
        return other <= self

    def __eq__(self, other: 'HasAttr'):
        return self.properties == other.properties and \
               self.methods == other.methods

    def __ne__(self, other: 'HasAttr'):
        return not self == other


class Typed(HasAttr):
    def __init__(self, typedef: preanalysis.TypeDef):
        super().__init__()
        self.typedef = typedef
        self.properties.extend(typedef.type.properties)
        self.methods.extend(typedef.type.methods)

    def __str__(self):
        return f"Typed type [{self.typedef.class_name}] {super().__str__()}"


class FixedType(HasAttr):
    def __init__(self, has_attr):
        super().__init__()
        if isinstance(has_attr, HasAttr):
            self.properties.extend(has_attr.properties)
            self.methods.extend(has_attr.methods)

    def __str__(self):
        return f"Fixed type {super().__str__()}"


class AnnotatedType(BaseType):
    def __init__(self, str_type):
        self.strType = str_type

    def __str__(self):
        return f"Annotated type [{self.strType}]"


class PrimitiveType(Typed):
    # TODO: To be filled
    prim_types = ["int", "str", "float", "bool", "list", "dict"]

    def __init__(self, type_):
        if type_ in self.prim_types:
            super().__init__(preanalysis.TypeDef(eval(type_)))

    def __str__(self):
        return f"Primitive " + super().__str__()
