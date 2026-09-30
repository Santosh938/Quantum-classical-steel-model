"""Koistinen-Marburger displacive athermal martensite transformation model."""

import math
from typing import Union
import numpy as np


class KoistinenMarburgerModel:
    """Athermal martensite formation model below Ms temperature."""

    def __init__(self, alpha: float = 0.0110) -> None:
        """Args:

        alpha: KM rate parameter in 1/K (default 0.0110 1/K for medium-carbon low-alloy steels).
        """
        self.alpha = float(alpha)

    def martensite_fraction(
        self,
        temperature_c: Union[float, np.ndarray],
        Ms_c: float,
        available_austenite: float = 1.0
    ) -> Union[float, np.ndarray]:
        """Compute martensite fraction formed upon cooling to temperature_c.

        f_M = available_austenite * (1 - exp(-alpha * (Ms - T))) for T < Ms
        f_M = 0 for T >= Ms
        """
        def _calc(t: float) -> float:
            if t >= Ms_c or available_austenite <= 0.0:
                return 0.0
            undercooling = Ms_c - t
            return float(available_austenite * (1.0 - math.exp(-self.alpha * undercooling)))

        if isinstance(temperature_c, (list, tuple, np.ndarray)):
            return np.array([_calc(float(t)) for t in temperature_c])
        return _calc(float(temperature_c))
