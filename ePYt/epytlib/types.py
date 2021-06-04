from inspect import signature, getmembers


class TypeBase:
    pass


class AnyType(TypeBase):
    def __init__(self):
        super().__init__()
        self.is_Any = True


class HasAttr(TypeBase):
    def __init__(self):
        super().__init__()
        self.is_Any = False
        self.properties = list()
        self.methods = list()


class PrimitiveType(HasAttr):
    prim_types = ["int", "str", "list"]  # TODO: To be filled

    def __init__(self, type_):
        super().__init__()
        if type_ in self.prim_types:
            self.type_def = TypeDef(eval(type_))
            self.properties.extend(self.type_def.properties)
            self.methods.extend(self.type_def.methods)


class TypeDef:
    @staticmethod
    def _get_signature(x):
        try:
            return signature(x)
        except ValueError:
            return None

    def __init__(self, class_):
        self.class_ = class_
        self.module_name = class_.__module__
        self.class_name = str(class_)[8:-2]
        if self.module_name != "builtins":
            self.class_name = self.class_name.split('.')[1]
        self.methods = list()
        self.properties = list()
        for key, value in getmembers(class_):
            if callable(value):
                self.methods.append((key, self._get_signature(value)))
            else:
                self.properties.append(key)

    def __str__(self):
        return "\n".join(map(str, [f"Module : {str(self.module_name)}",
                                   f"Class : {str(self.class_name)}",
                                   "Methods",
                                   "\n".join(map(str, self.methods)),
                                   "Properties",
                                   "\n".join(self.properties)]))

    def __repr__(self):
        return f"TypeDef <{str(self)}>"
