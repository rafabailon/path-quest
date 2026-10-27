import random
import sys
import unittest
from collections import deque
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from maze import Maze  # noqa: E402
from solver import a_star  # noqa: E402


def breadth_first_distance(maze: Maze) -> int:
    queue = deque([(maze.start, 0)])
    visited = {maze.start}
    while queue:
        point, distance = queue.popleft()
        if point == maze.goal:
            return distance
        for neighbor in maze.neighbors(point):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    return -1


class AStarTests(unittest.TestCase):
    def test_finds_optimal_path_for_multiple_seeded_mazes(self):
        for seed in range(20):
            with self.subTest(seed=seed):
                maze = Maze.generate(9, 6, random.Random(seed))
                result = a_star(maze)
                self.assertEqual(result.cost, breadth_first_distance(maze))
                self.assertEqual(result.path[0], maze.start)
                self.assertEqual(result.path[-1], maze.goal)
                self.assertTrue(all(maze.is_open(point) for point in result.path))
                self.assertTrue(
                    all(
                        abs(first[0] - second[0]) + abs(first[1] - second[1]) == 1
                        for first, second in zip(result.path, result.path[1:])
                    )
                )

    def test_finds_optimal_path_in_largest_supported_maze(self):
        maze = Maze.generate(50, 50, random.Random(2026))

        result = a_star(maze)

        self.assertEqual(result.cost, breadth_first_distance(maze))
        self.assertEqual(result.path[-1], maze.goal)

    def test_calls_visit_callback_once_for_each_expanded_tile(self):
        maze = Maze.generate(5, 4, random.Random(4))
        visits = []
        result = a_star(maze, visits.append)

        self.assertEqual(tuple(visits), result.explored)
        self.assertEqual(len(visits), len(set(visits)))

    def test_exploration_starts_at_start_without_duplicates(self):
        maze = Maze.generate(6, 5, random.Random(11))

        result = a_star(maze)

        self.assertEqual(result.explored[0], maze.start)
        self.assertEqual(len(result.explored), len(set(result.explored)))

    def test_reports_no_route_when_goal_is_isolated(self):
        maze = Maze(
            ((False, True, False),),
            start=(0, 0),
            goal=(2, 0),
        )

        result = a_star(maze)

        self.assertEqual(result.path, ())
        self.assertEqual(result.cost, -1)
        self.assertEqual(result.explored, (maze.start,))

    def test_start_equal_to_goal_returns_zero_cost_route(self):
        maze = Maze(((False,),), start=(0, 0), goal=(0, 0))

        result = a_star(maze)

        self.assertEqual(result.path, ((0, 0),))
        self.assertEqual(result.cost, 0)


if __name__ == "__main__":
    unittest.main()
