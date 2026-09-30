"""Unit tests for material specification, composition balance, and validation."""

import unittest
from steelcq.materials.loader import get_default_aisi4140
from steelcq.materials.schema import SteelMaterial
from steelcq.validation.qc import QualityControlValidator
from steelcq.provenance.record import ValidationStatus


class TestMaterials(unittest.TestCase):
    def setUp(self):
        self.mat = get_default_aisi4140()

    def test_aisi4140_composition_balance(self):
        """Verify composition sum is exactly 100.0 wt%."""
        total = sum(self.mat.composition.values())
        self.assertAlmostEqual(total, 100.0, places=3)

    def test_carbon_content(self):
        """Verify AISI 4140 medium carbon content range."""
        c = self.mat.get_element("C")
        self.assertGreaterEqual(c, 0.38)
        self.assertLessEqual(c, 0.43)

    def test_carbon_equivalent_iiw(self):
        """Verify CE_IIW calculation is physically reasonable (~0.8 to 0.9 for 4140)."""
        ce = self.mat.carbon_equivalent_iiw()
        self.assertGreater(ce, 0.7)
        self.assertLess(ce, 1.1)

    def test_qc_validation(self):
        """Verify pre-simulation QC passes on standard AISI 4140."""
        qc_rep = QualityControlValidator.validate_material(self.mat)
        self.assertTrue(qc_rep.is_valid)

    def test_invalid_negative_element(self):
        """Verify negative concentration raises ValueError."""
        with self.assertRaises(ValueError):
            SteelMaterial(
                name="InvalidSteel",
                composition={"C": -0.1, "Fe": 99.0}
            )


if __name__ == "__main__":
    unittest.main()
