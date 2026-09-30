"""Unit tests for Quantum VQE, circuit rendering, and observable extraction."""

import unittest
from pathlib import Path
from steelcq.visualization.quantum_circuit_plots import generate_all_quantum_figures
from steelcq.validation.figure_checker import FigureQualityChecker


class TestQuantumVQEAndCircuits(unittest.TestCase):
    def test_generate_and_verify_all_quantum_figures(self):
        """Generate and verify Q1-Q7 circuit figures and Figs 18-30 at >=350 DPI."""
        repo_root = Path(__file__).resolve().parents[2]
        figs_dir = repo_root / "figures"
        saved = generate_all_quantum_figures(figs_dir)
        self.assertGreaterEqual(len(saved), 10)

        checker = FigureQualityChecker(min_dpi=350)
        for png_p, json_p in saved:
            res = checker.check_figure(png_p)
            self.assertTrue(res.passed, f"Failed for {png_p.name}: {res.errors}")


if __name__ == "__main__":
    unittest.main()
