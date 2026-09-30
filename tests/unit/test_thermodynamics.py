"""Unit tests for thermodynamic model and austenitization kinetics."""

import unittest
from pathlib import Path
from steelcq.materials.loader import get_default_aisi4140
from steelcq.thermodynamics.critical_temperatures import ThermodynamicModel
from steelcq.austenitization.kinetics import AustenitizationEngine
from steelcq.visualization.thermo_austenitization_plots import generate_all_thermo_and_thermal_figures
from steelcq.validation.figure_checker import FigureQualityChecker


class TestThermodynamicsAndAustenitization(unittest.TestCase):
    def setUp(self):
        self.mat = get_default_aisi4140()
        self.thermo = ThermodynamicModel(self.mat)
        self.crit = self.thermo.compute_all()
        self.aust = AustenitizationEngine(self.mat, self.crit)

    def test_critical_temperatures_bounds(self):
        """Ensure critical temperatures for AISI 4140 are in standard literature ranges."""
        # Ac1 between 720 and 760 C
        self.assertGreaterEqual(self.crit.Ac1, 720.0)
        self.assertLessEqual(self.crit.Ac1, 760.0)

        # Ac3 between 770 and 820 C
        self.assertGreater(self.crit.Ac3, self.crit.Ac1)
        self.assertLessEqual(self.crit.Ac3, 820.0)

        # Ms between 300 and 350 C
        self.assertGreaterEqual(self.crit.Ms, 300.0)
        self.assertLessEqual(self.crit.Ms, 350.0)

        # Bs between 500 and 580 C
        self.assertGreaterEqual(self.crit.Bs, 500.0)
        self.assertLessEqual(self.crit.Bs, 580.0)

    def test_austenite_fraction_monotonicity(self):
        """Verify austenite formation starts at Ac1 and completes at Ac3."""
        self.assertEqual(self.aust.austenite_fraction_at_temperature(self.crit.Ac1 - 10.0), 0.0)
        self.assertEqual(self.aust.austenite_fraction_at_temperature(self.crit.Ac3 + 10.0), 1.0)
        # Midpoint fraction should be strictly between 0 and 1
        mid_T = 0.5 * (self.crit.Ac1 + self.crit.Ac3)
        mid_frac = self.aust.austenite_fraction_at_temperature(mid_T)
        self.assertGreater(mid_frac, 0.0)
        self.assertLess(mid_frac, 1.0)

    def test_grain_growth_kinetics(self):
        """Grain size must increase with temperature and time."""
        d_short = self.aust.predict_grain_growth(845.0, 600.0)
        d_long = self.aust.predict_grain_growth(845.0, 7200.0)
        d_hot = self.aust.predict_grain_growth(1050.0, 600.0)

        self.assertGreater(d_long, d_short)
        self.assertGreater(d_hot, d_short)

    def test_generate_and_verify_figures(self):
        """Generate figures 2-12 and verify that every figure passes >=350 DPI and quality checks."""
        repo_root = Path(__file__).resolve().parents[2]
        figs_dir = repo_root / "figures"
        saved = generate_all_thermo_and_thermal_figures(figs_dir)
        self.assertGreaterEqual(len(saved), 10)

        checker = FigureQualityChecker(min_dpi=350)
        for png_p, json_p in saved:
            res = checker.check_figure(png_p)
            self.assertTrue(res.passed, f"Failed for {png_p.name}: {res.errors}")


if __name__ == "__main__":
    unittest.main()
