import ast
from copy import deepcopy
from typing import List
import shutil
from pathlib import Path
from . import analysis


class NodeAnnotator(ast.NodeTransformer):
    def __init__(self, analyzed_file: analysis.FileInfo):
        self.analyzed_file = analyzed_file

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
            class_def = self.analyzed_file.class_defs[class_name]
            func_defs = class_def.func_defs
        func_def = func_defs.get(node.name, None)
        if func_def is None:
            return node
        for arg in node.args.args:
            inferred_types = func_def.arg_types.get(arg.arg, None)
            if not inferred_types:
                continue
            inferred_type_names = list(
                map(lambda x: x.class_.__name__, inferred_types))
            annotation = self.create_union(inferred_type_names)
            if annotation:
                arg.annotation = annotation
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        return self.annotate_FunctionDef(node, None)

    def visit_ClassDef(self, node):
        for body in node.body:
            if not isinstance(body, ast.FunctionDef):
                continue
            self.annotate_FunctionDef(body, node.name)
        return node

    @staticmethod
    def create_import_from(module, names):
        names = list(map(lambda x: ast.alias(name=x), names))
        import_from = ast.ImportFrom(module=module, names=names, level=0)
        return import_from

    def visit_Module(self, node):
        import_union = self.create_import_from('typing', ['Union'])
        node.body.insert(0, import_union)
        self.generic_visit(node)
        return node


class Annotator:
    @staticmethod
    def annotate(analyzed_file):
        tree = deepcopy(analyzed_file.tree)
        node_annotator = NodeAnnotator(analyzed_file)
        tree = node_annotator.visit(tree)
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


'''
/a/b/c/d.py
/a/b.annotated
/a
'''
