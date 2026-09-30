"""Quantum state encoding and qubit mapping for mesoscopic domain cluster."""

from typing import Dict, List
from pydantic import BaseModel, Field


class QubitDefinition(BaseModel):
    qubit_id: int
    physical_interpretation: str
    basis_0: str = "Austenite (FCC, parent)"
    basis_1: str = "Transformed product (BCC/BCT, martensite/ferrite/bainite)"
    domain_coordinate: tuple[int, int]


class DomainStateEncoding:
    """Documented mapping between physical transformation states and 4-qubit cluster states."""

    def __init__(self, num_qubits: int = 4) -> None:
        self.num_qubits = num_qubits
        # 2x2 domain cluster grid: (0,0), (0,1), (1,0), (1,1)
        self.qubits: Dict[int, QubitDefinition] = {
            0: QubitDefinition(qubit_id=0, physical_interpretation="Domain [0,0] structural order parameter", domain_coordinate=(0, 0)),
            1: QubitDefinition(qubit_id=1, physical_interpretation="Domain [0,1] structural order parameter", domain_coordinate=(0, 1)),
            2: QubitDefinition(qubit_id=2, physical_interpretation="Domain [1,0] structural order parameter", domain_coordinate=(1, 0)),
            3: QubitDefinition(qubit_id=3, physical_interpretation="Domain [1,1] structural order parameter", domain_coordinate=(1, 1)),
        }

    def get_basis_state_description(self, bitstring: str) -> str:
        """Interpret a 4-bit computational basis state (e.g. '0000', '1111')."""
        ones = bitstring.count("1")
        frac = ones / len(bitstring)
        if ones == 0:
            return f"|{bitstring}>: Pure FCC Austenite parent phase (f_trans = 0.0)"
        elif ones == len(bitstring):
            return f"|{bitstring}>: Fully transformed BCC/BCT product phase (f_trans = 1.0)"
        else:
            return f"|{bitstring}>: Mixed domain cluster with {ones}/{len(bitstring)} transformed domains (f_trans = {frac:.2f})"

    def nearest_neighbor_pairs(self) -> List[tuple[int, int]]:
        """Return 2x2 grid nearest-neighbor domain interaction pairs."""
        return [(0, 1), (0, 2), (1, 3), (2, 3)]
