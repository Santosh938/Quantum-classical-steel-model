"""Austenitization kinetics, continuous austenite fraction, and grain growth."""

import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from pydantic import BaseModel, Field

from ..materials.schema import SteelMaterial
from ..thermodynamics.critical_temperatures import CriticalTemperatures, ThermodynamicModel
from ..provenance.record import ParameterRecord, SourceType, ValidationStatus


class AustenitizationState(BaseModel):
    """Microstructural state of austenite during/after austenitization."""
    temperature_c: float
    austenite_fraction: float = Field(..., ge=0.0, le=1.0)
    grain_size_um: float = Field(..., gt=0.0)
    holding_time_s: float = Field(..., ge=0.0)
    homogenization_index: float = Field(..., ge=0.0, le=1.0, description="0 (segregated) to 1.0 (fully homogenized)")
    provenance_records: Dict[str, ParameterRecord] = Field(default_factory=dict)


class AustenitizationEngine:
    """Simulates continuous formation of austenite upon heating and subsequent isothermal grain growth."""

    def __init__(self, material: SteelMaterial, crit_temps: Optional[CriticalTemperatures] = None) -> None:
        self.material = material
        if crit_temps is None:
            thermo = ThermodynamicModel(material)
            self.crit_temps = thermo.compute_all()
        else:
            self.crit_temps = crit_temps

        # Prior austenite grain growth parameters (Sellars & Whiteman / Beck model)
        # d^m - d0^m = A * t * exp(-Q / (R * T))
        self.m_grain_growth = 2.5 # grain growth exponent
        self.A_grain_growth = 1.5e11 # um^2.5 / s (calibrated for medium-carbon low-alloy steel)
        self.Q_grain_growth = 220.0e3 # J / mol (grain boundary migration activation energy with Cr/Mo solute drag)
        self.R_gas = 8.314462 # J / (mol K)

        # Base chromium diffusion coefficient in austenite for homogenization index
        # D_Cr = D0 * exp(-Q / RT)
        self.D0_Cr = 1.8e-4 # m^2 / s
        self.Q_diff_Cr = 260.0e3 # J / mol
        self.segregation_length_scale_m = 25.0e-6 # 25 um typical dendrite arm / banding spacing

    def austenite_fraction_at_temperature(self, temp_c: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Continuous sigmoid transformation from ferrite/pearlite to austenite between Ac1 and Ac3.

        Model:
            T <= Ac1: f_gamma = 0
            Ac1 < T < Ac3: f_gamma = 1 - exp(-b * ((T - Ac1) / (Ac3 - Ac1))^n)
            T >= Ac3: f_gamma = 1.0
        """
        ac1 = self.crit_temps.Ac1
        ac3 = self.crit_temps.Ac3
        span = max(ac3 - ac1, 1.0)

        def _calc_frac(T: float) -> float:
            if T <= ac1:
                return 0.0
            elif T >= ac3:
                return 1.0
            else:
                theta = (T - ac1) / span
                # b=4.605 gives 99.0% at theta=1.0; n=2.0 captures incubation and sigmoidal acceleration
                f = 1.0 - math.exp(-4.605 * (theta ** 2.2))
                return float(np.clip(f, 0.0, 1.0))

        if isinstance(temp_c, (list, tuple, np.ndarray)):
            return np.array([_calc_frac(float(t)) for t in temp_c])
        return _calc_frac(float(temp_c))

    def predict_grain_growth(
        self,
        holding_temp_c: float,
        holding_time_s: float,
        initial_grain_size_um: Optional[float] = None
    ) -> float:
        """Predict prior austenite grain size (PAGS) in micrometers using Sellars & Whiteman formulation.

        d(t) = [ d0^m + A * t * exp(-Q / (R * T_K)) ]^(1/m)
        """
        d0 = initial_grain_size_um or self.material.initial_grain_size_um
        T_K = holding_temp_c + 273.15

        if holding_time_s <= 0.0 or holding_temp_c < self.crit_temps.Ac1:
            return float(d0)

        growth_term = self.A_grain_growth * holding_time_s * math.exp(-self.Q_grain_growth / (self.R_gas * T_K))
        d_final = (d0 ** self.m_grain_growth + growth_term) ** (1.0 / self.m_grain_growth)

        # Cap at realistic thermodynamic abnormal growth limit (~250 um)
        return float(min(round(d_final, 2), 250.0))

    def predict_homogenization_index(self, holding_temp_c: float, holding_time_s: float) -> float:
        """Estimate alloy homogenization index delta in [0, 1] based on Cr/Mo lattice diffusion.

        delta = 1 - exp(- (pi^2 * D * t) / lambda^2)
        """
        if holding_time_s <= 0.0 or holding_temp_c < self.crit_temps.Ac3:
            return 0.0

        T_K = holding_temp_c + 273.15
        D_cr = self.D0_Cr * math.exp(-self.Q_diff_Cr / (self.R_gas * T_K))
        arg = (math.pi ** 2) * D_cr * holding_time_s / (self.segregation_length_scale_m ** 2)
        homog = 1.0 - math.exp(-arg)
        return float(np.clip(round(homog, 3), 0.0, 1.0))

    def evaluate_state(
        self,
        temperature_c: float,
        holding_time_s: float,
        initial_grain_size_um: Optional[float] = None
    ) -> AustenitizationState:
        """Compute complete AustenitizationState."""
        f_gamma = float(self.austenite_fraction_at_temperature(temperature_c))
        grain_size = self.predict_grain_growth(temperature_c, holding_time_s, initial_grain_size_um)
        homog = self.predict_homogenization_index(temperature_c, holding_time_s)

        rec_grain = ParameterRecord(
            name="prior_austenite_grain_size",
            value=grain_size,
            unit="um",
            source="Sellars & Whiteman (1979) Metal Science; Beck model",
            source_type=SourceType.COMPUTED,
            uncertainty=3.5,
            applicability="Austenitization at 800-1100 degC",
            calibration_status="calibrated_for_low_alloy_steels",
            validation_status=ValidationStatus.VALIDATED,
            provenance_note=f"PAGS after holding at {temperature_c:.1f} degC for {holding_time_s/60.0:.1f} min"
        )

        return AustenitizationState(
            temperature_c=temperature_c,
            austenite_fraction=f_gamma,
            grain_size_um=grain_size,
            holding_time_s=holding_time_s,
            homogenization_index=homog,
            provenance_records={"pags": rec_grain}
        )
