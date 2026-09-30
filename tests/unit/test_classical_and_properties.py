"""Unit tests for classical phase transformation, microstructure, and properties."""

import unittest
from steelcq.materials.loader import get_default_aisi4140
from steelcq.thermodynamics.critical_temperatures import ThermodynamicModel
from steelcq.thermal_history.history import HeatTreatmentSchedule
from steelcq.classical.ttt_cct import TTTModel
from steelcq.classical.jmak import JMAKModel
from steelcq.classical.koistinen_marburger import KoistinenMarburgerModel
from steelcq.classical.tempering_kinetics import TemperingKineticsModel
from steelcq.phase_transformation.engine import PhaseTransformationEngine
from steelcq.microstructure.state import MicrostructureEngine
from steelcq.properties.mechanical import MechanicalPropertyPredictor
from steelcq.properties.thermal import ThermalPropertyPredictor
from steelcq.properties.electrical import ElectricalPropertyPredictor


class TestClassicalAndProperties(unittest.TestCase):
    def setUp(self):
        self.mat = get_default_aisi4140()
        self.thermo = ThermodynamicModel(self.mat)
        self.crit = self.thermo.compute_all()

    def test_jmak_monotonic_growth(self):
        jmak = JMAKModel(avrami_exponent=2.0)
        fracs = [jmak.isothermal_fraction(t, rate_constant=1e-3) for t in [0, 10, 50, 100]]
        self.assertEqual(fracs[0], 0.0)
        self.assertTrue(all(x <= y for x, y in zip(fracs, fracs[1:])))
        self.assertLessEqual(fracs[-1], 1.0)

    def test_km_martensite_formation(self):
        km = KoistinenMarburgerModel(alpha=0.0110)
        # Above Ms -> 0
        self.assertEqual(km.martensite_fraction(350.0, Ms_c=325.0), 0.0)
        # Below Ms -> positive
        f_m = km.martensite_fraction(150.0, Ms_c=325.0)
        self.assertGreater(f_m, 0.8)
        self.assertLessEqual(f_m, 1.0)

    def test_all_five_heat_treatments_phase_conservation(self):
        """Verify sum of phase fractions == 1.0 for all five heat treatments."""
        engine = PhaseTransformationEngine(self.mat, self.crit)

        schedules = [
            HeatTreatmentSchedule.quenching(),
            HeatTreatmentSchedule.normalizing(),
            HeatTreatmentSchedule.annealing(),
            HeatTreatmentSchedule.austempering(),
            HeatTreatmentSchedule.tempering()
        ]

        for sched in schedules:
            th = sched.build_thermal_history(num_points_per_stage=100)
            phases = engine.final_phase_fractions(th)
            total = (
                phases.austenite +
                phases.ferrite +
                phases.pearlite +
                phases.bainite +
                phases.martensite +
                phases.tempered_martensite +
                phases.retained_austenite
            )
            self.assertAlmostEqual(total, 1.0, places=4, msg=f"Phase conservation failed for {sched.treatment_name}")

    def test_property_ranges(self):
        """Verify mechanical, thermal, and electrical property predictions are within physical bounds."""
        engine = PhaseTransformationEngine(self.mat, self.crit)
        micro_engine = MicrostructureEngine(self.mat)
        mech_pred = MechanicalPropertyPredictor(self.mat)
        therm_pred = ThermalPropertyPredictor(self.mat)
        elec_pred = ElectricalPropertyPredictor(self.mat)

        # Quenching -> high hardness, lower CVN
        th_quench = HeatTreatmentSchedule.quenching().build_thermal_history(num_points_per_stage=100)
        micro_q = micro_engine.evaluate_microstructure(th_quench)
        mech_q = mech_pred.predict_all(micro_q)
        therm_q = therm_pred.predict_conductivity(micro_q)
        elec_q = elec_pred.predict_conductivity(micro_q)

        self.assertGreaterEqual(mech_q.hardness_hv, 450.0)
        self.assertGreaterEqual(mech_q.hardness_hrc, 45.0)
        self.assertGreaterEqual(mech_q.uts_mpa, 1400.0)
        self.assertGreater(therm_q.thermal_conductivity_w_m_k, 25.0)
        self.assertGreater(elec_q.electrical_conductivity_s_m, 2.0e6)

        # Tempering -> lower hardness, high CVN
        th_temper = HeatTreatmentSchedule.tempering().build_thermal_history(num_points_per_stage=100)
        micro_t = micro_engine.evaluate_microstructure(th_temper)
        mech_t = mech_pred.predict_all(micro_t, tempering_temp_c=550.0)

        self.assertLess(mech_t.hardness_hv, mech_q.hardness_hv)
        self.assertGreater(mech_t.charpy_toughness_j, mech_q.charpy_toughness_j)


if __name__ == "__main__":
    unittest.main()
