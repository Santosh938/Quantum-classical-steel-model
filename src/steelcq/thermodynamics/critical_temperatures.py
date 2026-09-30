"""Thermodynamic calculation of critical temperatures Ac1, Ac3, Ms, Mf, Bs, Bf."""

import math
from typing import Dict, Optional, Tuple
from pydantic import BaseModel, Field

from ..materials.schema import SteelMaterial
from ..provenance.record import ParameterRecord, SourceType, ValidationStatus


class CriticalTemperatures(BaseModel):
    """Container for critical transformation temperatures in degC."""
    Ac1: float = Field(..., description="Austenite formation start temp (degC)")
    Ac3: float = Field(..., description="Austenite formation finish temp (degC)")
    Ms: float = Field(..., description="Martensite start temp (degC)")
    Mf: float = Field(..., description="Martensite finish temp (degC)")
    Bs: float = Field(..., description="Bainite start temp (degC)")
    Bf: float = Field(..., description="Bainite finish temp (degC)")
    records: Dict[str, ParameterRecord] = Field(default_factory=dict)


class ThermodynamicModel:
    """Thermodynamic engine calculating critical transformation temperatures with explicit provenance."""

    def __init__(self, material: SteelMaterial) -> None:
        self.material = material
        self.comp = material.composition

    def calculate_Ac1_and_Ac3(self) -> Tuple[float, float, Dict[str, ParameterRecord]]:
        """Calculate Ac1 and Ac3 using Andrews (1965) / Trzaska empirical correlations.

        Ac1 formula (Grange/Andrews):
            Ac1 = 723 - 10.7*Mn - 16.9*Ni + 29.1*Si + 16.9*Cr (°C)
        Ac3 formula (Andrews 1965):
            Ac3 = 910 - 203*sqrt(C) - 15.2*Ni + 44.7*Si + 104*V + 31.5*Mo - 30*Mn - 11*Cr (°C)
        """
        c = self.comp.get("C", 0.0)
        mn = self.comp.get("Mn", 0.0)
        si = self.comp.get("Si", 0.0)
        cr = self.comp.get("Cr", 0.0)
        mo = self.comp.get("Mo", 0.0)
        ni = self.comp.get("Ni", 0.0)
        v = self.comp.get("V", 0.0)

        # Ac1 calculation
        ac1 = 723.0 - (10.7 * mn) - (16.9 * ni) + (29.1 * si) + (16.9 * cr)

        # Ac3 calculation
        ac3 = 910.0 - (203.0 * math.sqrt(max(c, 0.001))) - (15.2 * ni) + (44.7 * si) + (104.0 * v) + (31.5 * mo) - (30.0 * mn) - (11.0 * cr)

        # Ensure physical sanity: Ac3 must be > Ac1 for hypoeutectoid steel
        if ac3 <= ac1:
            ac3 = ac1 + 25.0

        rec_ac1 = ParameterRecord(
            name="Ac1_transformation_start",
            value=round(ac1, 1),
            unit="degC",
            source="Andrews (1965) J. Iron Steel Inst. 203:721; Grange (1961)",
            source_type=SourceType.LITERATURE,
            uncertainty=12.0,
            applicability="Medium carbon low-alloy steels (0.15 < C < 0.6 wt%)",
            calibration_status="literature_regression",
            validation_status=ValidationStatus.VALIDATED,
            provenance_note="Temperature at which austenite formation begins upon heating at ~10 C/s"
        )

        rec_ac3 = ParameterRecord(
            name="Ac3_transformation_finish",
            value=round(ac3, 1),
            unit="degC",
            source="Andrews (1965) J. Iron Steel Inst. 203:721",
            source_type=SourceType.LITERATURE,
            uncertainty=15.0,
            applicability="Hypoeutectoid steels (C < 0.77 wt%, Cr < 3 wt%)",
            calibration_status="literature_regression",
            validation_status=ValidationStatus.VALIDATED,
            provenance_note="Temperature at which ferrite-to-austenite transformation completes upon continuous heating"
        )

        return float(round(ac1, 1)), float(round(ac3, 1)), {"Ac1": rec_ac1, "Ac3": rec_ac3}

    def calculate_Ms_and_Mf(self) -> Tuple[float, float, Dict[str, ParameterRecord]]:
        """Calculate Ms and Mf using Andrews (1965) and Capdevila correlations.

        Ms formula (Andrews linear):
            Ms = 539 - 423*C - 30.4*Mn - 17.7*Ni - 12.1*Cr - 7.5*Mo (°C)
        Mf formula:
            Mf = Ms - 215 (°C) (~99% martensite formed)
        """
        c = self.comp.get("C", 0.0)
        mn = self.comp.get("Mn", 0.0)
        si = self.comp.get("Si", 0.0)
        cr = self.comp.get("Cr", 0.0)
        mo = self.comp.get("Mo", 0.0)
        ni = self.comp.get("Ni", 0.0)

        ms = 539.0 - (423.0 * c) - (30.4 * mn) - (17.7 * ni) - (12.1 * cr) - (7.5 * mo)
        mf = ms - 215.0 # Literature correlation for complete martensitic transformation

        rec_ms = ParameterRecord(
            name="Ms_martensite_start",
            value=round(ms, 1),
            unit="degC",
            source="Andrews (1965) J. Iron Steel Inst. 203:721",
            source_type=SourceType.LITERATURE,
            uncertainty=12.0,
            applicability="Low alloy steels (C: 0.1-0.6, Mn < 2.0, Cr < 3.0 wt%)",
            calibration_status="literature_regression",
            validation_status=ValidationStatus.VALIDATED,
            provenance_note="Temperature at which displacive martensite transformation begins upon rapid cooling"
        )

        rec_mf = ParameterRecord(
            name="Mf_martensite_finish",
            value=round(mf, 1),
            unit="degC",
            source="Grange & Stewart (1946) Trans. AIME 167:467",
            source_type=SourceType.LITERATURE,
            uncertainty=18.0,
            applicability="Medium carbon steels",
            calibration_status="literature_correlation",
            validation_status=ValidationStatus.VALIDATED,
            provenance_note="Temperature corresponding to ~99% martensite transformation completion"
        )

        return float(round(ms, 1)), float(round(mf, 1)), {"Ms": rec_ms, "Mf": rec_mf}

    def calculate_Bs_and_Bf(self) -> Tuple[float, float, Dict[str, ParameterRecord]]:
        """Calculate Bainite Start (Bs) and Finish (Bf) using Steven & Haynes (1956).

        Bs formula:
            Bs = 830 - 270*C - 90*Mn - 37*Ni - 70*Cr - 83*Mo (°C)
        Bf formula:
            Bf = Bs - 120 (°C)
        """
        c = self.comp.get("C", 0.0)
        mn = self.comp.get("Mn", 0.0)
        cr = self.comp.get("Cr", 0.0)
        mo = self.comp.get("Mo", 0.0)
        ni = self.comp.get("Ni", 0.0)

        bs = 830.0 - (270.0 * c) - (90.0 * mn) - (37.0 * ni) - (70.0 * cr) - (83.0 * mo)
        bf = bs - 120.0

        rec_bs = ParameterRecord(
            name="Bs_bainite_start",
            value=round(bs, 1),
            unit="degC",
            source="Steven & Haynes (1956) J. Iron Steel Inst. 183:349",
            source_type=SourceType.LITERATURE,
            uncertainty=15.0,
            applicability="Alloy steels (C: 0.1-0.55, Mn: 0.2-1.7, Cr < 3.5 wt%)",
            calibration_status="literature_regression",
            validation_status=ValidationStatus.VALIDATED,
            provenance_note="Upper limit for bainitic transformation nose"
        )

        rec_bf = ParameterRecord(
            name="Bf_bainite_finish",
            value=round(bf, 1),
            unit="degC",
            source="Bhadeshia (2001) Bainite in Steels",
            source_type=SourceType.LITERATURE,
            uncertainty=20.0,
            applicability="Alloy steels",
            calibration_status="literature_correlation",
            validation_status=ValidationStatus.VALIDATED,
            provenance_note="Lower limit of bainitic transformation prior to martensite intersection"
        )

        return float(round(bs, 1)), float(round(bf, 1)), {"Bs": rec_bs, "Bf": rec_bf}

    def compute_all(self) -> CriticalTemperatures:
        """Compute all transformation temperatures and return structured CriticalTemperatures."""
        ac1, ac3, rec_ac = self.calculate_Ac1_and_Ac3()
        ms, mf, rec_m = self.calculate_Ms_and_Mf()
        bs, bf, rec_b = self.calculate_Bs_and_Bf()

        all_records = {**rec_ac, **rec_m, **rec_b}
        return CriticalTemperatures(
            Ac1=ac1,
            Ac3=ac3,
            Ms=ms,
            Mf=mf,
            Bs=bs,
            Bf=bf,
            records=all_records
        )
