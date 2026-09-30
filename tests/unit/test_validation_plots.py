"""Unit tests for Advanced Validation, Ablation, Benchmarking, and Architecture figures."""

import unittest
from pathlib import Path
from steelcq.visualization.validation_ablation_benchmarking_plots import generate_all_advanced_figures
from steelcq.reporting.tables import TableGenerator
from steelcq.validation.figure_checker import FigureQualityChecker


class TestAdvancedPlotsAndTables(unittest.TestCase):
    def test_generate_and_verify_all_advanced_figures(self):
        repo_root = Path(__file__).resolve().parents[2]
        figs_dir = repo_root / "figures"
        saved = generate_all_advanced_figures(figs_dir)
        self.assertGreaterEqual(len(saved), 5)

        checker = FigureQualityChecker(min_dpi=350)
        for png_p, json_p in saved:
            res = checker.check_figure(png_p)
            self.assertTrue(res.passed, f"Failed for {png_p.name}: {res.errors}")

    def test_generate_all_tables(self):
        repo_root = Path(__file__).resolve().parents[2]
        tables_dir = repo_root / "results" / "tables"
        tables = TableGenerator.generate_all_tables(tables_dir)
        self.assertEqual(len(tables), 15)
        for t_id, paths in tables.items():
            self.assertTrue(paths["csv"].exists())
            self.assertTrue(paths["tex"].exists())
            self.assertTrue(paths["md"].exists())


if __name__ == "__main__":
    unittest.main()
