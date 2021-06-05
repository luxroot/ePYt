import ast
from inspect import signature, getmembers, isclass
from pathlib import Path
from types import ModuleType
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
                if hasattr(object, key) and value == getattr(object, key):
                    continue
                self.type.methods.append((key, self._get_signature(value)))
            else:
                self.type.properties.append(key)

    def __str__(self):
        return "\n".join(map(str, [f"Module : {self.module_name}",
                                   f"Class name : {self.class_name}",
                                   "Corresponding HasAttr:",
                                   str(self.type)]))

    def __repr__(self):
        return f"<TypeDef {self.module_name}.{self.class_name}\t" + \
               f"{repr(self.type)}"


def get_typedefs(script_path):
    script_path = Path(script_path)
    tree = ast.parse(script_path.read_text())
    compiled = compile(tree, "name", "exec")

    module = ModuleType(script_path.stem)
    module.__loader__ = __loader__
    module.__file__ = str(script_path)
    module.__builtins__ = __builtins__
    gvars = module.__dict__
    try:
        exec(compiled, gvars)
    except SystemExit:
        pass
    classes = list(filter(isclass, gvars.values()))
    class_types = list(map(TypeDef, classes))
    return class_types
