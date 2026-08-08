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

    def test_adopts_identical_unmanaged_skill(self):
        src = self.repo / ".agents/skills/demo"
        for rel in (Path(".claude/skills/demo"), Path(".cursor/skills/demo")):
            dest = self.repo / rel
            shutil.copytree(src, dest)
        cp = self.run_sync()
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("adopted", cp.stdout)
        manifest = json.loads((self.repo / ".leanloop/managed.json").read_text())
        self.assertIn("demo", manifest["targets"][".claude/skills"]["skills"])
        self.assertIn("demo", manifest["targets"][".cursor/skills"]["skills"])

    def test_conflict_preflight_does_not_partially_mutate_other_target(self):
        conflict = self.repo / ".cursor/skills/demo"
        conflict.mkdir(parents=True)
        (conflict / "SKILL.md").write_text("different foreign skill\n", encoding="utf-8")
        cp = self.run_sync()
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("aborted before changing any propagation target", cp.stdout + cp.stderr)
        self.assertFalse((self.repo / ".claude/skills/demo").exists())
        self.assertFalse((self.repo / ".leanloop/managed.json").exists())

    def test_scoped_sync_ignores_project_specific_canonical_skills(self):
        project_skill = self.repo / ".agents/skills/project-only"
        project_skill.mkdir(parents=True)
        (project_skill / "SKILL.md").write_text("project canonical\n", encoding="utf-8")
        project_copy = self.repo / ".claude/skills/project-only"
        project_copy.mkdir(parents=True)
        (project_copy / "SKILL.md").write_text("different project copy\n", encoding="utf-8")

        cp = self.run_sync("--skills", "demo")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertEqual((project_copy / "SKILL.md").read_text(encoding="utf-8"), "different project copy\n")
        manifest = json.loads((self.repo / ".leanloop/managed.json").read_text())
        self.assertIn("demo", manifest["targets"][".claude/skills"]["skills"])
        self.assertNotIn("project-only", manifest["targets"][".claude/skills"]["skills"])


if __name__ == "__main__":
    unittest.main()
