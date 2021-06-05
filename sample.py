import ePYt
import ast


class Class1:
    prop = "asdf"

    def __init__(self):
        self.a = 1

    def method(self):
        print('hi')


a = ePYt.preanalysis.TypeDef(Class1)
_ = input()
