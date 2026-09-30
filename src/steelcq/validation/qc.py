"""Quality control and physics consistency verification."""

from typing import Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field
from ..provenance.record import ValidationStatus
from ..materials.schema import SteelMaterial
from ..thermal_history.history import ThermalHistory


class QCItem(BaseModel):
    """Individual quality check result item."""
    check_name: str
    status: ValidationStatus
    message: str
    parameter: Optional[str] = None
    value: Optional[float] = None
    bounds: Optional[tuple] = None


class QCReport(BaseModel):
    """Aggregate quality control report."""
    is_valid: bool
    items: List[QCItem] = Field(default_factory=list)

    def add(self, item: QCItem) -> None:
        self.items.append(item)
        if item.status == ValidationStatus.ERROR:
            self.is_valid = False

    def summary(self) -> Dict[str, int]:
        counts = {s.value: 0 for s in ValidationStatus}
        for it in self.items:
            counts[it.status.value] += 1
        return counts


class QualityControlValidator:
    """Rigorous pre-simulation physics and consistency validator."""

    @staticmethod
    def validate_material(material: SteelMaterial) -> QCReport:
        """Validate steel composition against standard ASTM/SAE limits."""
        report = QCReport(is_valid=True)
        comp = material.composition

        # 1. Total balance
        total = sum(comp.values())
        if abs(total - 100.0) > 0.05:
            report.add(QCItem(
                check_name="total_composition_balance",
                status=ValidationStatus.ERROR,
                message=f"Total composition sum is {total:.3f} wt% (must equal 100.0 wt%).",
                value=total
            ))
        else:
            report.add(QCItem(
                check_name="total_composition_balance",
                status=ValidationStatus.VALIDATED,
                message="Total composition balances to 100.0 wt%.",
                value=total
            ))

        # 2. Composition ranges
        for elem, (low, high) in material.composition_ranges.items():
            val = comp.get(elem, 0.0)
            if val < low or val > high:
                report.add(QCItem(
                    check_name=f"composition_range_{elem}",
                    status=ValidationStatus.WARNING,
                    message=f"Element {elem} content {val:.3f} wt% is outside ASTM range [{low}, {high}] wt%.",
                    parameter=elem,
                    value=val,
                    bounds=(low, high)
                ))
            else:
                report.add(QCItem(
                    check_name=f"composition_range_{elem}",
                    status=ValidationStatus.VALIDATED,
                    message=f"Element {elem} content {val:.3f} wt% satisfies range [{low}, {high}] wt%.",
                    parameter=elem,
                    value=val,
                    bounds=(low, high)
                ))

        # 3. Carbon range for hypoeutectoid 4140
        c = comp.get("C", 0.0)
        if c < 0.2 or c > 0.6:
            report.add(QCItem(
                check_name="carbon_applicability",
                status=ValidationStatus.ERROR,
                message=f"Carbon content {c:.3f} wt% is invalid for medium-carbon 4140 alloy steel.",
                parameter="C",
                value=c
            ))

        return report

    @staticmethod
    def validate_thermal_history(history: ThermalHistory) -> QCReport:
        """Validate temperature trajectory continuity, time monotonicity, and physical thermal bounds."""
        report = QCReport(is_valid=True)

        # 1. Time monotonicity
        dt = np.diff(history.time)
        if np.any(dt <= 0.0):
            report.add(QCItem(
                check_name="time_monotonicity",
                status=ValidationStatus.ERROR,
                message="Thermal history time contains non-positive time increments."
            ))
        else:
            report.add(QCItem(
                check_name="time_monotonicity",
                status=ValidationStatus.VALIDATED,
                message=f"Time is strictly monotonically increasing (total duration {history.total_duration_s:.1f} s)."
            ))

        # 2. Temperature bounds (steel solidus / room temp)
        min_t = history.min_temperature
        max_t = history.max_temperature

        if min_t < -196.0: # Liquid nitrogen lower bound
            report.add(QCItem(
                check_name="min_temperature_bound",
                status=ValidationStatus.ERROR,
                message=f"Minimum temperature {min_t:.1f} degC is unphysically low.",
                value=min_t
            ))
        elif min_t < 0.0:
            report.add(QCItem(
                check_name="min_temperature_bound",
                status=ValidationStatus.ASSUMPTION,
                message=f"Sub-zero cryo-treatment detected ({min_t:.1f} degC).",
                value=min_t
            ))
        else:
            report.add(QCItem(
                check_name="min_temperature_bound",
                status=ValidationStatus.VALIDATED,
                message=f"Minimum temperature {min_t:.1f} degC is within physical bounds.",
                value=min_t
            ))

        if max_t > 1450.0: # Exceeds steel solidus/melting point
            report.add(QCItem(
                check_name="max_temperature_bound",
                status=ValidationStatus.ERROR,
                message=f"Maximum temperature {max_t:.1f} degC exceeds steel solidus melting point (~1420-1450 degC).",
                value=max_t
            ))
        elif max_t > 1100.0:
            report.add(QCItem(
                check_name="max_temperature_bound",
                status=ValidationStatus.WARNING,
                message=f"Maximum temperature {max_t:.1f} degC causes severe austenite grain coarsening.",
                value=max_t
            ))
        else:
            report.add(QCItem(
                check_name="max_temperature_bound",
                status=ValidationStatus.VALIDATED,
                message=f"Maximum temperature {max_t:.1f} degC is within standard heat-treatment range.",
                value=max_t
            ))

        # 3. Cooling rate stability
        dT_dt = history.derivative_at(history.time)
        max_cooling_rate = -np.min(dT_dt)
        if max_cooling_rate > 2000.0: # e.g. 2000 degC/s (extremely aggressive water/brine spray)
            report.add(QCItem(
                check_name="cooling_rate_feasibility",
                status=ValidationStatus.WARNING,
                message=f"Peak cooling rate {max_cooling_rate:.1f} degC/s exceeds typical bulk quench limits.",
                value=max_cooling_rate
            ))
        else:
            report.add(QCItem(
                check_name="cooling_rate_feasibility",
                status=ValidationStatus.VALIDATED,
                message=f"Peak cooling rate is feasible ({max_cooling_rate:.1f} degC/s).",
                value=max_cooling_rate
            ))

        return report
