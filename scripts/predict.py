"""CLI entrypoint for the NBA Props Model daily prediction pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nba_props_model.pipelines.predict import main  # noqa: E402

if __name__ == "__main__":
    main()
