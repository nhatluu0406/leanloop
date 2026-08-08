import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WorktreeTests(unittest.TestCase):
    def test_worker_gets_isolated_branch_index_and_task_state(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "LeanLoop Test"], cwd=repo, check=True)
            shutil.copytree(ROOT / "scripts/leanloop", repo / "scripts/leanloop")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)

            parent = Path(td) / "workers"
            create = subprocess.run(
                [
                    sys.executable,
                    str(repo / "scripts/leanloop/worktree.py"),
                    "create",
                    "feature-a",
                    "--parent",
                    str(parent),
                ],
                cwd=repo,
                text=True,
                capture_output=True,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            worker = parent / "feature-a"
            self.assertTrue(worker.exists())
            branch = subprocess.run(
                ["git", "branch", "--show-current"], cwd=worker, text=True, capture_output=True, check=True
            ).stdout.strip()
            self.assertEqual(branch, "leanloop/feature-a")
            self.assertEqual((worker / "state/CURRENT_TASK").read_text(encoding="utf-8").strip(), "feature-a")

            # A worker change must not appear in the orchestrator tree/index.
            (worker / "worker.txt").write_text("isolated\n", encoding="utf-8")
            main_status = subprocess.run(
                ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout
            self.assertEqual(main_status, "")

            # Force is intentional here because the test leaves worker.txt uncommitted.
            remove = subprocess.run(
                [sys.executable, str(repo / "scripts/leanloop/worktree.py"), "remove", "feature-a", "--force"],
                cwd=repo,
                text=True,
                capture_output=True,
            )
            self.assertEqual(remove.returncode, 0, remove.stdout + remove.stderr)
            self.assertFalse(worker.exists())


if __name__ == "__main__":
    unittest.main()
