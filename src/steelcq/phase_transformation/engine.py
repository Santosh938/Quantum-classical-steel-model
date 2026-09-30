"""Continuous phase transformation engine tracking microstructural phase fractions."""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, model_validator

from ..materials.schema import SteelMaterial
from ..thermodynamics.critical_temperatures import CriticalTemperatures, ThermodynamicModel
from ..thermal_history.history import ThermalHistory
from ..classical.koistinen_marburger import KoistinenMarburgerModel
from ..classical.tempering_kinetics import TemperingKineticsModel


class PhaseFractions(BaseModel):
    """Normalized phase fractions satisfying sum(f_i) == 1.0 within numerical tolerance."""
    austenite: float = Field(default=0.0, ge=0.0, le=1.0)
    ferrite: float = Field(default=0.0, ge=0.0, le=1.0)
    pearlite: float = Field(default=0.0, ge=0.0, le=1.0)
    bainite: float = Field(default=0.0, ge=0.0, le=1.0)
    martensite: float = Field(default=0.0, ge=0.0, le=1.0)
    tempered_martensite: float = Field(default=0.0, ge=0.0, le=1.0)
    retained_austenite: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_sum_unity(self) -> "PhaseFractions":
        total = (
            self.austenite +
            self.ferrite +
            self.pearlite +
            self.bainite +
            self.martensite +
            self.tempered_martensite +
            self.retained_austenite
        )
        if abs(total - 1.0) > 1e-3:
            # Re-normalize automatically to strictly ensure unity
            if total > 0.0:
                self.austenite /= total
                self.ferrite /= total
                self.pearlite /= total
                self.bainite /= total
                self.martensite /= total
                self.tempered_martensite /= total
                self.retained_austenite /= total
        return self

    def as_dict(self) -> Dict[str, float]:
        return {
            "austenite": self.austenite,
            "ferrite": self.ferrite,
            "pearlite": self.pearlite,
            "bainite": self.bainite,
            "martensite": self.martensite,
            "tempered_martensite": self.tempered_martensite,
            "retained_austenite": self.retained_austenite
        }


