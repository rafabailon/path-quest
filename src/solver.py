"""A* pathfinding for maze grids."""

from __future__ import annotations

from dataclasses import dataclass
import heapq
from itertools import count
from typing import Callable

from maze import Coordinate, Maze

VisitCallback = Callable[[Coordinate], None]


@dataclass(frozen=True)
class SearchResult:
    """The shortest route and the order in which A* expanded coordinates."""

    path: tuple[Coordinate, ...]
    explored: tuple[Coordinate, ...]

    @property
    def cost(self) -> int:
        """Return route length in moves, or -1 when no route exists."""
        return len(self.path) - 1 if self.path else -1


def a_star(
    maze: Maze,
    on_visit: VisitCallback | None = None,
) -> SearchResult:
    """Find an optimal route using A* and Manhattan distance.

    Every move has unit cost. Manhattan distance is admissible and consistent
    for orthogonal movement, so the first expanded goal has optimal cost.
    """
    frontier: list[tuple[int, int, Coordinate]] = []
    sequence = count()
    heapq.heappush(
        frontier,
        (_heuristic(maze.start, maze.goal), next(sequence), maze.start),
    )
    came_from: dict[Coordinate, Coordinate] = {}
    cost_so_far = {maze.start: 0}
    explored: list[Coordinate] = []
    expanded: set[Coordinate] = set()

    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current in expanded:
            continue
        expanded.add(current)
        explored.append(current)
        if on_visit is not None:
            on_visit(current)

        if current == maze.goal:
            return SearchResult(_reconstruct_path(came_from, current), tuple(explored))

        for neighbor in maze.neighbors(current):
            new_cost = cost_so_far[current] + 1
            if new_cost >= cost_so_far.get(neighbor, float("inf")):
                continue
            cost_so_far[neighbor] = new_cost
            came_from[neighbor] = current
            priority = new_cost + _heuristic(neighbor, maze.goal)
            heapq.heappush(frontier, (priority, next(sequence), neighbor))

    return SearchResult((), tuple(explored))


def _heuristic(first: Coordinate, second: Coordinate) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _reconstruct_path(
    came_from: dict[Coordinate, Coordinate],
    current: Coordinate,
) -> tuple[Coordinate, ...]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return tuple(path)
