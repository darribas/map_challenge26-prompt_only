"""Run by Quarto after each render (see `post-render` in _quarto.yml).

GitHub Pages runs Jekyll on the published folder unless it finds a `.nojekyll` file; Jekyll would skip some of Quarto's
files, so we always leave one in `docs/`.
"""
from pathlib import Path

(Path(__file__).resolve().parents[1] / "docs" / ".nojekyll").touch()
