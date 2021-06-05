import pathlib


class Class1:
    prop = "asdf"

    def __init__(self):
        self.a = 1

    def method(self):
        print(self.prop)


def func(var):
    a = pathlib.Path("./asdf")
    var.method(3)
    var + 2
