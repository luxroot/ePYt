import ast
from itertools import chain
from itertools import chain
from pathlib import Path
from . import preanalysis, domain, type_infer, graph, semantic


class FuncDef:
    def __init__(self, func_def: ast.FunctionDef):
        self.function_name = func_def.name
        self.args = func_def.args
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
        script_path = Path(script_path)
        tree = ast.parse(script_path.read_text())
        self.func_defs = []
        self.class_defs = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self.class_defs.append(ClassDef(node))
            elif isinstance(node, ast.FunctionDef):
                self.func_defs.append(FuncDef(node))


class Analyzer:
    prim_types = [*map(domain.PrimitiveType, domain.PrimitiveType.prim_types)]

    def __init__(self, file_path):
        self.user_types = preanalysis.get_typedefs(file_path)
        # Can infer type by calling type_infer.get_type(lineno, colno)
        self.type_infer = type_infer.TypeInfer(file_path)
        self.file_info = FileInfo(file_path)
        self.semantic = semantic.Semantic()
        self.all_func_list = list(chain(*map(lambda x: x.func_defs, self.file_info.class_defs))) + self.file_info.func_defs

        for func_def in self.all_func_list:
            self.semantic.run(func_def)
