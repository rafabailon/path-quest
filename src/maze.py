"""Maze model and procedural perfect-maze generation."""

from __future__ import annotations

from dataclasses import dataclass
import random

Coordinate = tuple[int, int]

MIN_DIMENSION = 2
MAX_DIMENSION = 50


@dataclass(frozen=True)
class Maze:
    """An immutable maze represented as a grid of walls and open tiles."""

    grid: tuple[tuple[bool, ...], ...]
    start: Coordinate
    goal: Coordinate

    def __post_init__(self) -> None:
        if not self.grid or not self.grid[0]:
            raise ValueError("Maze grid must not be empty.")
        # Store immutable copies so callers cannot mutate a frozen maze later.
        grid = tuple(tuple(row) for row in self.grid)
        object.__setattr__(self, "grid", grid)
        if any(not isinstance(cell, bool) for row in grid for cell in row):
            raise ValueError("Maze grid values must be booleans.")
        width = len(grid[0])
        if any(len(row) != width for row in grid):
            raise ValueError("Maze rows must all have the same width.")
        height = len(grid)
        for name, coordinate in (("start", self.start), ("goal", self.goal)):
            try:
                x, y = coordinate
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Maze {name} must have exactly two coordinates."
                ) from error
            if (
                isinstance(x, bool)
                or isinstance(y, bool)
                or not isinstance(x, int)
                or not isinstance(y, int)
            ):
                raise ValueError(f"Maze {name} coordinates must be integers.")
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError(f"Maze {name} must be inside the grid.")
            if grid[y][x]:
                raise ValueError(f"Maze {name} must be on an open tile.")
            object.__setattr__(self, name, (x, y))

    @property
    def width(self) -> int:
        return len(self.grid[0])

    @property
    def height(self) -> int:
        return len(self.grid)

    @property
    def open_tiles(self) -> tuple[Coordinate, ...]:
        """Return every traversable coordinate in row-major order."""
        return tuple(
            (x, y)
            for y, row in enumerate(self.grid)
            for x, is_wall in enumerate(row)
            if not is_wall
        )

    def is_open(self, coordinate: Coordinate) -> bool:
        """Return whether a coordinate is inside the maze and not a wall."""
        x, y = coordinate
        return 0 <= x < self.width and 0 <= y < self.height and not self.grid[y][x]

    def neighbors(self, coordinate: Coordinate) -> tuple[Coordinate, ...]:
        """Return open orthogonal neighbors in a stable order."""
        x, y = coordinate
        candidates = ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y))
        return tuple(point for point in candidates if self.is_open(point))

    @classmethod
    def generate(
        cls,
        width: int,
        height: int,
        rng: random.Random | None = None,
    ) -> Maze:
        """Generate a connected maze using randomized depth-first search.

        Width and height count maze cells, not wall tiles. The resulting
        drawable grid is therefore ``2 * width + 1`` by ``2 * height + 1``.
        """
        _validate_dimension(width, "width")
        _validate_dimension(height, "height")
        generator = rng if rng is not None else random.Random()

        grid_width = 2 * width + 1
        grid_height = 2 * height + 1
        grid = [[True] * grid_width for _ in range(grid_height)]
        start_cell = (0, 0)
        visited = {start_cell}
        stack = [start_cell]
        grid[1][1] = False

        while stack:
            cell_x, cell_y = stack[-1]
            unvisited = [
                (cell_x + dx, cell_y + dy)
                for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))
                if 0 <= cell_x + dx < width
                and 0 <= cell_y + dy < height
                and (cell_x + dx, cell_y + dy) not in visited
            ]
            if not unvisited:
                stack.pop()
                continue

            next_x, next_y = generator.choice(unvisited)
            visited.add((next_x, next_y))
            grid[2 * next_y + 1][2 * next_x + 1] = False
            grid[cell_y + next_y + 1][cell_x + next_x + 1] = False
            stack.append((next_x, next_y))

        return cls(
            tuple(tuple(row) for row in grid),
            start=(1, 1),
            goal=(grid_width - 2, grid_height - 2),
        )


def _validate_dimension(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Maze {name} must be an integer.")
    if not MIN_DIMENSION <= value <= MAX_DIMENSION:
        raise ValueError(
            f"Maze {name} must be between {MIN_DIMENSION} and {MAX_DIMENSION}."
        )
