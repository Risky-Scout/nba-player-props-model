#!/usr/bin/env python3
from sgp_engine.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["build-nba-bundle"] + __import__("sys").argv[1:]))
