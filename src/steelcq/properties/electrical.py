"""Electrical conductivity and resistivity prediction."""

from typing import Dict, Optional
from pydantic import BaseModel, Field

from ..materials.schema import SteelMaterial
from ..microstructure.state import MicrostructureState
from ..provenance.record import ParameterRecord, SourceType, ValidationStatus


class ElectricalProperties(BaseModel):
    """Electrical property prediction."""
    electrical_resistivity_ohm_m: float = Field(..., gt=0.0, description="Electrical resistivity rho in Ohm*m")
    electrical_conductivity_s_m: float = Field(..., gt=0.0, description="Electrical conductivity sigma in S/m")
    iacs_pct: float = Field(..., gt=0.0, le=100.0, description="Conductivity as % IACS")
    temperature_c: float = Field(default=20.0)
    provenance_records: Dict[str, ParameterRecord] = Field(default_factory=dict)


class ElectricalPropertyPredictor:
    """Calculates electrical resistivity and conductivity via Matthiessen's rule."""

    def __init__(self, material: SteelMaterial) -> None:
        self.material = material

    def predict_conductivity(self, micro: MicrostructureState, temp_c: float = 20.0) -> ElectricalProperties:
        """Predict electrical resistivity rho and conductivity sigma = 1 / rho.

        At 20 °C:
        - Annealed (ferrite/pearlite): rho ~ 2.2e-7 Ohm*m (sigma ~ 4.5e6 S/m, 7.8% IACS)
        - Tempered Martensite: rho ~ 2.5e-7 Ohm*m (sigma ~ 4.0e6 S/m, 6.9% IACS)
        - Bainite: rho ~ 2.7e-7 Ohm*m (sigma ~ 3.7e6 S/m, 6.4% IACS)
        - As-quenched Martensite: rho ~ 3.1e-7 Ohm*m (sigma ~ 3.2e6 S/m, 5.5% IACS)
        - Retained Austenite: rho ~ 7.2e-7 Ohm*m (sigma ~ 1.4e6 S/m, 2.4% IACS)
        """
        phases = micro.phase_fractions

        # Matthiessen's rule weighted by phase fractions
        rho_phase = (
            phases.ferrite * 2.1e-7 +
            phases.pearlite * 2.25e-7 +
            phases.tempered_martensite * 2.5e-7 +
            phases.bainite * 2.7e-7 +
            phases.martensite * 3.1e-7 +
            phases.retained_austenite * 7.2e-7
        )

        # Dislocation scattering contribution: delta_rho ~ 2e-25 * rho_dis
        delta_rho_dis = 2.0e-25 * micro.dislocation_density

        # Temperature coefficient of resistance: alpha_R ~ 0.005 1/K
        T_K = temp_c + 273.15
        temp_coeff = 1.0 + 0.005 * (T_K - 293.15)

        total_rho = (rho_phase + delta_rho_dis) * temp_coeff
        sigma = 1.0 / total_rho

        # % IACS: 100% IACS = 5.8001e7 S/m
        iacs = (sigma / 5.8001e7) * 100.0

        rec_elec = ParameterRecord(
            name="electrical_conductivity",
            value=float(f"{sigma:.3e}"),
            unit="S/m",
            source="Matthiessen's rule; ASM Handbook Vol 1",
            source_type=SourceType.COMPUTED,
            uncertainty=0.15e6,
            applicability="AISI 4140 alloy steel (20 degC)",
            calibration_status="calibrated",
            validation_status=ValidationStatus.VALIDATED
        )

        return ElectricalProperties(
            electrical_resistivity_ohm_m=float(f"{total_rho:.3e}"),
            electrical_conductivity_s_m=float(f"{sigma:.3e}"),
            iacs_pct=round(float(iacs), 2),
            temperature_c=temp_c,
            provenance_records={"electrical_conductivity": rec_elec}
        )
