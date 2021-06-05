import ePYt
import ast


class Class1:
    prop = "asdf"

    def __init__(self):
        self.a = 1

    def method(self):
        print(self.prop)


a = ePYt.analysis.Analyzer("./target.py")
b = ePYt.graph.parse_from_file("./target.py")
_ = input()
