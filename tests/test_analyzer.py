from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from backend.analyzer import ProjectAnalyzer


class ProjectAnalyzerTests(unittest.TestCase):
    def test_analysis_counts_files_lines_languages_and_ignored_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "demo"
            root.mkdir()
            (root / "main.py").write_text("print('a')\nprint('b')\n", encoding="utf-8")
            (root / "index.html").write_text("<h1>Hello</h1>", encoding="utf-8")
            (root / "empty.txt").write_text("", encoding="utf-8")
            (root / "binary.bin").write_bytes(b"\x00\x01\x02")

            src = root / "src"
            src.mkdir()
            (src / "app.js").write_text("const x = 1;\n", encoding="utf-8")

            ignored = root / "node_modules"
            ignored.mkdir()
            (ignored / "huge.js").write_text("ignored\n" * 100, encoding="utf-8")

            result = ProjectAnalyzer().analyze(root)

            self.assertEqual(result["summary"]["files"], 5)
            self.assertEqual(result["summary"]["directories"], 1)
            self.assertEqual(result["summary"]["lines"], 4)
            self.assertEqual(result["languages"]["Python"]["lines"], 2)
            self.assertEqual(result["languages"]["JavaScript"]["lines"], 1)
            self.assertEqual(result["languages"]["HTML"]["lines"], 1)
            self.assertNotIn("huge.js", str(result["tree"]))
            self.assertEqual(result["insights"]["empty_files"]["count"], 1)

    def test_structure_depth_and_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "demo"
            deep = root / "a" / "b" / "c"
            deep.mkdir(parents=True)
            (deep / "file.py").write_text("pass\n", encoding="utf-8")
            (root / "empty").mkdir()

            result = ProjectAnalyzer().analyze(root)

            self.assertEqual(result["structure"]["maximum_depth"], 3)
            self.assertEqual(result["structure"]["empty_directories"], 1)
            self.assertIn("empty", result["structure"]["empty_directory_paths"])

    def test_todo_fixme_and_hack_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "demo"
            root.mkdir()
            (root / "main.py").write_text(
                "# TODO: refactor this\n"
                "print('ok')  # FIXME handle failure\n"
                "# HACK temporary workaround\n"
                "# todo lower-case is counted too\n",
                encoding="utf-8",
            )
            (root / "binary.bin").write_bytes(b"\x00TODO\x00FIXME")

            result = ProjectAnalyzer().analyze(root)

            self.assertEqual(result["markers"]["counts"]["TODO"], 2)
            self.assertEqual(result["markers"]["counts"]["FIXME"], 1)
            self.assertEqual(result["markers"]["counts"]["HACK"], 1)
            self.assertEqual(result["markers"]["total"], 4)
            self.assertEqual(result["markers"]["files"], 1)
            self.assertEqual(result["markers"]["items"][0]["path"], "main.py")
            self.assertEqual(result["markers"]["items"][0]["line"], 1)


class DesktopApiSafetyTests(unittest.TestCase):
    def test_desktop_api_does_not_expose_complex_public_state(self) -> None:
        from main import DesktopApi

        api = DesktopApi()
        public_state = {
            name: value
            for name, value in vars(api).items()
            if not name.startswith("_")
        }

        self.assertEqual(public_state, {})


if __name__ == "__main__":
    unittest.main()
