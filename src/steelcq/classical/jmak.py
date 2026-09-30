"""Johnson-Mehl-Avrami-Kolmogorov (JMAK) kinetics for diffusional transformations."""

import math
from typing import Optional, Union
import numpy as np


class JMAKModel:
    """Generalized JMAK model supporting both isothermal kinetics and fictitious-time Scheil integration."""

    def __init__(self, avrami_exponent: float = 2.0, rate_constant_prefactor: float = 1e-3) -> None:
        self.n = avrami_exponent
        self.k0 = rate_constant_prefactor

    def isothermal_fraction(self, time_s: Union[float, np.ndarray], rate_constant: float) -> Union[float, np.ndarray]:
        """Compute transformed fraction X(t) = 1 - exp(-k * t^n)."""
        t = np.asarray(time_s)
        arg = rate_constant * (t ** self.n)
        res = 1.0 - np.exp(-arg)
        return float(res) if np.ndim(time_s) == 0 else res

    def step_non_isothermal(self, current_fraction: float, dt_s: float, rate_constant: float) -> float:
        """Compute incremental transformation fraction for non-isothermal cooling step using fictitious time.

        Fictitious time t_fict satisfies:
            current_fraction = 1 - exp(-k * t_fict^n)
            => t_fict = [ -ln(1 - current_fraction) / k ]^(1/n)
        New fraction after dt:
            next_fraction = 1 - exp(-k * (t_fict + dt)^n)
        """
        if current_fraction >= 0.9999 or rate_constant <= 0.0 or dt_s <= 0.0:
            return float(current_fraction)

        eps = 1e-7
        f_clamped = min(max(current_fraction, 0.0), 1.0 - eps)

        # Fictitious time
        inside = -math.log(1.0 - f_clamped) / rate_constant
        t_fict = inside ** (1.0 / self.n)

        # Increment
        t_new = t_fict + dt_s
        new_fraction = 1.0 - math.exp(-rate_constant * (t_new ** self.n))
        return float(np.clip(new_fraction, current_fraction, 1.0))
