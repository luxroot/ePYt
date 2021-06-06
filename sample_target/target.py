class BaseClass:
    base_prop = 1

    def init(self):
        # Custom init prop
        self.custom_base_init_prop = 2

    def __init__(self):
        self.base_init_prop = 3
        self.init()


class DerivedClass(BaseClass):
    derived_prop = 4

    def init(self):
        # Custom init prop
        self.custom_derived_init_prop = 5

    def __init__(self):
        super().__init__()
        self.derived_init_prop = 6
        self.init()
