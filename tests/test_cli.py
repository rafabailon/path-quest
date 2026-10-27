import argparse
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC))

SUBPROCESS_ENV = {
    **os.environ,
    "PYTHONPATH": str(SRC),
    "PYTHONDONTWRITEBYTECODE": "1",
}

from cli_main import (  # noqa: E402
    __version__,
    build_parser,
    main,
    positive_dimension,
    prompt_dimension,
    prompt_speed,
)


class FakeTty(io.StringIO):
    """In-memory stream that reports itself as an interactive terminal."""

    def isatty(self) -> bool:
        return True


class CliTests(unittest.TestCase):
    def test_direct_script_runs_and_prints_solution(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SRC / "cli_main.py"),
                "--width",
                "4",
                "--height",
                "3",
                "--seed",
                "7",
                "--speed",
                "instant",
            ],
            cwd=PROJECT_ROOT,
            env=SUBPROCESS_ENV,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Path Quest | 4 x 3 cells | seed: 7", completed.stdout)
        self.assertIn("Route found:", completed.stdout)

    def test_invalid_cli_dimensions_are_rejected(self):
        completed = subprocess.run(
            [sys.executable, str(SRC / "cli_main.py"), "--width", "1"],
            cwd=PROJECT_ROOT,
            env=SUBPROCESS_ENV,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("must be between 2 and 50", completed.stderr)

    def test_version_flag_reports_project_name(self):
        buffer = io.StringIO()

        with self.assertRaises(SystemExit) as raised, redirect_stdout(buffer):
            build_parser().parse_args(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(buffer.getvalue().strip(), f"Path Quest {__version__}")

    def test_dimension_prompt_retries_then_accepts_valid_value(self):
        input_stream = io.StringIO("invalid\n6\n")
        output_stream = io.StringIO()

        result = prompt_dimension("Width", 15, input_stream, output_stream)

        self.assertEqual(result, 6)
        self.assertIn("Invalid width", output_stream.getvalue())

    def test_speed_prompt_retries_then_accepts_valid_value(self):
        input_stream = io.StringIO("warp\nfast\n")
        output_stream = io.StringIO()

        result = prompt_speed(input_stream, output_stream)

        self.assertEqual(result, "fast")
        self.assertIn("Invalid speed", output_stream.getvalue())

    def test_empty_prompts_select_defaults(self):
        self.assertEqual(
            prompt_dimension("Height", 8, io.StringIO("\n"), io.StringIO()),
            8,
        )
        self.assertEqual(prompt_speed(io.StringIO("\n"), io.StringIO()), "normal")

    def test_eof_during_prompt_is_reported(self):
        with self.assertRaisesRegex(EOFError, "Input ended"):
            prompt_dimension("Width", 15, io.StringIO(""), io.StringIO())

    def test_noninteractive_defaults_finish_without_animation(self):
        input_stream = io.StringIO("")
        output_stream = io.StringIO()
        status = main([], input_stream, output_stream)

        self.assertEqual(status, 0)
        self.assertIn("Path Quest | 15 x 8 cells", output_stream.getvalue())
        self.assertIn("seed: ", output_stream.getvalue())
        self.assertIn("Route found:", output_stream.getvalue())

    def test_generated_seed_is_reported_and_reproducible(self):
        first_output = io.StringIO()
        first_status = main(
            ["--width", "4", "--height", "3"],
            io.StringIO(""),
            first_output,
        )
        match = re.search(r"seed: (\d+)", first_output.getvalue())
        self.assertIsNotNone(match)
        self.assertEqual(first_status, 0)

        second_output = io.StringIO()
        second_status = main(
            ["--width", "4", "--height", "3", "--seed", match.group(1)],
            io.StringIO(""),
            second_output,
        )

        self.assertEqual(second_status, 0)
        self.assertEqual(second_output.getvalue(), first_output.getvalue())

    def test_interactive_prompts_accept_defaults(self):
        output_stream = io.StringIO()

        status = main([], FakeTty("\n\n\n"), output_stream)

        self.assertEqual(status, 0)
        output = output_stream.getvalue()
        self.assertIn("Width (2-50, default 15)", output)
        self.assertIn("Height (2-50, default 8)", output)
        self.assertIn("Animation speed", output)
        self.assertIn("Route found:", output)

    def test_export_writes_solved_maze_and_summary(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "maze.txt"
            output_stream = io.StringIO()

            status = main(
                [
                    "--width",
                    "4",
                    "--height",
                    "3",
                    "--seed",
                    "7",
                    "--speed",
                    "instant",
                    "--export",
                    str(destination),
                ],
                io.StringIO(""),
                output_stream,
            )

            self.assertEqual(status, 0)
            self.assertTrue(destination.is_file())
            content = destination.read_text(encoding="utf-8")
            self.assertIn("Path Quest | 4 x 3 cells | seed: 7", content)
            self.assertIn("Route found:", content)
            self.assertIn("S", content)
            self.assertIn("E", content)
            self.assertIn(f"Saved solved maze to {destination}.", output_stream.getvalue())

    def test_export_failure_returns_error_status(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "missing" / "maze.txt"
            output_stream = io.StringIO()

            status = main(
                [
                    "--width",
                    "4",
                    "--height",
                    "3",
                    "--seed",
                    "7",
                    "--export",
                    str(destination),
                ],
                io.StringIO(""),
                output_stream,
            )

            self.assertEqual(status, 2)
            self.assertIn("Could not write export file", output_stream.getvalue())

    def test_positive_dimension_rejects_non_numeric_values(self):
        with self.assertRaisesRegex(argparse.ArgumentTypeError, "whole number"):
            positive_dimension("wide")


if __name__ == "__main__":
    unittest.main()
