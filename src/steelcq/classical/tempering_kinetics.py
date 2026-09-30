"""Tempering kinetics, Hollomon-Jaffe parameter, and martensite softening."""

import math
from typing import Tuple


class TemperingKineticsModel:
    """Tempering kinetics for conversion of as-quenched martensite into tempered martensite.

    Tracks carbon diffusion from BCT martensite, transition carbide formation (epsilon/eta carbide),
    theta cementite precipitation, and dislocation density recovery.
    """

    def __init__(self, Chj: float = 19.5) -> None:
        """Args:

        Chj: Hollomon-Jaffe material constant for AISI 4140 low-alloy steel (~19.5).
        """
        self.Chj = Chj

    def compute_hollomon_jaffe(self, temp_c: float, hold_time_s: float) -> float:
        """Compute Hollomon-Jaffe tempering parameter:

        HJP = T_K * (C + log10(time_hours))
        """
        if hold_time_s <= 0.0 or temp_c < 100.0:
            return 0.0

        T_K = temp_c + 273.15
        time_hours = max(hold_time_s / 3600.0, 1e-4)
        hjp = T_K * (self.Chj + math.log10(time_hours))
        return float(hjp)

    def fraction_tempered_martensite(self, as_quenched_martensite: float, hjp: float) -> float:
        """Calculate fraction of martensite converted to tempered martensite.

        At HJP < 11000 (room temp or brief low heat), essentially untempered.
        Between 12000 and 15000, stages 1-3 tempering occurs.
        At HJP >= 15000 (e.g. 500-650 °C for 1-2 hours), transformation to tempered martensite is ~100%.
        """
        if as_quenched_martensite <= 0.0 or hjp < 10000.0:
            return 0.0

        # Sigmoidal conversion from untempered to tempered martensite
        mid_hjp = 13500.0
        width = 1200.0
        conversion_ratio = 1.0 / (1.0 + math.exp(-(hjp - mid_hjp) / width))
        return float(as_quenched_martensite * conversion_ratio)
