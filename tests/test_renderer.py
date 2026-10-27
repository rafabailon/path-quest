import io
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from maze import Maze  # noqa: E402
from renderer import MazeAnimator, render_maze, tile_summary  # noqa: E402
from solver import SearchResult  # noqa: E402


class FakeTty(io.StringIO):
    """In-memory stream that reports itself as an interactive terminal."""

    def isatty(self) -> bool:
        return True


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.maze = Maze(
            (
                (True, True, True),
                (True, False, True),
                (True, True, True),
            ),
            start=(1, 1),
            goal=(1, 1),
        )

    def test_render_marks_walls_and_endpoints(self):
        maze = Maze(
            (
                (True, True, True),
                (False, False, False),
                (True, True, True),
            ),
            start=(0, 1),
            goal=(2, 1),
        )
        self.assertEqual(render_maze(maze), "###\nS E\n###")

    def test_path_symbol_takes_precedence_over_explored_symbol(self):
        maze = Maze(
            (
                (True, True, True, True, True),
                (True, False, False, False, True),
                (True, True, True, True, True),
            ),
            start=(1, 1),
            goal=(3, 1),
        )
        rendered = render_maze(maze, explored={(2, 1)}, path={(2, 1)})
        self.assertEqual(rendered, "#####\n#S*E#\n#####")

    def test_explored_tiles_are_shown_in_instant_final_frame(self):
        stream = io.StringIO()
        animator = MazeAnimator(self.maze, "instant", stream=stream)
        result = SearchResult(((1, 1),), ((1, 1),))

        animator.finish(result)

        self.assertEqual(animator.explored, {(1, 1)})

    def test_animator_prints_final_route_summary(self):
        stream = io.StringIO()
        animator = MazeAnimator(self.maze, "instant", stream=stream)
        result = SearchResult(((1, 1),), ((1, 1),))

        animator.finish(result)

        self.assertIn("Route found: 0 moves, 1 tile explored.", stream.getvalue())

    def test_animator_reports_when_no_route_exists(self):
        stream = io.StringIO()
        animator = MazeAnimator(self.maze, "instant", stream=stream)
        result = SearchResult((), ((1, 1),))

        animator.finish(result)

        self.assertIn("No route found. 1 tile explored.", stream.getvalue())

    def test_step_mode_waits_for_confirmation(self):
        stream = FakeTty()
        animator = MazeAnimator(
            self.maze,
            "step",
            stream=stream,
            input_stream=io.StringIO("\n"),
        )

        animator.visit((1, 1))

        self.assertIn("Press Enter to continue...", stream.getvalue())
        self.assertIn((1, 1), animator.explored)

    def test_non_tty_stream_disables_intermediate_animation(self):
        stream = io.StringIO()
        animator = MazeAnimator(self.maze, "slow", stream=stream)

        animator.visit((1, 1))

        self.assertFalse(animator.animated)
        self.assertEqual(stream.getvalue(), "")
        self.assertEqual(animator.explored, {(1, 1)})

    def test_tty_final_frame_clears_previous_frames(self):
        stream = FakeTty()
        animator = MazeAnimator(self.maze, "instant", stream=stream)

        animator.finish(SearchResult(((1, 1),), ((1, 1),)))

        self.assertIn("\033[2J\033[H", stream.getvalue())

    def test_step_mode_survives_input_eof(self):
        stream = FakeTty()
        animator = MazeAnimator(
            self.maze,
            "step",
            stream=stream,
            input_stream=io.StringIO(""),
        )

        animator.visit((1, 1))

        self.assertIn((1, 1), animator.explored)

    def test_invalid_speed_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported speed"):
            MazeAnimator(self.maze, "warp")

    def test_tile_summary_uses_singular_and_plural(self):
        self.assertEqual(tile_summary(1), "1 tile explored")
        self.assertEqual(tile_summary(2), "2 tiles explored")


if __name__ == "__main__":
    unittest.main()
