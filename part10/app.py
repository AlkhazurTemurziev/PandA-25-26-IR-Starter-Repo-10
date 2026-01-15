#!/usr/bin/env python3
"""
Part 10 starter.

WHAT'S NEW IN PART 10
You will write two classes without detailed instructions! This is a refactoring, we are not adding new functionality.
"""

from typing import List
import time

from .constants import BANNER, HELP
from .models import Sonnet, SearchResult, SearchEngine, Setting
from .file_utilities import load_config, load_sonnets, Configuration


def print_results(
        query: str,
        results: List[SearchResult],
        highlight: bool,
        hl_mode: str,
        query_time_ms: float | None = None,
) -> None:
    total_docs = len(results)
    matched = [r for r in results if r.matches > 0]

    line = f'{len(matched)} out of {total_docs} sonnets contain "{query}".'
    if query_time_ms is not None:
        line += f" Your query took {query_time_ms:.2f}ms."
    print(line)

    for idx, r in enumerate(matched, start=1):
        r.print(idx, highlight, total_docs, hl_mode)


def main() -> None:
    print(BANNER)
    config = load_config()

    # Load sonnets with timing
    start_load = time.time()
    sonnets = load_sonnets()
    load_time = (time.time() - start_load) * 1000
    print(f"Loading sonnets took: {load_time:.3f} [ms]")
    print(f"Loaded {len(sonnets)} sonnets.")

    # ToDo 1: create search engine with sonnets
    engine = SearchEngine(sonnets)

    # ToDo 2: create settings handlers
    # these 3 objects handle the 3 different settings commands
    settings = [
        Setting(":highlight", ["on", "off"], "highlight", "Highlighting"),
        Setting(":search-mode", ["AND", "OR"], "search_mode", "Search mode"),
        Setting(":hl-mode", ["DEFAULT", "GREEN"], "hl_mode", "Highlight mode"),
    ]

    while True:
        raw = ""
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not raw:
            continue

        # commands
        if raw.startswith(":"):
            if raw == ":quit":
                print("Bye.")
                break

            if raw == ":help":
                print(HELP)
                continue

            # try each setting handler
            handled = False
            for setting in settings:
                if setting.try_handle(raw, config):
                    handled = True
                    break

            if handled:
                continue

            print("Unknown command. Type :help for commands.")
            continue

        # ---------- Query evaluation ----------
        if not raw.split():
            continue

        start_query = time.time()

        # ToDo 1: use search engine instead of doing search here
        combined_results = engine.search(raw, config.search_mode)

        elapsed_ms = (time.time() - start_query) * 1000

        print_results(raw, combined_results, config.highlight, config.hl_mode, elapsed_ms)


if __name__ == "__main__":
    main()