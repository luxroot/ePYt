import ePYt


class Class1:
    prop = "asdf"

    def __init__(self):
        self.a = 1

    def method(self):
        print(self.prop)


analysis_result = ePYt.analysis.Analyzer("./sample_target")
print(analysis_result.type_inferrer.table)
_ = input()
