import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "scripts/leanloop/install.py"


def run_install(target: Path, *args: str, source: Path = ROOT):
    return subprocess.run(
        [sys.executable, str(source / "scripts/leanloop/install.py"), str(target), *args],
        text=True,
        capture_output=True,
    )


class LifecycleTests(unittest.TestCase):
    def init_target(self, root: Path) -> Path:
        target = root / "target"
        target.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=target, check=True)
        return target

    def test_install_records_version_provenance_and_doctor_version(self):
        with tempfile.TemporaryDirectory() as td:
            target = self.init_target(Path(td))
            cp = run_install(target, "--tiers", "0")
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            manifest = json.loads((target / ".leanloop/install.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["leanloop_version"], (ROOT / "VERSION").read_text().strip())
            self.assertEqual(manifest["installed_tiers"], ["0"])
            self.assertIn("scripts/leanloop/install.py", manifest["managed_files"])
            version = subprocess.run(
                [sys.executable, "scripts/leanloop/doctor.py", "--version"],
                cwd=target, text=True, capture_output=True,
            )
            self.assertEqual(version.returncode, 0, version.stdout + version.stderr)
            self.assertEqual(version.stdout.strip(), (ROOT / "VERSION").read_text().strip())

    def test_upgrade_can_add_tier_without_redeclaring_existing_tiers(self):
        with tempfile.TemporaryDirectory() as td:
            target = self.init_target(Path(td))
            self.assertEqual(run_install(target, "--tiers", "0,1").returncode, 0)
            cp = run_install(target, "--upgrade", "--add-tiers", "2")
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            manifest = json.loads((target / ".leanloop/install.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["installed_tiers"], ["0", "1", "2"])
            self.assertTrue((target / ".agents/skills/token-telemetry/SKILL.md").exists())
            self.assertTrue((target / ".claude/skills/token-telemetry/SKILL.md").exists())

    def test_install_refuses_same_name_foreign_skill_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            target = self.init_target(Path(td))
            foreign = target / ".claude/skills/concise-output/SKILL.md"
            foreign.parent.mkdir(parents=True)
            foreign.write_text("foreign same-name\n", encoding="utf-8")
            cp = run_install(target, "--tiers", "0")
            self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
            self.assertIn("foreign skill conflicts", cp.stdout)
            self.assertEqual(foreign.read_text(), "foreign same-name\n")
            self.assertFalse((target / ".leanloop/install.json").exists())
            self.assertFalse((target / "scripts/leanloop/install.py").exists())

    def test_upgrade_can_remove_a_tier_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            target = self.init_target(Path(td))
            self.assertEqual(run_install(target, "--tiers", "0,1").returncode, 0)
            cp = run_install(target, "--upgrade", "--tiers", "0")
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            self.assertFalse((target / ".agents/skills/read-budget").exists())
            self.assertFalse((target / ".claude/skills/read-budget").exists())
            first = json.loads((target / ".leanloop/install.json").read_text(encoding="utf-8"))
            cp = run_install(target, "--upgrade")
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            second = json.loads((target / ".leanloop/install.json").read_text(encoding="utf-8"))
            self.assertEqual(first["installed_tiers"], second["installed_tiers"])
            self.assertEqual(first["managed_files"], second["managed_files"])
            self.assertEqual(first["sync_ownership_hash"], second["sync_ownership_hash"])

    def test_upgrade_refuses_locally_modified_managed_file_before_writing(self):
        with tempfile.TemporaryDirectory() as td:
            target = self.init_target(Path(td))
            self.assertEqual(run_install(target, "--tiers", "0").returncode, 0)
            managed = target / "scripts/leanloop/task.py"
            managed.write_text(managed.read_text(encoding="utf-8") + "\n# local edit\n", encoding="utf-8")
            before_manifest = (target / ".leanloop/install.json").read_bytes()
            cp = run_install(target, "--upgrade")
            self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
            self.assertIn("managed file modified locally", cp.stdout)
            self.assertEqual((target / ".leanloop/install.json").read_bytes(), before_manifest)
            self.assertTrue(managed.read_text(encoding="utf-8").endswith("# local edit\n"))

    def test_upgrade_replaces_unchanged_managed_file_from_new_source(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            target = self.init_target(base)
            self.assertEqual(run_install(target, "--tiers", "0").returncode, 0)

            source2 = base / "source2"
            shutil.copytree(ROOT, source2, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
            (source2 / "VERSION").write_text("1.0.0-rc.2\n", encoding="utf-8")
            changed = source2 / "scripts/leanloop/task.py"
            changed.write_text(changed.read_text(encoding="utf-8") + "\n# rc2 marker\n", encoding="utf-8")

            cp = run_install(target, "--upgrade", source=source2)
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            self.assertIn("# rc2 marker", (target / "scripts/leanloop/task.py").read_text(encoding="utf-8"))
            manifest = json.loads((target / ".leanloop/install.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["leanloop_version"], "1.0.0-rc.2")

    def test_uninstall_preserves_foreign_skill_adapter_text_and_task_state(self):
        with tempfile.TemporaryDirectory() as td:
            target = self.init_target(Path(td))
            (target / "AGENTS.md").write_text("# Project rules\n\nKeep me.\n", encoding="utf-8")
            foreign = target / ".claude/skills/custom/SKILL.md"
            foreign.parent.mkdir(parents=True)
            foreign.write_text("foreign\n", encoding="utf-8")
            self.assertEqual(run_install(target, "--tiers", "0").returncode, 0)
            handoff = target / "state/tasks/product/HANDOFF.md"
            handoff.parent.mkdir(parents=True)
            handoff.write_text("user state\n", encoding="utf-8")

            cp = run_install(target, "--uninstall")
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            self.assertTrue(foreign.exists())
            self.assertEqual(foreign.read_text(), "foreign\n")
            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# Project rules", agents)
            self.assertNotIn("LEANLOOP:ADAPTER", agents)
            self.assertEqual(handoff.read_text(), "user state\n")
            self.assertFalse((target / "scripts/leanloop/install.py").exists())
            self.assertFalse((target / ".agents/skills/concise-output").exists())
            self.assertFalse((target / ".leanloop/install.json").exists())

    def test_uninstall_refuses_tampered_sync_ownership_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            target = self.init_target(Path(td))
            self.assertEqual(run_install(target, "--tiers", "0").returncode, 0)
            path = target / ".leanloop/managed.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["targets"][".claude/skills"]["skills"]["invented-foreign"] = "deadbeef"
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            cp = run_install(target, "--uninstall")
            self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
            self.assertIn("ownership manifest changed", cp.stdout)
            self.assertTrue((target / ".leanloop/install.json").exists())

    def test_uninstall_refuses_modified_propagated_skill(self):
        with tempfile.TemporaryDirectory() as td:
            target = self.init_target(Path(td))
            self.assertEqual(run_install(target, "--tiers", "0").returncode, 0)
            propagated = target / ".claude/skills/concise-output/SKILL.md"
            propagated.write_text(propagated.read_text(encoding="utf-8") + "\nlocal\n", encoding="utf-8")
            cp = run_install(target, "--uninstall")
            self.assertEqual(cp.returncode, 1, cp.stdout + cp.stderr)
            self.assertIn("propagated managed skill modified locally", cp.stdout)
            self.assertTrue((target / ".leanloop/install.json").exists())

    def test_custom_statusline_survives_install_and_uninstall(self):
        with tempfile.TemporaryDirectory() as td:
            target = self.init_target(Path(td))
            settings = target / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text(json.dumps({"statusLine": {"type": "command", "command": "custom-status"}}), encoding="utf-8")
            cp = run_install(target, "--tiers", "0")
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            installed = json.loads(settings.read_text())
            self.assertEqual(installed["statusLine"]["command"], "custom-status")
            cp = run_install(target, "--uninstall")
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            final = json.loads(settings.read_text())
            self.assertEqual(final["statusLine"]["command"], "custom-status")


if __name__ == "__main__":
    unittest.main()
