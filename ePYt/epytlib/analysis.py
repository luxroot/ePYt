import ast
from itertools import chain
from itertools import chain
from pathlib import Path
from . import preanalysis, domain, type_infer, graph, semantic


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

    def __init__(self, dir_path):
        self.dir_path = Path(dir_path)
        self.user_types = preanalysis.get_typedefs(dir_path)
        # Can infer type by calling type_infer.get_type(lineno, colno)
        # self.type_infer = type_infer.TypeInfer(dir_path)
        self.file_infos = []
        for src_path in self.dir_path.rglob('*.py'):
            file_info = FileInfo(src_path)
            self.file_infos.append(file_info)
        self.analyze(self.file_infos)

    def run_semantic(self, func_def: FuncDef):
        semantic.Semantic(func_def)
        for node in func_def.graph.nodes:
            for variable, value in node.memory.memory.items():
                node_attrs = set(value.attributes)
                fit_user_types = filter(
                    lambda x: set(x.type.attributes).issuperset(node_attrs),
                    self.user_types.values())
                func_def.arg_types[variable] = list(fit_user_types)
        return func_def

    def analyze(self, file_infos: list):
        for file_info in self.file_infos:
            all_func_list = \
                list(chain(*map(lambda x: x.func_defs, file_info.class_defs)))
            all_func_list += file_info.func_defs
            for func_def in all_func_list:
                self.run_semantic(func_def)
        return file_infos
