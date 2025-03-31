import argparse
from .tui import CellularAutomatonTui


def main():
    parser = argparse.ArgumentParser(description="Conway's Game of Life in the terminal")
    _ = parser.add_argument("--width", type=int, default=20, help="Initial canvas width (default: 20)")
    _ = parser.add_argument("--height", type=int, default=20, help="Initial canvas height (default: 20)")
    _ = parser.add_argument(
        "--speed", type=float, default=0.5, help="Simulation speed - lower is faster (default: 0.5)"
    )
    _ = parser.add_argument("--brush-size", type=int, default=1, help="Initial brush size (default: 1)")
    _ = parser.add_argument("--load", type=str, help="Load a saved game state from file")
    _ = parser.add_argument("--random", action="store_true", help="Start with a random pattern")

    args = parser.parse_args()

    app = CellularAutomatonTui(
        width=args.width,
        height=args.height,
        speed=args.speed,
        brush_size=args.brush_size,
        load_file=args.load,
        random_start=args.random,
    )
    _ = app.run()


if __name__ == "__main__":
    main()
