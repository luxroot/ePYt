import ast
from inspect import signature, getmembers
from . import domain


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
        self.type = domain.HasAttr()
        for key, value in getmembers(class_):
            if callable(value):
                self.type.methods.append((key, self._get_signature(value)))
            else:
                self.type.properties.append(key)

    def __str__(self):
        return "\n".join(map(str, [f"Module : {str(self.module_name)}",
                                   f"Class name : {str(self.class_name)}",
                                   "Corresponding HasAttr:",
                                   str(self.type)]))

    def __repr__(self):
        return f"TypeDef <{str(self)}>"


def get_typedefs(script):
    tree = ast.parse(script)
    tree
