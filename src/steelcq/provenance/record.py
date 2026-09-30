"""Parameter record and provenance tracker."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    LITERATURE = "literature"
    EXPERIMENTAL = "experimental"
    DATABASE = "database"
    USER_INPUT = "user_input"
    DERIVED = "derived"
    CALIBRATED = "calibrated"
    COMPUTED = "computed"


class ValidationStatus(str, Enum):
    VALIDATED = "VALIDATED"
    WARNING = "WARNING"
    ASSUMPTION = "ASSUMPTION"
    MISSING = "MISSING"
    ERROR = "ERROR"


class ParameterRecord(BaseModel):
    """Traceable scientific parameter record with provenance and uncertainty."""

    name: str = Field(..., description="Parameter name (e.g. 'carbon_content', 'Ac1')")
    value: Any = Field(..., description="Numerical or structured parameter value")
    unit: str = Field(..., description="Standard physical unit (e.g. 'wt%', 'degC', 'J/mol')")
    source: str = Field(..., description="Literature citation, dataset, DOI, or calculation rule")
    source_type: SourceType = Field(..., description="Category of the source")
    uncertainty: Optional[Union[float, Dict[str, float]]] = Field(
        default=None,
        description="Standard uncertainty (1-sigma) or bounds (e.g. {'std': 0.01} or {'min': 0.38, 'max': 0.43})"
    )
    applicability: Optional[str] = Field(
        default=None,
        description="Range or condition under which this value/formula is scientifically valid"
    )
    calibration_status: str = Field(
        default="uncalibrated",
        description="Whether parameter has been calibrated, verified, or is nominal"
    )
    validation_status: ValidationStatus = Field(
        default=ValidationStatus.VALIDATED,
        description="QC validation state (VALIDATED, WARNING, ASSUMPTION, MISSING, ERROR)"
    )
    provenance_note: Optional[str] = Field(
        default=None,
        description="Contextual remarks regarding assumptions or derivation"
    )

    @field_validator("name", "unit", "source")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return v.strip()


class ProvenanceTracker:
    """Registry to collect, query, and audit parameter provenance across pipelines."""

    def __init__(self) -> None:
        self._records: Dict[str, ParameterRecord] = {}

    def register(self, record: ParameterRecord) -> None:
        self._records[record.name] = record

    def get(self, name: str) -> Optional[ParameterRecord]:
        return self._records.get(name)

    def list_records(self) -> List[ParameterRecord]:
        return list(self._records.values())

    def audit_summary(self) -> Dict[str, int]:
        summary: Dict[str, int] = {status.value: 0 for status in ValidationStatus}
        for r in self._records.values():
            summary[r.validation_status.value] += 1
        return summary

    def export_dict(self) -> Dict[str, Any]:
        return {k: v.model_dump() for k, v in self._records.items()}
