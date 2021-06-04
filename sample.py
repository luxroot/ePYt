import ePYt
import ast


a = ast.parse('''class AClass:
    def method(self, a: int):
        pass


class BClass:
    def method(self, a: str):
        pass


def func(var):
    var.method(3)
''')
#
#
#
# fvisit = ePYt.analysis.FuncVisitor()
# fvisit.visit(a)

a = ePYt.domain.PrimitiveType("list")
print(a)
_ = input()
