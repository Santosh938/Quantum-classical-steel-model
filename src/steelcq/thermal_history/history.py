"""Thermal history and heat treatment schedule engine."""

from typing import List, Optional, Union
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from pydantic import BaseModel, Field


class HeatTreatmentStage(BaseModel):
    """Specification of an individual stage in a heat-treatment schedule."""
    name: str = Field(..., description="Stage name (e.g. 'heating', 'austenitization_hold', 'quenching')")
    start_temp_c: float = Field(..., description="Initial temperature in degC")
    target_temp_c: float = Field(..., description="Target end temperature in degC")
    duration_s: float = Field(..., gt=0.0, description="Stage duration in seconds")
    regime: str = Field(default="linear", description="'linear', 'exponential', 'isothermal', or 'newtonian'")
    cooling_rate_nominal_c_s: Optional[float] = Field(default=None, description="Nominal cooling rate in degC/s if constant")


class ThermalHistory:
    """Continuous temperature trajectory and cooling-rate evaluation engine."""

    def __init__(
        self,
        time: Union[List[float], np.ndarray],
        temperature: Union[List[float], np.ndarray],
        source: str = "analytical_model",
        uncertainty: Optional[float] = 2.0,
        metadata: Optional[dict] = None
    ) -> None:
        self.time = np.asarray(time, dtype=np.float64)
        self.temperature = np.asarray(temperature, dtype=np.float64)
        self.source = str(source)
        self.uncertainty = float(uncertainty) if uncertainty is not None else None
        self.metadata = metadata or {}

        # Validation
        if len(self.time) != len(self.temperature):
            raise ValueError(f"Time length ({len(self.time)}) must match temperature length ({len(self.temperature)}).")
        if len(self.time) < 2:
            raise ValueError("ThermalHistory requires at least two data points.")
        if not np.all(np.diff(self.time) > 0):
            raise ValueError("Time array must be strictly monotonically increasing.")

        # Fit C2 continuous cubic spline
        self._spline = CubicSpline(self.time, self.temperature, bc_type="natural")
        self._spline_deriv = self._spline.derivative(nu=1)

    def temperature_at(self, t: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Evaluate temperature T(t) in degC."""
        t_arr = np.asarray(t)
        # Handle scalar or array
        res = self._spline(t_arr)
        return float(res) if np.ndim(t) == 0 else res

    def derivative_at(self, t: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Evaluate dT/dt in degC/s."""
        t_arr = np.asarray(t)
        res = self._spline_deriv(t_arr)
        return float(res) if np.ndim(t) == 0 else res

    def cooling_rate_at(self, t: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Evaluate cooling rate -dT/dt in degC/s (positive when cooling)."""
        return -self.derivative_at(t)

    @property
    def total_duration_s(self) -> float:
        return float(self.time[-1] - self.time[0])

    @property
    def max_temperature(self) -> float:
        return float(np.max(self.temperature))

    @property
    def min_temperature(self) -> float:
        return float(np.min(self.temperature))

    def get_t8_5(self) -> Optional[float]:
        """Compute time in seconds to cool from 800 degC to 500 degC (standard t8/5 cooling time)."""
        peak_idx = int(np.argmax(self.temperature))
        cool_time = self.time[peak_idx:]
        cool_temp = self.temperature[peak_idx:]

        if np.max(cool_temp) < 800.0 or np.min(cool_temp) > 500.0:
            return None

        # Dense evaluation along cooling branch
        dense_t = np.linspace(cool_time[0], cool_time[-1], 2000)
        dense_T = self.temperature_at(dense_t)

        t_800_idx = np.where(dense_T <= 800.0)[0]
        t_500_idx = np.where(dense_T <= 500.0)[0]

        if len(t_800_idx) == 0 or len(t_500_idx) == 0:
            return None

        t_800 = dense_t[t_800_idx[0]]
        t_500 = dense_t[t_500_idx[0]]
        return float(t_500 - t_800)

    def to_dataframe(self) -> pd.DataFrame:
        """Export discrete time, temperature, and derivative as pandas DataFrame."""
        return pd.DataFrame({
            "time_s": self.time,
            "temperature_c": self.temperature,
            "dT_dt_c_s": self.derivative_at(self.time)
        })

    def save_csv(self, filepath: Union[str, Path]) -> None:
        """Save thermal history to CSV file."""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False)

    @classmethod
    def from_csv(cls, filepath: Union[str, Path], source: Optional[str] = None, uncertainty: float = 2.0) -> "ThermalHistory":
        """Load thermal history from CSV file."""
        df = pd.read_csv(filepath)
        time_col = [c for c in df.columns if "time" in c.lower()][0]
        temp_col = [c for c in df.columns if "temp" in c.lower()][0]
        return cls(
            time=df[time_col].values,
            temperature=df[temp_col].values,
            source=source or f"csv:{Path(filepath).name}",
            uncertainty=uncertainty
        )


class HeatTreatmentSchedule(BaseModel):
    """Structured heat-treatment schedule generator with multi-stage physics."""

    treatment_name: str = Field(..., description="Quenching, Normalizing, Annealing, Austempering, or Tempering")
    material_name: str = Field(default="AISI 4140")
    stages: List[HeatTreatmentStage] = Field(default_factory=list)

    def build_thermal_history(self, num_points_per_stage: int = 150) -> ThermalHistory:
        """Synthesize continuous ThermalHistory from scheduled stages."""
        time_segments = []
        temp_segments = []
        current_time = 0.0

        for stage in self.stages:
            dt = stage.duration_s
            t_local = np.linspace(0.0, dt, num_points_per_stage)

            if stage.regime == "isothermal":
                T_local = np.full_like(t_local, stage.start_temp_c)
            elif stage.regime == "linear":
                T_local = np.linspace(stage.start_temp_c, stage.target_temp_c, num_points_per_stage)
            elif stage.regime == "exponential" or stage.regime == "newtonian":
                # T(t) = T_ambient + (T_0 - T_ambient) * exp(-k * t)
                t_ambient = stage.target_temp_c
                t_init = stage.start_temp_c
                # Choose decay rate k so that at dt, (T - t_ambient)/(t_init - t_ambient) ~ 0.01 (99% decay)
                k_decay = 4.605 / max(dt, 1e-3)
                T_local = t_ambient + (t_init - t_ambient) * np.exp(-k_decay * t_local)
            else:
                T_local = np.linspace(stage.start_temp_c, stage.target_temp_c, num_points_per_stage)

            if len(time_segments) > 0:
                # Omit first point to avoid duplicate timestamps
                time_segments.append(current_time + t_local[1:])
                temp_segments.append(T_local[1:])
            else:
                time_segments.append(t_local)
                temp_segments.append(T_local)

            current_time += dt

        full_time = np.concatenate(time_segments)
        full_temp = np.concatenate(temp_segments)

        return ThermalHistory(
            time=full_time,
            temperature=full_temp,
            source=f"synthetic_schedule:{self.treatment_name}",
            uncertainty=2.5,
            metadata={"treatment_name": self.treatment_name, "stages_count": len(self.stages)}
        )

    @classmethod
    def quenching(
        cls,
        austenitize_temp_c: float = 845.0,
        heat_time_s: float = 1800.0,
        hold_time_s: float = 2400.0,
        quench_duration_s: float = 120.0,
        ambient_temp_c: float = 25.0
    ) -> "HeatTreatmentSchedule":
        """Quenching: Heating to 845 degC, holding 40 min, fast oil/water quench to 25 degC in ~120 s."""
        stages = [
            HeatTreatmentStage(name="heating", start_temp_c=25.0, target_temp_c=austenitize_temp_c, duration_s=heat_time_s, regime="linear"),
            HeatTreatmentStage(name="austenitization_hold", start_temp_c=austenitize_temp_c, target_temp_c=austenitize_temp_c, duration_s=hold_time_s, regime="isothermal"),
            HeatTreatmentStage(name="quenching", start_temp_c=austenitize_temp_c, target_temp_c=ambient_temp_c, duration_s=quench_duration_s, regime="newtonian")
        ]
        return cls(treatment_name="Quenching", stages=stages)

    @classmethod
    def normalizing(
        cls,
        austenitize_temp_c: float = 870.0,
        heat_time_s: float = 2100.0,
        hold_time_s: float = 2400.0,
        air_cool_duration_s: float = 3600.0,
        ambient_temp_c: float = 25.0
    ) -> "HeatTreatmentSchedule":
        """Normalizing: Heating to 870 degC, holding 40 min, still-air cooling to 25 degC (~1 hr)."""
        stages = [
            HeatTreatmentStage(name="heating", start_temp_c=25.0, target_temp_c=austenitize_temp_c, duration_s=heat_time_s, regime="linear"),
            HeatTreatmentStage(name="austenitization_hold", start_temp_c=austenitize_temp_c, target_temp_c=austenitize_temp_c, duration_s=hold_time_s, regime="isothermal"),
            HeatTreatmentStage(name="air_cooling", start_temp_c=austenitize_temp_c, target_temp_c=ambient_temp_c, duration_s=air_cool_duration_s, regime="newtonian")
        ]
        return cls(treatment_name="Normalizing", stages=stages)

    @classmethod
    def annealing(
        cls,
        austenitize_temp_c: float = 845.0,
        heat_time_s: float = 2400.0,
        hold_time_s: float = 3600.0,
        furnace_cool_duration_s: float = 28800.0, # 8 hours slow furnace cool
        ambient_temp_c: float = 25.0
    ) -> "HeatTreatmentSchedule":
        """Full Annealing: Heating to 845 degC, holding 1 hr, slow furnace cool at ~20 degC/hr (8 hours) to room temp."""
        stages = [
            HeatTreatmentStage(name="heating", start_temp_c=25.0, target_temp_c=austenitize_temp_c, duration_s=heat_time_s, regime="linear"),
            HeatTreatmentStage(name="austenitization_hold", start_temp_c=austenitize_temp_c, target_temp_c=austenitize_temp_c, duration_s=hold_time_s, regime="isothermal"),
            HeatTreatmentStage(name="furnace_cooling", start_temp_c=austenitize_temp_c, target_temp_c=ambient_temp_c, duration_s=furnace_cool_duration_s, regime="linear")
        ]
        return cls(treatment_name="Annealing", stages=stages)

    @classmethod
    def austempering(
        cls,
        austenitize_temp_c: float = 845.0,
        heat_time_s: float = 1800.0,
        hold_time_s: float = 2400.0,
        salt_bath_quench_s: float = 60.0,
        isothermal_temp_c: float = 340.0,
        isothermal_hold_s: float = 5400.0, # 1.5 hr bainite transformation hold
        final_cool_s: float = 3600.0,
        ambient_temp_c: float = 25.0
    ) -> "HeatTreatmentSchedule":
        """Austempering: Austenitize at 845 degC, rapid salt bath quench to 340 degC (above Ms), isothermal hold 90 min, final air cool."""
        stages = [
            HeatTreatmentStage(name="heating", start_temp_c=25.0, target_temp_c=austenitize_temp_c, duration_s=heat_time_s, regime="linear"),
            HeatTreatmentStage(name="austenitization_hold", start_temp_c=austenitize_temp_c, target_temp_c=austenitize_temp_c, duration_s=hold_time_s, regime="isothermal"),
            HeatTreatmentStage(name="salt_bath_quench", start_temp_c=austenitize_temp_c, target_temp_c=isothermal_temp_c, duration_s=salt_bath_quench_s, regime="newtonian"),
            HeatTreatmentStage(name="isothermal_bainite_hold", start_temp_c=isothermal_temp_c, target_temp_c=isothermal_temp_c, duration_s=isothermal_hold_s, regime="isothermal"),
            HeatTreatmentStage(name="final_cooling", start_temp_c=isothermal_temp_c, target_temp_c=ambient_temp_c, duration_s=final_cool_s, regime="newtonian")
        ]
        return cls(treatment_name="Austempering", stages=stages)

    @classmethod
    def tempering(
        cls,
        austenitize_temp_c: float = 845.0,
        heat_time_s: float = 1800.0,
        hold_time_s: float = 2400.0,
        quench_duration_s: float = 120.0,
        quench_temp_c: float = 25.0,
        reheat_duration_s: float = 1200.0,
        temper_temp_c: float = 550.0,
        temper_hold_s: float = 7200.0, # 2 hours tempering hold
        final_air_cool_s: float = 3600.0,
        ambient_temp_c: float = 25.0
    ) -> "HeatTreatmentSchedule":
        """Tempering: Austenitize, quench to room temp to form martensite, reheat to 550 degC, hold 2 hours, air cool."""
        stages = [
            HeatTreatmentStage(name="heating", start_temp_c=25.0, target_temp_c=austenitize_temp_c, duration_s=heat_time_s, regime="linear"),
            HeatTreatmentStage(name="austenitization_hold", start_temp_c=austenitize_temp_c, target_temp_c=austenitize_temp_c, duration_s=hold_time_s, regime="isothermal"),
            HeatTreatmentStage(name="quench_to_martensite", start_temp_c=austenitize_temp_c, target_temp_c=quench_temp_c, duration_s=quench_duration_s, regime="newtonian"),
            HeatTreatmentStage(name="reheating_to_temper", start_temp_c=quench_temp_c, target_temp_c=temper_temp_c, duration_s=reheat_duration_s, regime="linear"),
            HeatTreatmentStage(name="tempering_hold", start_temp_c=temper_temp_c, target_temp_c=temper_temp_c, duration_s=temper_hold_s, regime="isothermal"),
            HeatTreatmentStage(name="final_cooling", start_temp_c=temper_temp_c, target_temp_c=ambient_temp_c, duration_s=final_air_cool_s, regime="newtonian")
        ]
        return cls(treatment_name="Tempering", stages=stages)
