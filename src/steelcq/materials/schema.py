"""Steel material and composition schema."""

from typing import Dict, Optional, Tuple, Any
from pydantic import BaseModel, Field, model_validator
from ..provenance.record import ParameterRecord, SourceType, ValidationStatus


class CompositionRange(BaseModel):
    """Allowable element range according to standard specification (e.g. ASTM A29)."""
    min_val: float = Field(..., ge=0.0, description="Minimum weight percentage")
    max_val: float = Field(..., ge=0.0, description="Maximum weight percentage")
    nominal: float = Field(..., ge=0.0, description="Nominal weight percentage")


class ElementSpecification(BaseModel):
    """Specification of an alloying element with standard limits and provenance."""
    symbol: str
    nominal_wt_pct: float
    range_wt_pct: Optional[Tuple[float, float]] = None
    record: Optional[ParameterRecord] = None


class SteelMaterial(BaseModel):
    """Research-grade steel material model with full provenance and QC checks."""

    name: str = Field(..., description="Standard steel designation (e.g. 'AISI 4140')")
    standard: str = Field(default="ASTM A29 / SAE J404", description="Material standard")
    composition: Dict[str, float] = Field(..., description="Element symbol to weight percent (wt%)")
    composition_ranges: Dict[str, Tuple[float, float]] = Field(
        default_factory=dict,
        description="Standard composition limits (min, max) in wt%"
    )
    density_kg_m3: float = Field(default=7850.0, description="Density at room temperature in kg/m3")
    initial_microstructure: str = Field(
        default="as-received_hot-rolled_ferrite_pearlite",
        description="Initial state prior to heat treatment"
    )
    initial_grain_size_um: float = Field(
        default=25.0,
        gt=0.0,
        description="Initial average austenite/ferrite grain size in micrometers"
    )
    provenance_records: Dict[str, ParameterRecord] = Field(
        default_factory=dict,
        description="Traceable records for every composition and physical parameter"
    )

    @model_validator(mode="after")
    def validate_and_balance_composition(self) -> "SteelMaterial":
        """Validate composition bounds and balance iron (Fe)."""
        comp = dict(self.composition)

        # Check for non-negative values
        for el, val in comp.items():
            if val < 0.0:
                raise ValueError(f"Negative concentration for element {el}: {val} wt%")

        # Ensure Fe balance if not provided or to ensure strict 100.0 wt%
        alloying_sum = sum(v for k, v in comp.items() if k != "Fe")
        if alloying_sum > 100.0:
            raise ValueError(f"Sum of alloying elements exceeds 100 wt%: {alloying_sum:.4f}")

        if "Fe" not in comp or abs((comp["Fe"] + alloying_sum) - 100.0) > 1e-4:
            comp["Fe"] = round(100.0 - alloying_sum, 5)

        self.composition = comp

        # Check limits against ranges if defined
        for el, (low, high) in self.composition_ranges.items():
            actual = comp.get(el, 0.0)
            if actual < (low - 1e-5) or actual > (high + 1e-5):
                # We do not fail silently; if outside, update validation status on parameter record
                if el in self.provenance_records:
                    self.provenance_records[el].validation_status = ValidationStatus.WARNING
                    self.provenance_records[el].provenance_note = (
                        f"Value {actual} wt% is outside standard specification [{low}, {high}] wt%."
                    )

        return self

    def get_element(self, symbol: str) -> float:
        """Get weight percent of an element, returning 0.0 if not present."""
        return float(self.composition.get(symbol, 0.0))

    def carbon_equivalent_iiw(self) -> float:
        """Calculate International Institute of Welding Carbon Equivalent: CE_IIW = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15."""
        c = self.get_element("C")
        mn = self.get_element("Mn")
        cr = self.get_element("Cr")
        mo = self.get_element("Mo")
        v = self.get_element("V")
        ni = self.get_element("Ni")
        cu = self.get_element("Cu")
        return c + (mn / 6.0) + ((cr + mo + v) / 5.0) + ((ni + cu) / 15.0)
