from urllib1.request import URLopener
class B():
    def __init__(self, f: URLopener):
        self.f = f

        
class C():
    def __init__(self, o, n: int):
        self.o = o 
        self.n = n 
    
    def add(self, a: float, b):
        return a + b + self.n + self.o.n

class E():
    def zxcv(self, x) -> C:
        return C(1, 2)