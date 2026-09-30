"""Physically motivated reduced-order domain Hamiltonian generator."""

from typing import Dict, List, Tuple
import numpy as np
from qiskit.quantum_info import SparsePauliOp

from ..materials.schema import SteelMaterial
from ..thermodynamics.critical_temperatures import CriticalTemperatures, ThermodynamicModel
from .encoding import DomainStateEncoding


class SteelDomainHamiltonian:
    """Constructs physical Pauli Hamiltonian H(T, C, f_target) for 4-qubit mesoscopic cluster."""

    def __init__(
        self,
        material: SteelMaterial,
        crit_temps: CriticalTemperatures,
        lambda_constraint: float = 2.5,
        coupling_J: float = 0.8
    ) -> None:
        self.material = material
        self.crit = crit_temps
        self.lambda_constraint = float(lambda_constraint)
        self.coupling_J = float(coupling_J)
        self.encoding = DomainStateEncoding(num_qubits=4)

    def calculate_chemical_field(self, temp_c: float) -> float:
        """Calculate single-domain chemical field h(T) representing free-energy driving force Delta G(T).

        - At T > Ac3: h(T) > 0 (favors |0> austenite, Z = +1)
        - At T < Ms:  h(T) < 0 (favors |1> martensite/product, Z = -1)
        - At T0 ~ 0.5 * (Ac1 + Ms): h(T) ~ 0 (neutral equilibrium)
        Normalized energy units (eV/domain or arb. chemical potential units).
        """
        T0 = 0.5 * (self.crit.Ac1 + self.crit.Ms) # ~ 530 C
        delta_T = temp_c - T0
        # Driving force coefficient ~ 0.008 per degree undercooling/superheating
        h = 0.008 * delta_T
        return float(np.clip(h, -3.0, 3.0))

    def build_pauli_operator(
        self,
        temp_c: float,
        target_transformed_fraction: float = 0.5
    ) -> SparsePauliOp:
        """Construct SparsePauliOp representing:

        H = sum_i h Z_i + sum_<i,j> J Z_i Z_j + lambda * ( sum_i (I - Z_i)/2 - N * f_target )^2
        """
        n = 4
        h_chem = self.calculate_chemical_field(temp_c)
        J = self.coupling_J
        lam = self.lambda_constraint
        f_tgt = float(np.clip(target_transformed_fraction, 0.0, 1.0))
        target_count = n * f_tgt

        pauli_dict: Dict[str, complex] = {}

        # 1. Chemical field: sum_i h_chem * Z_i
        for i in range(n):
            label = list("I" * n)
            label[i] = "Z"
            pauli_dict["".join(label)] = pauli_dict.get("".join(label), 0.0) + h_chem

        # 2. Interfacial coupling: sum_<i,j> J * Z_i Z_j
        pairs = self.encoding.nearest_neighbor_pairs()
        for i, j in pairs:
            label = list("I" * n)
            label[i] = "Z"
            label[j] = "Z"
            pauli_dict["".join(label)] = pauli_dict.get("".join(label), 0.0) + J

        # 3. Soft constraint: lam * ( sum_i (I - Z_i)/2 - target_count )^2
        # Let n_hat = sum_i (I - Z_i)/2 = (n/2) * I - (1/2) * sum_i Z_i
        # (n_hat - target_count) = ( (n/2) - target_count ) * I - (1/2) * sum_i Z_i
        # Let c0 = (n/2 - target_count)
        # (c0 * I - 0.5 * sum_i Z_i)^2 = c0^2 * I - c0 * sum_i Z_i + 0.25 * (sum_i Z_i)^2
        # (sum_i Z_i)^2 = sum_i Z_i^2 + 2 * sum_{i < j} Z_i Z_j = n * I + 2 * sum_{i < j} Z_i Z_j
        c0 = (n / 2.0) - target_count

        # Identity term
        const_term = lam * (c0 ** 2 + 0.25 * n)
        pauli_dict["I" * n] = pauli_dict.get("I" * n, 0.0) + const_term

        # Linear Z_i terms from constraint
        z_coeff = -lam * c0
        for i in range(n):
            label = list("I" * n)
            label[i] = "Z"
            pauli_dict["".join(label)] = pauli_dict.get("".join(label), 0.0) + z_coeff

        # Quadratic Z_i Z_j terms from constraint (all pairs i < j)
        zz_coeff = lam * 0.5
        for i in range(n):
            for j in range(i + 1, n):
                label = list("I" * n)
                label[i] = "Z"
                label[j] = "Z"
                pauli_dict["".join(label)] = pauli_dict.get("".join(label), 0.0) + zz_coeff

        # Convert to Qiskit SparsePauliOp
        labels = list(pauli_dict.keys())
        coeffs = [pauli_dict[k] for k in labels]
        return SparsePauliOp(labels, coeffs)
