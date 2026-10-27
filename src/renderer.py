"""Text rendering and animation helpers for terminal mazes."""

from __future__ import annotations

import sys
import time
from typing import TextIO

from maze import Coordinate, Maze
from solver import SearchResult

SPEEDS: dict[str, float | None] = {
    "step": None,
    "slow": 0.20,
    "normal": 0.06,
    "fast": 0.015,
    "instant": 0.0,
}


def render_maze(
    maze: Maze,
    explored: set[Coordinate] | frozenset[Coordinate] = frozenset(),
    path: set[Coordinate] | frozenset[Coordinate] = frozenset(),
) -> str:
    """Render the maze using portable ASCII characters."""
    rows: list[str] = []
    for y, row in enumerate(maze.grid):
        symbols: list[str] = []
        for x, is_wall in enumerate(row):
            point = (x, y)
            if point == maze.start:
                symbol = "S"
            elif point == maze.goal:
                symbol = "E"
            elif is_wall:
                symbol = "#"
            elif point in path:
                symbol = "*"
            elif point in explored:
                symbol = "."
            else:
                symbol = " "
            symbols.append(symbol)
        rows.append("".join(symbols))
    return "\n".join(rows)


class MazeAnimator:
    """Display search progress at a selected speed.

    Intermediate frames are only useful on an interactive terminal, so
    animation is disabled automatically when ``stream`` is not a TTY. This
    keeps piped or redirected output small and avoids blocking on prompts.
    """

    def __init__(
        self,
        maze: Maze,
        speed: str,
        stream: TextIO = sys.stdout,
        input_stream: TextIO = sys.stdin,
    ) -> None:
        if speed not in SPEEDS:
            raise ValueError(f"Unsupported speed: {speed}")
        self.maze = maze
        self.speed = speed
        self.stream = stream
        self.input_stream = input_stream
        self.explored: set[Coordinate] = set()
        self.animated = speed != "instant" and stream_is_interactive(stream)

    def visit(self, coordinate: Coordinate) -> None:
        """Record and display one expanded coordinate."""
        self.explored.add(coordinate)
        if not self.animated:
            return
        self._draw()
        delay = SPEEDS[self.speed]
        if delay is None:
            try:
                self.stream.write("Press Enter to continue...")
                self.stream.flush()
                self.input_stream.readline()
            except (EOFError, OSError, ValueError):
                return
        elif delay > 0:
            time.sleep(delay)

    def finish(self, result: SearchResult) -> None:
        """Display the final route and its cost."""
        self.explored.update(result.explored)
        self._draw(path=set(result.path))
        tiles = tile_summary(len(result.explored))
        if result.path:
            print(
                f"\nRoute found: {result.cost} moves, {tiles}.",
                file=self.stream,
                flush=True,
            )
        else:
            print(
                f"\nNo route found. {tiles}.",
                file=self.stream,
                flush=True,
            )

    def _draw(self, path: set[Coordinate] | None = None, clear: bool = True) -> None:
        if clear and stream_is_interactive(self.stream):
            self.stream.write("\033[2J\033[H")
        print(
            render_maze(self.maze, self.explored, path or frozenset()),
            file=self.stream,
            flush=True,
        )


def stream_is_interactive(stream: TextIO) -> bool:
    """Return whether a stream can display an interactive animation."""
    isatty = getattr(stream, "isatty", None)
    if not callable(isatty):
        return False
    try:
        return bool(isatty())
    except (OSError, ValueError):
        return False


def tile_summary(count: int) -> str:
    noun = "tile" if count == 1 else "tiles"
    return f"{count} {noun} explored"
