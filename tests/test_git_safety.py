import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


class GitSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        run(["git", "init"], self.repo)
        run(["git", "config", "user.email", "leanloop@example.invalid"], self.repo)
        run(["git", "config", "user.name", "LeanLoop Test"], self.repo)
        (self.repo / "scripts/leanloop").mkdir(parents=True)
        for name in ("git_guard.py", "safe_commit.py", "leanloop_common.py"):
            shutil.copy2(ROOT / "scripts/leanloop" / name, self.repo / "scripts/leanloop" / name)
        (self.repo / "a.txt").write_text("a\n")
        (self.repo / "b.txt").write_text("b\n")
        run(["git", "add", "a.txt", "b.txt"], self.repo)
        run(["git", "commit", "-m", "init"], self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def test_guard_rejects_dirty_tree(self):
        (self.repo / "a.txt").write_text("changed\n")
        cp = run([sys.executable, "scripts/leanloop/git_guard.py"], self.repo)
        self.assertEqual(cp.returncode, 1)
        self.assertIn("not clean", cp.stdout)

    def test_safe_commit_only_stages_allowlist(self):
        (self.repo / "a.txt").write_text("changed a\n")
        (self.repo / "b.txt").write_text("changed b\n")
        cp = run([sys.executable, "scripts/leanloop/safe_commit.py", "-m", "plan#1: a", "a.txt"], self.repo)
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        status = run(["git", "status", "--porcelain"], self.repo).stdout
        self.assertIn(" M b.txt", status)
        self.assertNotIn("a.txt", status)

    def test_safe_commit_rejects_broad_staging(self):
        cp = run([sys.executable, "scripts/leanloop/safe_commit.py", "-m", "bad", "."], self.repo)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("forbidden", cp.stdout)


if __name__ == "__main__":
    unittest.main()
