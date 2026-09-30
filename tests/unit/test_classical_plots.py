"""Unit tests for figure generation and verification of transformations and properties."""

import unittest
from pathlib import Path
from steelcq.visualization.classical_property_plots import generate_all_classical_and_property_figures
from steelcq.validation.figure_checker import FigureQualityChecker


class TestClassicalPropertyPlots(unittest.TestCase):
    def test_generate_and_verify_all_classical_figures(self):
        repo_root = Path(__file__).resolve().parents[2]
        figs_dir = repo_root / "figures"
        saved = generate_all_classical_and_property_figures(figs_dir)
        self.assertGreaterEqual(len(saved), 7)

        checker = FigureQualityChecker(min_dpi=350)
        for png_p, json_p in saved:
            res = checker.check_figure(png_p)
            self.assertTrue(res.passed, f"Failed for {png_p.name}: {res.errors}")


if __name__ == "__main__":
    unittest.main()
