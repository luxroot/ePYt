from inspect import signature, getmembers


class TypeDef:
    @staticmethod
    def _has_signature(x):
        s = getattr(x, "__text_signature__", None)
        return s

    def __init__(self, class_):
        self.class_ = class_
        self.module_name = class_.__module__
        self.class_name = str(class_)[8:-2].split('.')[1]
        self.methods = \
            list(map(lambda x: (x[0], signature(x[1])),
                     filter(lambda y:
                            callable(y[1]) and self._has_signature(y[1]),
                            getmembers(class_)[1:])))
        self.properties = \
            list(map(lambda x: x[0],
                     filter(lambda y: not callable(y[1]), getmembers(class_))))

    def __str__(self):
        return "\n".join(map(str, [f"Module : {str(self.module_name)}",
                                   f"Class : {str(self.class_name)}",
                                   "Methods",
                                   "\n".join(map(str, self.methods)),
                                   "Properties",
                                   "\n".join(self.properties)]))

    def __repr__(self):
        return f"TypeDef <{str(self)}>"
