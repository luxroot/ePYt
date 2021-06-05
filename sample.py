import ePYt
import ast


class Class1:
    prop = "asdf"

    def __init__(self):
        self.a = 1

    def method(self):
        print(self.prop)


a = ePYt.preanalysis.TypeDef(Class1)
b = ePYt.domain.PrimitiveType("int")
print(repr(a))
print(repr(b))
_ = input()
