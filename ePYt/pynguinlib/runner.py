from typing import Optional, Union
import subprocess

import pynguin
from pynguin import Configuration, set_configuration
from pynguin.generator import ReturnCode


Algorithm = pynguin.Algorithm


class Pynguin(object):

    def __init__(self, algorithm: Algorithm, project_path: str, output_path: str,):
        self.algorithm = algorithm
        self.project_path = project_path
        self.output_path = output_path

    def run_pynguin(self, algorithm: Algorithm, project_path: str, output_path: str, module_name: str) -> ReturnCode:
        configuration = Configuration(
            algorithm=algorithm, project_path=project_path, output_path=output_path, module_name=module_name)
        set_configuration(configuration)
        return pynguin.run_pynguin().value

    def spawn_pynguin(self, algorithm: Algorithm, project_path: str, output_path: str, module_name: str,
                      capture_output: Optional[bool] = False) -> subprocess.CompletedProcess:
        args = ["pynguin", "--algorithm", Algorithm(algorithm).value,
                "--project_path", project_path, "--output_path", output_path,
                "--module_name", module_name]
        return subprocess.run(args, capture_output=capture_output)

    def run(self, module_name: str,
            spawn: Optional[bool] = True, capture_output: Optional[bool] = False,
            **kwargs) -> Union[ReturnCode, subprocess.CompletedProcess]:
        algorithm = kwargs.get("algorithm", self.algorithm)
        project_path = kwargs.get("project_path", self.project_path)
        output_path = kwargs.get("output_path", self.output_path)
        if spawn:
            return self.spawn_pynguin(algorithm, project_path, output_path, module_name, spawn, capture_output)
        return self.run_pynguin(algorithm, project_path, output_path, module_name)
