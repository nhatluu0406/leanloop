import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def test_installs_selected_tier_without_overwriting_existing_adapter_or_foreign_skill(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)
            (target / "AGENTS.md").write_text("# Existing project\n", encoding="utf-8")
            foreign = target / ".claude/skills/custom"
            foreign.mkdir(parents=True)
            (foreign / "SKILL.md").write_text("foreign\n", encoding="utf-8")
            cp = subprocess.run(
                [sys.executable, str(ROOT / "scripts/leanloop/install.py"), str(target), "--tiers", "0"],
                text=True, capture_output=True,
            )
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            self.assertIn("# Existing project", (target / "AGENTS.md").read_text())
            self.assertIn("LEANLOOP:ADAPTER:START", (target / "AGENTS.md").read_text())
            self.assertEqual((foreign / "SKILL.md").read_text(), "foreign\n")
            self.assertTrue((target / "scripts/leanloop/sync.py").exists())
            self.assertTrue((target / ".claude/skills/concise-output/SKILL.md").exists())
            doctor = subprocess.run([sys.executable, "scripts/leanloop/doctor.py"], cwd=target, text=True, capture_output=True)
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)

    def test_conflict_aborts_before_partial_install(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)
            conflict = target / "scripts/leanloop/sync.py"
            conflict.parent.mkdir(parents=True)
            conflict.write_text("project-owned\n", encoding="utf-8")

            cp = subprocess.run(
                [sys.executable, str(ROOT / "scripts/leanloop/install.py"), str(target), "--tiers", "0"],
                text=True, capture_output=True,
            )
            self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
            self.assertIn("installation did not start", cp.stdout)
            self.assertEqual(conflict.read_text(encoding="utf-8"), "project-owned\n")
            self.assertFalse((target / ".agents/skills/concise-output").exists())
            self.assertFalse((target / ".leanloop/kit/PLAYBOOK.md").exists())

    def test_invalid_claude_settings_aborts_without_overwriting(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)
            settings = target / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text("{not valid json\n", encoding="utf-8")

            cp = subprocess.run(
                [sys.executable, str(ROOT / "scripts/leanloop/install.py"), str(target), "--tiers", "0"],
                text=True, capture_output=True,
            )
            self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
            self.assertIn("installation did not start", cp.stdout)
            self.assertEqual(settings.read_text(encoding="utf-8"), "{not valid json\n")
            self.assertFalse((target / ".agents/skills/concise-output").exists())

    def test_adopts_identical_preexisting_propagated_skills(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)
            skill = "concise-output"
            src = ROOT / ".agents/skills" / skill
            for rel in (Path(".claude/skills") / skill, Path(".cursor/skills") / skill):
                shutil.copytree(src, target / rel)
            cp = subprocess.run(
                [sys.executable, str(ROOT / "scripts/leanloop/install.py"), str(target), "--tiers", "0"],
                text=True, capture_output=True,
            )
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            self.assertTrue((target / ".leanloop/install.json").exists())
            self.assertTrue((target / ".leanloop/managed.json").exists())

    def test_foreign_same_name_skill_aborts_before_install_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)
            conflict = target / ".cursor/skills/concise-output"
            conflict.mkdir(parents=True)
            (conflict / "SKILL.md").write_text("project-owned different skill\n", encoding="utf-8")
            cp = subprocess.run(
                [sys.executable, str(ROOT / "scripts/leanloop/install.py"), str(target), "--tiers", "0"],
                text=True, capture_output=True,
            )
            self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
            self.assertIn("installation did not start", cp.stdout)
            self.assertFalse((target / ".agents/skills/concise-output").exists())
            self.assertFalse((target / ".leanloop/kit/PLAYBOOK.md").exists())


if __name__ == "__main__":
    unittest.main()
