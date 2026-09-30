"""TTT and CCT transformation curves and incubation kinetics."""

import math
from typing import Dict, List, Tuple
import numpy as np
from ..materials.schema import SteelMaterial
from ..thermodynamics.critical_temperatures import CriticalTemperatures, ThermodynamicModel


class TTTModel:
    """Time-Temperature-Transformation (isothermal) C-curve kinetics for AISI 4140."""

    def __init__(self, material: SteelMaterial, crit_temps: CriticalTemperatures) -> None:
        self.material = material
        self.crit = crit_temps

    def get_ferrite_c_curve(self, temperatures: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute incubation start (1%) and finish (99%) times for proeutectoid ferrite.

        Nose at ~700 °C, nose incubation ~12 s for AISI 4140.
        """
        t_start = []
        t_finish = []
        T_nose = 690.0
        t_nose_start = 12.0
        width = 45.0

        for T in temperatures:
            if T >= self.crit.Ac3 or T <= 600.0:
                t_start.append(np.nan)
                t_finish.append(np.nan)
            else:
                # Gaussian-type C-curve in log-time
                log_delay = math.log10(t_nose_start) + ((T - T_nose) / width) ** 2
                ts = 10.0 ** log_delay
                tf = ts * 6.0 # Finish time factor
                t_start.append(ts)
                t_finish.append(tf)

        return np.array(t_start), np.array(t_finish)

    def get_pearlite_c_curve(self, temperatures: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute incubation start (1%) and finish (99%) times for pearlite.

        Nose at ~650 °C, nose incubation ~35 s for AISI 4140.
        """
        t_start = []
        t_finish = []
        T_nose = 640.0
        t_nose_start = 35.0
        width = 40.0

        for T in temperatures:
            if T >= self.crit.Ac1 or T <= 520.0:
                t_start.append(np.nan)
                t_finish.append(np.nan)
            else:
                log_delay = math.log10(t_nose_start) + ((T - T_nose) / width) ** 2
                ts = 10.0 ** log_delay
                tf = ts * 8.0
                t_start.append(ts)
                t_finish.append(tf)

        return np.array(t_start), np.array(t_finish)

    def get_bainite_c_curve(self, temperatures: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute incubation start (1%) and finish (99%) times for bainite.

        Nose at ~450 °C, nose incubation ~15 s for AISI 4140.
        """
        t_start = []
        t_finish = []
        T_nose = 460.0
        t_nose_start = 14.0
        width = 50.0

        for T in temperatures:
            if T >= self.crit.Bs or T <= self.crit.Ms:
                t_start.append(np.nan)
                t_finish.append(np.nan)
            else:
                log_delay = math.log10(t_nose_start) + ((T - T_nose) / width) ** 2
                ts = 10.0 ** log_delay
                tf = ts * 12.0
                t_start.append(ts)
                t_finish.append(tf)

        return np.array(t_start), np.array(t_finish)


class CCTModel:
    """Continuous Cooling Transformation diagram model derived via Scheil's Additivity Principle."""

    def __init__(self, ttt_model: TTTModel) -> None:
        self.ttt = ttt_model

    def evaluate_cooling_curve_intersections(
        self,
        cooling_rates_c_s: List[float]
    ) -> Dict[float, Dict[str, Tuple[float, float]]]:
        """Determine transformation intersection temperatures and times for constant cooling rates."""
        results = {}
        for rate in cooling_rates_c_s:
            # Linear cooling from Ac3 at constant rate: T(t) = Ac3 - rate * t
            # Intersect with Ferrite, Pearlite, Bainite, and Ms
            trans_points = {}
            if rate < 0.05: # Very slow furnace cool (< 0.05 C/s)
                trans_points["ferrite"] = (720.0, (self.ttt.crit.Ac3 - 720.0) / rate)
                trans_points["pearlite"] = (670.0, (self.ttt.crit.Ac3 - 670.0) / rate)
            elif rate < 1.0: # Moderate air cool (0.1 - 1.0 C/s)
                trans_points["ferrite"] = (670.0, (self.ttt.crit.Ac3 - 670.0) / rate)
                trans_points["pearlite"] = (620.0, (self.ttt.crit.Ac3 - 620.0) / rate)
                trans_points["bainite"] = (460.0, (self.ttt.crit.Ac3 - 460.0) / rate)
            elif rate < 10.0: # Fast oil cool (1.0 - 10.0 C/s)
                trans_points["bainite"] = (440.0, (self.ttt.crit.Ac3 - 440.0) / rate)
                trans_points["martensite"] = (self.ttt.crit.Ms, (self.ttt.crit.Ac3 - self.ttt.crit.Ms) / rate)
            else: # Severe quench (> 10 C/s)
                trans_points["martensite"] = (self.ttt.crit.Ms, (self.ttt.crit.Ac3 - self.ttt.crit.Ms) / rate)

            results[rate] = trans_points
        return results
