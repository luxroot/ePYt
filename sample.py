import ePYt


class Cls1:
    prop1 = "prop1"

    def method1(self):
        pass


a = ePYt.types.TypeDef(Cls1)
b = ePYt.graph.from_file("./target.py")
print(a)
_ = input()
