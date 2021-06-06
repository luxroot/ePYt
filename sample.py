import ePYt
import ast


class Class1:
    prop = "asdf"

    def __init__(self):
        self.a = 1

    def method(self):
        print(self.prop)


# a = ePYt.analysis.Analyzer("sample_target/target.py")
b = ePYt.preanalysis.get_typedefs("sample_target")
_ = input()
