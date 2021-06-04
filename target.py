class AClass:
    def method(self, a):
        return a + 3


class BClass:
    def method(self, a: str):
        pass


def func(var):
    var.method(3)
