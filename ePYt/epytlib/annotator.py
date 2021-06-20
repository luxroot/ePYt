import ast
from copy import deepcopy
from typing import List
import shutil
from pathlib import Path
from . import analysis


def create_import(names):
    names = list(map(lambda x: ast.alias(name=x), names))
    import_ = ast.Import(names=names)
    return import_


def create_import_from(module, names):
    names = list(map(lambda x: ast.alias(name=x), names))
    import_from = ast.ImportFrom(module=module, names=names, level=0)
    return import_from


def is_my_module(file_info, module_name):
    return module_name.endswith(f".{file_info.path.stem}")


class NodeAnnotator(ast.NodeTransformer):
    def __init__(self, analyzed_file: analysis.FileInfo):
        self.analyzed_file = analyzed_file
        self.imports = {}

    @staticmethod
    def create_union(ids: List[str]):
        value = ast.Name(id='Union')
        elts = list(map(lambda x: ast.Name(id=x), ids))
        slice = ast.Tuple(elts=elts)
        subscript = ast.Subscript(value=value, slice=slice)
        return subscript

    def annotate_FunctionDef(self, node, class_name=None):
        if class_name is None:
            func_defs = self.analyzed_file.func_defs
        else:
            class_def = self.analyzed_file.class_defs.get(class_name, None)
            if class_def is None:
                return node
            func_defs = class_def.func_defs
        func_def = func_defs.get(node.name, None)
        if func_def is None:
            return node
        for arg in node.args.args:
            inferred_types = func_def.arg_types.get(arg.arg, None)
            if not inferred_types:
                continue
            inferred_type_names = list(
                map(
                    lambda x: f"{x.module_name}.{x.class_.__name__}"
                    if not is_my_module(self.analyzed_file, x.module_name) else
                    f"{x.class_.__name__}", inferred_types))
            annotation = self.create_union(inferred_type_names)
            if annotation:
                arg.annotation = annotation
            for inferred_type in inferred_types:
                if inferred_type.module_name not in self.imports:
                    self.imports[inferred_type.module_name] = []
                import_name = inferred_type.class_.__name__
                module_imports = self.imports[inferred_type.module_name]
                if import_name not in module_imports:
                    module_imports.append(import_name)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        return self.annotate_FunctionDef(node, None)

    def visit_ClassDef(self, node):
        for body in node.body:
            if not isinstance(body, ast.FunctionDef):
                continue
            self.annotate_FunctionDef(body, node.name)
        return node

    def visit_Module(self, node):
        import_union = create_import_from('typing', ['Union'])
        node.body.insert(0, import_union)
        self.generic_visit(node)
        return node


class NodeImporter(ast.NodeTransformer):
    def __init__(self, file_info, imports: dict):
        self.file_info = file_info
        self.imports = imports

    def visit_Module(self, node):
        for module_name, import_names in self.imports.items():
            if is_my_module(self.file_info,
                            module_name):  # TODO: Avoid to import itself
                for import_name in import_names:
                    dummy_class_def = ast.ClassDef(name=import_name,
                                                   decorator_list=[],
                                                   bases=[],
                                                   keywords=[], body=[ast.Pass()])
                    node.body.insert(0, dummy_class_def)
                continue
            import_ = create_import([module_name])
            node.body.insert(0, import_)
        self.generic_visit(node)
        return node


class Annotator:
    @staticmethod
    def annotate(analyzed_file):
        tree = deepcopy(analyzed_file.tree)
        node_annotator = NodeAnnotator(analyzed_file)
        tree = node_annotator.visit(tree)
        node_importer = NodeImporter(analyzed_file, node_annotator.imports)
        tree = node_importer.visit(tree)
        return tree

    @staticmethod
    def annotate_dir(dir_path, analyzed_files, output_dir=None):
        dir_path = Path(dir_path)
        if output_dir:
            new_dir_path = Path(output_dir)
        else:
            new_dir_path = Path(f"{str(dir_path)}.annotated")
        shutil.copytree(dir_path, new_dir_path, dirs_exist_ok=True)
        for analyzed_file in analyzed_files:
            relative_path = analyzed_file.path.relative_to(dir_path)
            annoatated_path = new_dir_path / relative_path
            annotated_code = ast.unparse(Annotator.annotate(analyzed_file))
            annoatated_path.write_text(annotated_code)
