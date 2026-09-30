"""Unit tests for figure quality checker and DPI enforcement."""

import tempfile
import unittest
from pathlib import Path
import matplotlib.pyplot as plt
from steelcq.visualization.style import apply_publication_style
from steelcq.visualization.exporter import save_publication_figure
from steelcq.validation.figure_checker import FigureQualityChecker


class TestFigureQuality(unittest.TestCase):
    def setUp(self):
        apply_publication_style()

    def test_publication_figure_dpi_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fig, ax = plt.subplots(figsize=(3.4, 2.8))
            ax.plot([0, 1, 2], [10, 20, 15], label="Curve")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Metric (arb. units)")
            ax.legend()

            out_path = Path(tmpdir) / "test_fig_400dpi.png"
            png_p, json_p = save_publication_figure(
                fig=fig,
                filepath=out_path,
                figure_id="FIG_TEST",
                title="Test Publication Figure",
                description="Testing figure export and >= 350 DPI validation",
                dpi=400
            )
            plt.close(fig)

            self.assertTrue(png_p.exists())
            self.assertTrue(json_p.exists())

            # Validate using FigureQualityChecker
            checker = FigureQualityChecker(min_dpi=350)
            res = checker.check_figure(png_p)
            self.assertTrue(res.passed, f"Errors: {res.errors}")
            self.assertEqual(res.metadata.get("dpi"), 400)

    def test_sub_350_dpi_rejected(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        with self.assertRaises(ValueError):
            save_publication_figure(
                fig=fig,
                filepath="dummy.png",
                figure_id="FIG_LOW",
                title="Low DPI",
                description="Should fail",
                dpi=200 # Below 350 DPI
            )
        plt.close(fig)


if __name__ == "__main__":
    unittest.main()