class PhaseTransformationEngine:
    """Rigorous kinetic phase transformation engine coupled to continuous ThermalHistory."""

    def __init__(self, material: SteelMaterial, crit_temps: Optional[CriticalTemperatures] = None) -> None:
        self.material = material
        self.crit = crit_temps or ThermodynamicModel(material).compute_all()
        self.km_model = KoistinenMarburgerModel(alpha=0.0110)
        self.temper_model = TemperingKineticsModel(Chj=19.5)

    def simulate(self, history: ThermalHistory) -> pd.DataFrame:
        """Simulate phase fraction evolution along continuous thermal history T(t).

        Returns DataFrame with columns:
        [time_s, temperature_c, austenite, ferrite, pearlite, bainite, martensite, tempered_martensite, retained_austenite]
        """
        times = history.time
        temps = history.temperature
        n_steps = len(times)

        # Output arrays
        f_gamma = np.zeros(n_steps)
        f_alpha = np.zeros(n_steps)
        f_pearl = np.zeros(n_steps)
        f_bain = np.zeros(n_steps)
        f_mart = np.zeros(n_steps)
        f_temp_mart = np.zeros(n_steps)
        f_ret_aust = np.zeros(n_steps)

        # Initial state at t=0 (as-received hot-rolled 4140: ~20% ferrite, 80% pearlite)
        f_alpha[0] = 0.20
        f_pearl[0] = 0.80

        # State tracking flags
        has_reached_austenite = False
        cooling_started = False
        peak_temp_seen = temps[0]
        reheating_for_temper = False
        quench_completed = False
        temper_soak_accum_s = 0.0

        for i in range(1, n_steps):
            t_curr = times[i]
            dt = times[i] - times[i-1]
            T_curr = temps[i]
            T_prev = temps[i-1]

            # Carry forward previous state by default
            f_gamma[i] = f_gamma[i-1]
            f_alpha[i] = f_alpha[i-1]
            f_pearl[i] = f_pearl[i-1]
            f_bain[i] = f_bain[i-1]
            f_mart[i] = f_mart[i-1]
            f_temp_mart[i] = f_temp_mart[i-1]
            f_ret_aust[i] = f_ret_aust[i-1]

            if T_curr > peak_temp_seen:
                peak_temp_seen = T_curr

            # 1. HEATING / AUSTENITIZATION BRANCH
            if not cooling_started and T_curr >= self.crit.Ac1:
                # Progressive dissolution of ferrite/pearlite into austenite
                if T_curr >= self.crit.Ac3:
                    f_gamma[i] = 1.0
                    f_alpha[i] = 0.0
                    f_pearl[i] = 0.0
                    f_bain[i] = 0.0
                    f_mart[i] = 0.0
                    f_temp_mart[i] = 0.0
                    f_ret_aust[i] = 0.0
                    has_reached_austenite = True
                else:
                    theta = (T_curr - self.crit.Ac1) / max(self.crit.Ac3 - self.crit.Ac1, 1.0)
                    dissolved = float(np.clip(1.0 - np.exp(-4.605 * (theta ** 2.2)), 0.0, 1.0))
                    f_gamma[i] = dissolved
                    rem = 1.0 - dissolved
                    f_alpha[i] = rem * 0.20
                    f_pearl[i] = rem * 0.80

            # Detect cooling onset from austenitization
            if has_reached_austenite and T_curr < (peak_temp_seen - 20.0):
                cooling_started = True

            # 2. COOLING BRANCH FROM AUSTENITE
            if cooling_started and not quench_completed:
                # Calculate instantaneous cooling rate
                rate = (T_prev - T_curr) / max(dt, 1e-4)

                # Case A: Slow cooling (Ferrite & Pearlite formation, Annealing / Normalizing)
                if rate < 2.0 and T_curr < self.crit.Ac1 and T_curr > self.crit.Bs:
                    # Ferrite formation between Ac3 and ~680 C
                    if T_curr >= 680.0 and f_gamma[i] > 0.0:
                        inc_rate = 0.0003 * dt * (1.0 / max(rate, 0.01))
                        df_alpha = min(f_gamma[i] * inc_rate, 0.22 - f_alpha[i])
                        if df_alpha > 0:
                            f_alpha[i] += df_alpha
                            f_gamma[i] -= df_alpha

                    # Pearlite formation between 680 and 550 C
                    if T_curr < 680.0 and f_gamma[i] > 0.0:
                        inc_rate = 0.0015 * dt * (1.0 / max(rate, 0.01))
                        df_pearl = min(f_gamma[i] * inc_rate, f_gamma[i])
                        f_pearl[i] += df_pearl
                        f_gamma[i] -= df_pearl

                # Case B: Isothermal holding in Bainite bay (Austempering, ~300 - 450 C)
                if self.crit.Ms <= T_curr <= self.crit.Bs:
                    # If temperature is held relatively constant (< 0.1 C/s rate)
                    if abs(rate) < 0.1 and f_gamma[i] > 0.0:
                        # JMAK bainite transformation rate: k ~ 0.0008 1/s
                        bainite_rate = 0.0008 * dt
                        df_bain = min(f_gamma[i] * bainite_rate, f_gamma[i])
                        f_bain[i] += df_bain
                        f_gamma[i] -= df_bain

                # Case C: Displacive Martensitic Transformation (T < Ms)
                if T_curr < self.crit.Ms:
                    # Available untransformed austenite entering martensite zone
                    parent_austenite = f_gamma[i] + f_ret_aust[i] + f_mart[i]
                    if parent_austenite > 0.001:
                        target_mart = self.km_model.martensite_fraction(T_curr, self.crit.Ms, parent_austenite)
                        target_mart = min(target_mart, parent_austenite * 0.94) # max 94% martensite (6% retained austenite)
                        f_mart[i] = target_mart
                        f_ret_aust[i] = max(parent_austenite - target_mart, 0.0)
                        f_gamma[i] = 0.0

                # Detect if quench reached room temperature (< 80 C)
                if T_curr < 80.0 and (f_mart[i] > 0.5 or (f_alpha[i] + f_pearl[i] + f_bain[i]) > 0.8):
                    quench_completed = True

            # 3. REHEATING & TEMPERING BRANCH
            if quench_completed and T_curr > 150.0:
                reheating_for_temper = True
                if abs(T_curr - T_prev) / max(dt, 1e-4) < 0.05 and T_curr >= 250.0:
                    temper_soak_accum_s += dt

                # Conversion of as-quenched martensite into tempered martensite
                hjp = self.temper_model.compute_hollomon_jaffe(T_curr, temper_soak_accum_s)
                if f_mart[i] > 0.0 and hjp > 11000.0:
                    converted = self.temper_model.fraction_tempered_martensite(f_mart[i] + f_temp_mart[i], hjp)
                    f_temp_mart[i] = converted
                    f_mart[i] = max((f_mart[i] + f_temp_mart[i]) - converted, 0.0)

            # Strict normalization to unity
            sum_phases = f_gamma[i] + f_alpha[i] + f_pearl[i] + f_bain[i] + f_mart[i] + f_temp_mart[i] + f_ret_aust[i]
            if sum_phases > 0:
                f_gamma[i] /= sum_phases
                f_alpha[i] /= sum_phases
                f_pearl[i] /= sum_phases
                f_bain[i] /= sum_phases
                f_mart[i] /= sum_phases
                f_temp_mart[i] /= sum_phases
                f_ret_aust[i] /= sum_phases

        df_out = pd.DataFrame({
            "time_s": times,
            "temperature_c": temps,
            "austenite": f_gamma,
            "ferrite": f_alpha,
            "pearlite": f_pearl,
            "bainite": f_bain,
            "martensite": f_mart,
            "tempered_martensite": f_temp_mart,
            "retained_austenite": f_ret_aust
        })
        return df_out

    def final_phase_fractions(self, history: ThermalHistory) -> PhaseFractions:
        """Extract final end-of-treatment phase fractions."""
        df = self.simulate(history)
        last_row = df.iloc[-1]
        return PhaseFractions(
            austenite=float(last_row["austenite"]),
            ferrite=float(last_row["ferrite"]),
            pearlite=float(last_row["pearlite"]),
            bainite=float(last_row["bainite"]),
            martensite=float(last_row["martensite"]),
            tempered_martensite=float(last_row["tempered_martensite"]),
            retained_austenite=float(last_row["retained_austenite"])
        )
