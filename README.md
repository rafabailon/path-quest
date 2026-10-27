# Path Quest

Path Quest is a dependency-free terminal maze generator and visual solver written in Python. It carves a reproducible perfect maze, animates the A* search, and prints the shortest route from the entrance to the exit.

## Features

- Reproducible mazes with `--seed`; generated seeds are always reported
- Optimal A* pathfinding with an admissible Manhattan-distance heuristic
- Five animation modes, from step-by-step to instant
- Automatic frame skipping when output is piped or redirected
- Optional text export of the solved maze and its summary
- Maze sizes from 2 to 50 cells per side with clear validation messages
- Standard-library-only runtime and test suite

## Requirements

- Python 3.10 or later
- No third-party runtime dependencies

## Quick start

From the project root:

```sh
make run
```

Or run the source entry point directly:

```sh
PYTHONPATH=src python3 src/cli_main.py
```

In an interactive terminal, Path Quest prompts for the maze dimensions and animation speed. Press Enter to accept a prompt's default.

When standard input is not a terminal (for example in a script or CI job), the same command uses a 15-by-8 maze and instant output.

## Usage

```sh
PYTHONPATH=src python3 src/cli_main.py --width 20 --height 10 --speed fast --seed 42
```

Available options:

| Option | Description |
| --- | --- |
| `--width N` | Maze width in cells (2-50) |
| `--height N` | Maze height in cells (2-50) |
| `--speed MODE` | `step`, `slow`, `normal`, `fast`, or `instant` |
| `--seed N` | Seed for a repeatable maze |
| `--export FILE` | Write the solved maze and summary to a text file |
| `--version` | Print the Path Quest version |
| `-h`, `--help` | Show command-line help |

When `--seed` is omitted, Path Quest generates a random seed and prints it in the header. Reuse that value to reproduce the exact same maze:

```sh
PYTHONPATH=src python3 src/cli_main.py --width 20 --height 10 --seed 123456789
```

Export a printable copy of the solved maze:

```sh
PYTHONPATH=src python3 src/cli_main.py --width 12 --height 8 --seed 7 --export solved-maze.txt
```

### Install the command

```sh
python3 -m pip install -e .
path-quest --width 20 --height 10 --speed instant --seed 42
```

## Output legend

| Symbol | Meaning |
| --- | --- |
| `#` | Wall |
| `S` | Start |
| `E` | Exit |
| `.` | Tile expanded by A* |
| `*` | Shortest route |

Animation works only when the output stream is an interactive terminal. `step` waits for Enter after each expanded tile; `slow`, `normal`, and `fast` use decreasing delays; `instant` shows only the final frame. If output is redirected, intermediate frames are skipped automatically so the file stays small.

## How it works

The generator uses randomized depth-first search to carve a connected perfect maze: every open cell is reachable and there is exactly one route between any two open cells. Each logical cell is drawn as a 3-by-3 block, so a maze of `width` by `height` cells produces a grid of `2 * width + 1` by `2 * height + 1` characters.

A* explores open tiles with a min-priority queue. Every move costs one, and Manhattan distance estimates the remaining distance to the exit. That heuristic never overestimates the true cost and is consistent for orthogonal movement, so the first route A* returns is optimal. The search also records every expanded tile for the animation.

## Tests

Run the suite with either command:

```sh
make test
python3 -m unittest discover -s tests -v
```

The 40 tests cover:

- Maze dimensions, connectivity, acyclicity, reproducibility, and the largest supported size
- Immutable grid, boolean cell, and coordinate validation
- A* optimality against an independent breadth-first search, including a 50-by-50 maze
- Rendering symbols, route precedence, animation modes, TTY detection, and EOF handling
- CLI parsing, prompts, generated-seed reproducibility, export success and failure, and `--version`

## Project structure

```text
src/
  maze.py       Immutable maze model and procedural generator
  solver.py     A* search and route reconstruction
  renderer.py   ASCII rendering and animation
  cli_main.py   Prompts, command-line options, export, and entry point
tests/
  test_maze.py
  test_solver.py
  test_renderer.py
  test_cli.py
Makefile        Run, test, and clean shortcuts
pyproject.toml  Packaging and console-script metadata
```

The source modules live directly in `src/`; the project intentionally keeps this small layout instead of adding a nested package directory.

## Make targets

```sh
make run    # start the interactive app
make test   # run the unittest suite
make clean  # remove caches and build artifacts
```
