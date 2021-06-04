from inspect import signature, getmembers, isbuiltin


class TypeDef:
    @staticmethod
    def _has_signature(x):
        return not isbuiltin(x) or getattr(x, "__text_signature__", None)

    def __init__(self, class_):
        self.class_ = class_
        self.module_name = class_.__module__
        self.class_name = str(class_)[8:-2].split('.')[1]
        self.methods = list()
        self.properties = list()
        for member in getmembers(class_)[1:]:
            if not callable(member[1]):
                self.properties.append(member[0])
            elif self._has_signature(member[1]):
                self.methods.append((member[0], signature(member[1])))
                # Maybe we should use FullArgSpec instead of signature

    def __str__(self):
        return "\n".join(map(str, [f"Module : {str(self.module_name)}",
                                   f"Class : {str(self.class_name)}",
                                   "Methods",
                                   "\n".join(map(str, self.methods)),
                                   "Properties",
                                   "\n".join(self.properties)]))

    def __repr__(self):
        return f"TypeDef <{str(self)}>"
