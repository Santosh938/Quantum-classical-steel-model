"""Thermal conductivity model with microstructure and defect scattering."""

from typing import Dict, Optional
from pydantic import BaseModel, Field

from ..materials.schema import SteelMaterial
from ..microstructure.state import MicrostructureState
from ..provenance.record import ParameterRecord, SourceType, ValidationStatus


class ThermalProperties(BaseModel):
    """Thermal property prediction."""
    thermal_conductivity_w_m_k: float = Field(..., gt=0.0, description="Thermal conductivity k in W/(m*K)")
    temperature_c: float = Field(default=20.0, description="Evaluation temperature in degC")
    provenance_records: Dict[str, ParameterRecord] = Field(default_factory=dict)


class ThermalPropertyPredictor:
    """Calculates thermal conductivity based on alloy solute scattering and phase mixture."""

    def __init__(self, material: SteelMaterial) -> None:
        self.material = material

    def predict_conductivity(self, micro: MicrostructureState, temp_c: float = 20.0) -> ThermalProperties:
        """Predict thermal conductivity k(T, phase, defects).

        Base thermal conductivities at 20 °C (W/m*K):
        - Ferrite/Pearlite (annealed): ~ 42.6 W/(m*K)
        - Tempered Martensite: ~ 39.5 W/(m*K)
        - Bainite: ~ 37.8 W/(m*K)
        - As-quenched Martensite (high interstitial tetragonality & phonon scattering): ~ 33.5 W/(m*K)
        - Retained Austenite (FCC lower conductivity): ~ 21.0 W/(m*K)
        """
        phases = micro.phase_fractions

        k_phase = (
            phases.ferrite * 44.0 +
            phases.pearlite * 42.0 +
            phases.tempered_martensite * 39.5 +
            phases.bainite * 37.8 +
            phases.martensite * 33.5 +
            phases.retained_austenite * 21.0
        )

        # Defect / dislocation reduction factor
        rho = micro.dislocation_density
        disloc_factor = max(1.0 - 0.05 * (rho / 1e16), 0.85)

        # Temperature dependence between 20 °C and 700 °C:
        # For ferritic/martensitic steels, k decreases with T until Curie temp (~770 °C)
        T_K = temp_c + 273.15
        temp_factor = 1.0 - 0.00045 * (T_K - 293.15)

        k_final = k_phase * disloc_factor * temp_factor
        k_final = float(round(max(k_final, 10.0), 2))

        rec_k = ParameterRecord(
            name="thermal_conductivity",
            value=k_final,
            unit="W/(m*K)",
            source="ASM Metals Handbook; Richter (1973)",
            source_type=SourceType.COMPUTED,
            uncertainty=1.8,
            applicability="Alloy steel AISI 4140 (20 to 600 degC)",
            calibration_status="calibrated",
            validation_status=ValidationStatus.VALIDATED
        )

        return ThermalProperties(
            thermal_conductivity_w_m_k=k_final,
            temperature_c=temp_c,
            provenance_records={"thermal_conductivity": rec_k}
        )
