import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TaskHookTests(unittest.TestCase):
    def test_task_scoped_precompact_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".git").mkdir()
            (repo / "scripts/leanloop").mkdir(parents=True)
            for name in ("task.py", "leanloop_common.py"):
                shutil.copy2(ROOT / "scripts/leanloop" / name, repo / "scripts/leanloop" / name)
            hooks = repo / ".claude/hooks"
            shutil.copytree(ROOT / ".claude/hooks", hooks)
            cp = subprocess.run([sys.executable, "scripts/leanloop/task.py", "start", "feature-x"], cwd=repo, text=True, capture_output=True)
            self.assertEqual(cp.returncode, 0)
            payload = json.dumps({"cwd": str(repo), "trigger": "auto"})
            hook = subprocess.run([sys.executable, ".claude/hooks/precompact_checkpoint.py"], cwd=repo, input=payload, text=True, capture_output=True)
            self.assertEqual(hook.returncode, 0)
            checkpoint = repo / "state/tasks/feature-x/CHECKPOINT.md"
            self.assertTrue(checkpoint.exists())
            self.assertIn("feature-x", checkpoint.read_text())


if __name__ == "__main__":
    unittest.main()
