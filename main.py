"""
main.py — Entry point and restart loop.
"""

import random
import sys

import game
import report
import ui


def main() -> None:
    ui.print_banner()
    while True:
        params = ui.prompt_initial_params()
        rng = random.Random()
        result = game.run_mission(params, rng)
        report.print_report(result)
        if not ui.ask_restart():
            break
    ui.print_farewell()
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMision cancelada. Hasta la proxima, capitan.")
        sys.exit(0)
