import ePYt


class Class1:
    prop = "asdf"

    def __init__(self):
        self.a = 1

    def method(self):
        print(self.prop)


a = ePYt.analysis.Analyzer("./sample_target")
print(a.table)
analyzed_files = a.analyze(a.file_infos)
ePYt.annotator.Annotator.annotate_dir("./sample_target", analyzed_files)
