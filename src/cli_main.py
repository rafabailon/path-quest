"""Command-line interface for Path Quest."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Sequence, TextIO

from maze import MAX_DIMENSION, MIN_DIMENSION, Maze
from renderer import (
    MazeAnimator,
    SPEEDS,
    render_maze,
    stream_is_interactive,
    tile_summary,
)
from solver import SearchResult, a_star

DEFAULT_WIDTH = 15
DEFAULT_HEIGHT = 8
__version__ = "1.1.0"


def positive_dimension(value: str) -> int:
    """Parse and validate one maze dimension."""
    try:
        dimension = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a whole number") from error
    if not MIN_DIMENSION <= dimension <= MAX_DIMENSION:
        raise argparse.ArgumentTypeError(
            f"must be between {MIN_DIMENSION} and {MAX_DIMENSION}"
        )
    return dimension


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="path-quest",
        description="Generate a maze and visualize its optimal A* solution.",
    )
    parser.add_argument("--width", type=positive_dimension, help="maze width in cells")
    parser.add_argument(
        "--height", type=positive_dimension, help="maze height in cells"
    )
    parser.add_argument(
        "--speed",
        choices=tuple(SPEEDS),
        help="animation speed (step, slow, normal, fast, or instant)",
    )
    parser.add_argument("--seed", type=int, help="random seed for repeatable mazes")
    parser.add_argument(
        "--export",
        type=Path,
        metavar="FILE",
        help="write the solved maze and its summary to FILE",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Path Quest {__version__}",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> int:
    args = build_parser().parse_args(argv)
    interactive = stream_is_interactive(input_stream)
    width = args.width
    height = args.height
    speed = args.speed

    if width is None:
        if interactive:
            width = prompt_dimension(
                "Width", DEFAULT_WIDTH, input_stream, output_stream
            )
        else:
            width = DEFAULT_WIDTH
    if height is None:
        if interactive:
            height = prompt_dimension(
                "Height", DEFAULT_HEIGHT, input_stream, output_stream
            )
        else:
            height = DEFAULT_HEIGHT
    if speed is None:
        speed = prompt_speed(input_stream, output_stream) if interactive else "instant"

    # Always report the seed that was used, including generated seeds, so every
    # run can be reproduced with --seed.
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**32)
    rng = random.Random(seed)
    maze = Maze.generate(width, height, rng)
    print(
        f"Path Quest | {width} x {height} cells | seed: {seed}",
        file=output_stream,
    )
    print("Searching for the shortest route with A*...", file=output_stream)

    animator = MazeAnimator(maze, speed, output_stream, input_stream)
    result = a_star(maze, animator.visit if animator.animated else None)
    animator.finish(result)

    if args.export is not None:
        if not write_export(args.export, maze, result, seed, output_stream):
            return 2

    return 0 if result.path else 1


def write_export(
    destination: Path,
    maze: Maze,
    result: SearchResult,
    seed: int,
    output_stream: TextIO,
) -> bool:
    """Write the solved maze to ``destination``, reporting any failure."""
    header = (
        f"Path Quest | {maze.width // 2} x {maze.height // 2} cells | seed: {seed}"
    )
    tiles = tile_summary(len(result.explored))
    if result.path:
        summary = f"Route found: {result.cost} moves, {tiles}."
    else:
        summary = f"No route found. {tiles}."
    content = (
        f"{header}\n{summary}\n\n"
        f"{render_maze(maze, set(result.explored), set(result.path))}\n"
    )
    try:
        destination.write_text(content, encoding="utf-8")
    except OSError as error:
        print(
            f"Could not write export file {destination}: {error}",
            file=output_stream,
        )
        return False
    print(f"Saved solved maze to {destination}.", file=output_stream)
    return True


def prompt_dimension(
    label: str,
    default: int,
    input_stream: TextIO,
    output_stream: TextIO,
) -> int:
    """Prompt repeatedly until a dimension is valid."""
    while True:
        output_stream.write(
            f"{label} ({MIN_DIMENSION}-{MAX_DIMENSION}, default {default}): "
        )
        output_stream.flush()
        raw_value = input_stream.readline()
        if raw_value == "":
            raise EOFError(f"Input ended while reading {label.lower()}.")
        value = raw_value.strip()
        if not value:
            return default
        try:
            return positive_dimension(value)
        except argparse.ArgumentTypeError as error:
            print(f"Invalid {label.lower()}: {error}. Try again.", file=output_stream)


def prompt_speed(input_stream: TextIO, output_stream: TextIO) -> str:
    """Prompt for one of the supported animation speeds."""
    choices = ", ".join(SPEEDS)
    while True:
        output_stream.write(f"Animation speed ({choices}, default normal): ")
        output_stream.flush()
        value = input_stream.readline()
        if value == "":
            raise EOFError("Input ended while reading animation speed.")
        speed = value.strip().lower() or "normal"
        if speed in SPEEDS:
            return speed
        print(f"Invalid speed. Choose one of: {choices}.", file=output_stream)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EOFError as error:
        print(f"\n{error}", file=sys.stderr)
        raise SystemExit(2) from error
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        raise SystemExit(130) from None
