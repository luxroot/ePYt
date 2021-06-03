from inspect import signature, getmembers


class ClassDef:
    @staticmethod
    def has_signature(x):
        s = getattr(x, "__text_signature__", None)
        return s

    def __init__(self, class_):
        self.methods = \
            list(map(lambda x: (x[0], signature(x[1])),
                     filter(lambda y:
                            callable(y[1]) and self.has_signature(y[1]),
                            getmembers(class_)[1:])))
        self.properties = \
            list(map(lambda x: x[0],
                     filter(lambda y: not callable(y[1]), getmembers(class_))))
