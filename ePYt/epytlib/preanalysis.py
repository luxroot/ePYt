import ast
from inspect import signature, getmembers, isclass, getmro
from pathlib import Path
from types import ModuleType
from typing import Dict
import sys

from . import domain


class TypeDef:
    @staticmethod
    def _get_signature(x):
        try:
            return signature(x)
        except ValueError:
            return None

    @staticmethod
    def make_class_name(module_name, class_name):
        return f"{module_name}.{class_name}"

    def __init__(self, class_):
        self.class_ = class_
        self.module_name = class_.__module__
        self.class_name = self.make_class_name(self.module_name,
                                               class_.__name__)
        self.type = domain.HasAttr()
        self.base_classes = tuple(
            filter(lambda x: x not in (class_, object), getmro(class_)))
        self.base_class_types = []
        for key, value in getmembers(class_):
            if callable(value):
                if hasattr(object, key) and value == getattr(object, key):
                    continue
                # self.type.methods.append((key, self._get_signature(value)))
                self.type.methods.append(key)
            else:
                self.type.properties.append(key)
        self.init_properties = []

    def __str__(self):
        return "\n".join(
            map(str, [
                f"Module : {self.module_name}",
                f"Class name : {self.class_name}", "Corresponding HasAttr:",
                str(self.type)
            ]))

    def __repr__(self):
        return f"<TypeDef {self.module_name}.{self.class_name}\t" + \
               f"{repr(self.type)}"


class MethodsVisitor(ast.NodeVisitor):
    def __init__(self):
        self.methods: Dict[str, Dict[str, ast.AST]] = {}

    def visit_ClassDef(self, node):
        for body in node.body:
            if not isinstance(body, ast.FunctionDef):
                continue
            if node.name not in self.methods:
                self.methods[node.name] = {}
            self.methods[node.name][body.name] = body


class InitPropertiesVisitor(ast.NodeVisitor):
    @staticmethod
    def get_self_attr(node):
        if not isinstance(node, ast.Attribute):
            return None
        if not (hasattr(node.value, 'id') and node.value.id == 'self'):
            return None
        return node.attr

    def __init__(self, methods):
        self.init_properties: Dict[str, list] = {}
        self.methods: Dict[str, list] = methods

    def handle_call_in_init(self, class_name, node):
        call_func = self.get_self_attr(node.func)
        if not call_func:
            return
        if class_name not in self.methods or \
                call_func not in self.methods[class_name]:
            return  # not support base_class
        self.handle_init(class_name, self.methods[class_name][call_func])

    def handle_init(self, class_name, init):
        for body in init.body:
            if not (isinstance(body, ast.Assign)
                    or isinstance(body, ast.AugAssign)):
                for node in ast.walk(body):
                    if not isinstance(node, ast.Call):
                        continue
                    self.handle_call_in_init(class_name, node)
                continue
            assign = body
            targets = getattr(assign, 'target', None)
            targets = getattr(assign, 'targets', None)
            if hasattr(assign, 'target'):
                targets = [assign.target]
            elif hasattr(assign, 'targets'):
                targets = assign.targets
            else:
                continue  # raise ?
            for target in targets:
                attr_name = self.get_self_attr(target)
                if not attr_name:
                    continue
                if class_name not in self.init_properties:
                    self.init_properties[class_name] = []
                self.init_properties[class_name].append(attr_name)

    def visit_ClassDef(self, node):
        for body in node.body:
            if not isinstance(body, ast.FunctionDef):
                continue
            if body.name == "__init__":
                self.handle_init(node.name, body)


def make_module_name(dir_path, src_path):
    parts = src_path.relative_to(dir_path.parent).with_suffix('').parts
    module_name = '.'.join(map(str, parts))
    return module_name


def get_typedefs(script_dir_path) -> Dict[str, TypeDef]:
    script_dir_path = Path(script_dir_path)
    sys.path.append(str(script_dir_path.parent))
    class_types = {}
    script_paths = list(script_dir_path.rglob('*.py'))
    for script_path in script_paths:
        module_name = make_module_name(script_dir_path, script_path)
        tree = ast.parse(script_path.read_text())
        compiled = compile(tree, "name", "exec")
        module = ModuleType(module_name)
        module.__loader__ = __loader__
        module.__file__ = str(script_path)
        module.__builtins__ = __builtins__
        gvars = module.__dict__
        try:
            exec(compiled, gvars)
        except SystemExit:
            pass
        classes = list(filter(isclass, gvars.values()))
        for class_ in classes:
            class_type = TypeDef(class_)
            class_types[class_type.class_name] = class_type
    sys.path.pop()

    # add all base_class_types recursively
    for class_type in list(class_types.values()):

        def add_base_class(class_types_, class_type_):
            for base_class in class_type_.base_classes:
                if base_class in class_types_.keys():
                    continue
                base_class_type_ = TypeDef(base_class)
                class_types_[base_class_type_.class_name] = base_class_type_
                class_type_.base_class_types.append(base_class_type_)
                add_base_class(class_types_, base_class_type_)

        add_base_class(class_types, class_type)

    for script_path in script_paths:
        # get init properties
        module_name = make_module_name(script_dir_path, script_path)
        tree = ast.parse(script_path.read_text())
        methods_visitor = MethodsVisitor()
        methods_visitor.visit(tree)
        init_props_visitor = InitPropertiesVisitor(methods_visitor.methods)
        init_props_visitor.visit(tree)
        init_props = init_props_visitor.init_properties
        for class_name, init_props in init_props.items():
            name = TypeDef.make_class_name(module_name, class_name)
            class_type = class_types[name]
            class_type.init_properties = init_props
            class_type.type.properties.extend(init_props)

    # merge from base_class
    for class_type in class_types.values():
        props = class_type.type.properties
        for base_class_type in class_type.base_class_types:
            for base_class_init_prop in base_class_type.init_properties:
                if base_class_init_prop in props:
                    continue
                props.append(base_class_init_prop)
    return class_types
