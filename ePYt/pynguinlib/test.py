from pathlib import Path
from unittest import TestCase

from .runner import Pynguin, Algorithm

class PynguinTestCase(TestCase):
    def test_pynguin(self):
        project_path = str(Path(__file__).parent)
        output_path = str(Path('outputs'))
        pynguin = Pynguin(Algorithm.WHOLE_SUITE, project_path, output_path)
        pynguin.run('target')
        pynguin.run('target', algorithm=Algorithm.RANDOM, project_path=project_path, output_path=f"rand_{output_path}")
        return True
