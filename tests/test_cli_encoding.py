import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cp1252_env():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252:strict"
    return env


class CliEncodingTests(unittest.TestCase):
    def test_doctor_output_is_cp1252_safe(self):
        cp = subprocess.run(
            [sys.executable, "scripts/leanloop/doctor.py", "--strict"],
            cwd=ROOT,
            env=cp1252_env(),
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn("rough tokens", cp.stdout)

    def test_repomap_output_is_cp1252_safe(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "scripts/leanloop").mkdir(parents=True)
            for name in ("repomap.py", "leanloop_common.py"):
                shutil.copy2(ROOT / "scripts/leanloop" / name, repo / "scripts/leanloop" / name)
            (repo / "src").mkdir()
            (repo / "src/main.py").write_text("def run():\n    pass\n", encoding="utf-8")
            cp = subprocess.run(
                [sys.executable, "scripts/leanloop/repomap.py", "."],
                cwd=repo,
                env=cp1252_env(),
                text=True,
                capture_output=True,
            )
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            self.assertIn("rough tokens", cp.stdout)

    def test_executable_core_sources_are_ascii_only(self):
        paths = list((ROOT / "scripts/leanloop").glob("*.py")) + [ROOT / "scripts/install_tools.sh"]
        offenders = []
        for path in paths:
            text = path.read_text(encoding="utf-8")
            chars = sorted({ch for ch in text if ord(ch) > 127})
            if chars:
                offenders.append(f"{path.relative_to(ROOT)}: {''.join(chars)}")
        self.assertEqual(offenders, [], "non-ASCII executable core: " + "; ".join(offenders))


if __name__ == "__main__":
    unittest.main()
