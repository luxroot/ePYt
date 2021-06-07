import ast
from copy import deepcopy
from itertools import chain
from pathlib import Path
from . import domain, graph, type_inferer


class FuncDef:
    def __init__(self, func_def: ast.FunctionDef):
        self.function_name = func_def.name
        self.args = func_def.args
        self.arg_types = {}
        self.graph = graph.Graph(func_def.body)

    def __str__(self):
        return f"def {self.function_name}({ast.unparse(self.args)})"

    def __repr__(self):
        return f"<FuncDef {str(self)}>"


class ClassDef:
    def __init__(self, class_def: ast.ClassDef):
        self.class_name = class_def.name
        self.func_defs = []
        for node in class_def.body:
            if isinstance(node, ast.FunctionDef):
                self.func_defs.append(FuncDef(node))

    def __str__(self):
        return f"class {self.class_name}:" + \
               ", ".join(map(lambda x: x.function_name, self.func_defs))

    def __repr__(self):
        return f"<ClassDef {str(self)}>"


class FileInfo:
    def __init__(self, script_path):
        self.path = Path(script_path)
        self.tree = ast.parse(self.path.read_text())
        self.func_defs = []
        self.class_defs = []
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                self.class_defs.append(ClassDef(node))
            elif isinstance(node, ast.FunctionDef):
                self.func_defs.append(FuncDef(node))


class Analyzer:
    prim_types = [*map(domain.PrimitiveType, domain.PrimitiveType.prim_types)]

    def __init__(self, dir_path):
        self.dir_path = Path(dir_path)
        self.type_inferer = type_inferer.TypeInferer(self.dir_path)
        # Can infer type by calling type_infer.get_type(lineno, colno)
        # self.type_infer = type_infer.TypeInfer(dir_path)
        self.file_infos = []
        for src_path in self.dir_path.rglob('*.py'):
            file_info = FileInfo(src_path)
            self.file_infos.append(file_info)
        self.analyzed_files = self.analyze(self.file_infos)


    def analyze(self, file_infos) -> FileInfo:
        analyzed_files = deepcopy(file_infos)
        for file_info in analyzed_files:
            analyzed_file = FileInfo(file_info.path)
            analyzed_files.append(analyzed_file)
            all_func_list = \
                list(chain(*map(lambda x: x.func_defs, file_info.class_defs)))
            all_func_list += file_info.func_defs
            for func_def in all_func_list:
                inferred_types = self.type_inferer.infer(func_def)
                func_def.arg_types = inferred_types

        return analyzed_files
