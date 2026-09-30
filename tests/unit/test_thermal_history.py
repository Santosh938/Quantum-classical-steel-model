"""Unit tests for ThermalHistory continuous trajectory and derivative evaluation."""

import unittest
import numpy as np
from steelcq.thermal_history.history import ThermalHistory, HeatTreatmentSchedule
from steelcq.validation.qc import QualityControlValidator


class TestThermalHistory(unittest.TestCase):
    def test_spline_interpolation_and_derivatives(self):
        t = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
        # Parabolic cooling: T = 800 - 0.5 * t^2
        T = 800.0 - 0.5 * (t ** 2)
        th = ThermalHistory(time=t, temperature=T, source="test_parabola")

        # Check exact points
        self.assertAlmostEqual(th.temperature_at(0.0), 800.0)
        self.assertAlmostEqual(th.temperature_at(20.0), 600.0)

        # Check derivative: dT/dt at t=10 should be approx -t = -10 degC/s
        deriv_10 = th.derivative_at(10.0)
        self.assertAlmostEqual(deriv_10, -10.0, delta=1.5)

        # Cooling rate is positive
        self.assertGreater(th.cooling_rate_at(10.0), 0.0)

    def test_quenching_schedule_generation(self):
        schedule = HeatTreatmentSchedule.quenching()
        th = schedule.build_thermal_history(num_points_per_stage=100)

        self.assertAlmostEqual(th.max_temperature, 845.0, delta=1.0)
        self.assertLessEqual(th.min_temperature, 35.0)

        qc = QualityControlValidator.validate_thermal_history(th)
        self.assertTrue(qc.is_valid)

    def test_non_monotonic_time_rejected(self):
        with self.assertRaises(ValueError):
            ThermalHistory(
                time=[0.0, 10.0, 5.0, 20.0],
                temperature=[800.0, 700.0, 600.0, 500.0]
            )


if __name__ == "__main__":
    unittest.main()
