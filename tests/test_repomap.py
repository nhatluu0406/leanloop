import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepoMapTests(unittest.TestCase):
    def test_hidden_agent_dirs_are_mapped_but_git_is_not(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "scripts/leanloop").mkdir(parents=True)
            for name in ("repomap.py", "leanloop_common.py"):
                shutil.copy2(ROOT / "scripts/leanloop" / name, repo / "scripts/leanloop" / name)
            (repo / ".agents/skills/demo").mkdir(parents=True)
            (repo / ".agents/skills/demo/SKILL.md").write_text("# Demo\n", encoding="utf-8")
            (repo / ".git/objects").mkdir(parents=True)
            (repo / ".git/objects/junk").write_text("x", encoding="utf-8")
            (repo / "src").mkdir()
            (repo / "src/main.py").write_text("from .util import thing\n\ndef run():\n    pass\n", encoding="utf-8")
            cp = subprocess.run([sys.executable, "scripts/leanloop/repomap.py", "."], cwd=repo, text=True, capture_output=True)
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            text = (repo / "state/REPOMAP.md").read_text(encoding="utf-8")
            self.assertIn(".agents/", text)
            self.assertIn("main.py", text)
            self.assertNotIn(".git/objects", text)


if __name__ == "__main__":
    unittest.main()
