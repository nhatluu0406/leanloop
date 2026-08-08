import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "scripts/leanloop").mkdir(parents=True)
        for name in ("sync.py", "leanloop_common.py"):
            shutil.copy2(ROOT / "scripts/leanloop" / name, self.repo / "scripts/leanloop" / name)
        skill = self.repo / ".agents/skills/demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: demo\ndescription: demo\n---\n# Demo\n", encoding="utf-8")
        foreign = self.repo / ".claude/skills/custom"
        foreign.mkdir(parents=True)
        (foreign / "SKILL.md").write_text("foreign", encoding="utf-8")
        (self.repo / ".cursor/skills/custom").mkdir(parents=True)
        (self.repo / ".cursor/skills/custom/SKILL.md").write_text("foreign", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_sync(self, *args):
        return subprocess.run([sys.executable, "scripts/leanloop/sync.py", *args], cwd=self.repo, text=True, capture_output=True)

    def test_preserves_foreign_skills(self):
        cp = self.run_sync()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertTrue((self.repo / ".claude/skills/custom/SKILL.md").exists())
        self.assertTrue((self.repo / ".cursor/skills/custom/SKILL.md").exists())
        self.assertTrue((self.repo / ".claude/skills/demo/SKILL.md").exists())
        manifest = json.loads((self.repo / ".leanloop/managed.json").read_text())
        self.assertIn("demo", manifest["targets"][".claude/skills"]["skills"])
        self.assertNotIn("custom", manifest["targets"][".claude/skills"]["skills"])

    def test_refuses_to_overwrite_modified_managed_copy(self):
        self.assertEqual(self.run_sync().returncode, 0)
        dest = self.repo / ".claude/skills/demo/SKILL.md"
        dest.write_text(dest.read_text() + "local edit\n", encoding="utf-8")
        cp = self.run_sync()
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("changed locally", cp.stderr + cp.stdout)


if __name__ == "__main__":
    unittest.main()
