import random
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from maze import MAX_DIMENSION, MIN_DIMENSION, Maze  # noqa: E402


class MazeGenerationTests(unittest.TestCase):
    def test_generated_dimensions_and_endpoints(self):
        maze = Maze.generate(4, 3, random.Random(2))

        self.assertEqual((maze.width, maze.height), (9, 7))
        self.assertEqual(maze.start, (1, 1))
        self.assertEqual(maze.goal, (7, 5))
        self.assertTrue(maze.is_open(maze.start))
        self.assertTrue(maze.is_open(maze.goal))

    def test_generated_maze_is_connected_and_has_no_cycles(self):
        width, height = 8, 5
        maze = Maze.generate(width, height, random.Random(8))
        open_tiles = maze.open_tiles
        edges = sum(len(maze.neighbors(point)) for point in open_tiles) // 2
        reached = set()
        stack = [maze.start]

        while stack:
            current = stack.pop()
            if current in reached:
                continue
            reached.add(current)
            stack.extend(maze.neighbors(current))

        self.assertEqual(len(open_tiles), 2 * width * height - 1)
        self.assertEqual(len(reached), len(open_tiles))
        self.assertEqual(edges, len(open_tiles) - 1)

    def test_same_seed_generates_same_maze(self):
        self.assertEqual(
            Maze.generate(6, 4, random.Random(12)),
            Maze.generate(6, 4, random.Random(12)),
        )

    def test_largest_supported_maze_is_fully_connected(self):
        maze = Maze.generate(MAX_DIMENSION, MAX_DIMENSION, random.Random(0))

        self.assertEqual(
            (maze.width, maze.height),
            (2 * MAX_DIMENSION + 1, 2 * MAX_DIMENSION + 1),
        )
        self.assertEqual(
            len(maze.open_tiles), 2 * MAX_DIMENSION * MAX_DIMENSION - 1
        )
        self.assertTrue(maze.is_open(maze.goal))

    def test_dimension_validation(self):
        for value in (MIN_DIMENSION - 1, MAX_DIMENSION + 1, 2.5, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Maze.generate(value, 4)

    def test_maze_normalizes_mutable_grid_and_coordinates(self):
        maze = Maze([[False, False]], [0, 0], [1, 0])

        self.assertEqual(maze.grid, ((False, False),))
        self.assertEqual(maze.start, (0, 0))
        self.assertEqual(maze.goal, (1, 0))
        self.assertIsInstance(maze.grid, tuple)
        self.assertIsInstance(maze.start, tuple)

    def test_maze_rejects_ragged_grid_and_wall_endpoint(self):
        with self.assertRaisesRegex(ValueError, "same width"):
            Maze(((False, False), (False,)), (0, 0), (1, 0))
        with self.assertRaisesRegex(ValueError, "open tile"):
            Maze(((True, False),), (0, 0), (1, 0))

    def test_maze_rejects_empty_grid_and_invalid_coordinates(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            Maze((), (0, 0), (0, 0))
        for coordinate in ((0.5, 0), (True, 0), (0,), (0, 0, 0)):
            with self.subTest(coordinate=coordinate):
                with self.assertRaises(ValueError):
                    Maze(((False, False),), coordinate, (1, 0))

    def test_maze_rejects_non_boolean_cells(self):
        with self.assertRaisesRegex(ValueError, "must be booleans"):
            Maze(((0, False),), (0, 0), (1, 0))

    def test_open_tiles_are_listed_in_row_major_order(self):
        maze = Maze(
            (
                (True, True, True),
                (False, False, False),
                (True, True, True),
            ),
            start=(0, 1),
            goal=(2, 1),
        )

        self.assertEqual(maze.open_tiles, ((0, 1), (1, 1), (2, 1)))


if __name__ == "__main__":
    unittest.main()
