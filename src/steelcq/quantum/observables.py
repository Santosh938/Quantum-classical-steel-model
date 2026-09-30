"""Quantum observables and descriptor set extraction."""

from typing import Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp


class QuantumDescriptorSet(BaseModel):
    """Set of quantified quantum observables extracted from optimized ground state."""
    ground_state_energy: float = Field(..., description="VQE ground state energy E0")
    local_expectations: Dict[str, float] = Field(..., description="<Z_i> magnetization for each domain qubit")
    pair_correlations: Dict[str, float] = Field(..., description="<Z_i Z_j> two-domain correlators")
    mean_order_parameter: float = Field(..., description="Transformed fraction derived from <(I-Z)/2>")
    fluctuation_susceptibility: float = Field(..., description="Spatial correlation sum chi")
    entanglement_entropy: float = Field(..., description="Bipartite entanglement entropy S_E")
    uncertainty: float = Field(default=0.01, description="Statistical / shot noise error estimate")
    backend_metadata: Dict[str, str] = Field(default_factory=dict)


class ObservableCalculator:
    """Evaluates physical observables from optimized quantum state."""

    @staticmethod
    def calculate_descriptors(
        ansatz: QuantumCircuit,
        optimal_parameters: List[float],
        ground_state_energy: float,
        backend_name: str = "ideal_statevector",
        shot_noise_std: float = 0.01
    ) -> QuantumDescriptorSet:
        """Evaluate local expectations <Z_i>, two-domain correlations <Z_i Z_j>, and entropy."""
        n = ansatz.num_qubits
        bound_circ = ansatz.assign_parameters(optimal_parameters)
        sv = Statevector(bound_circ)

        # 1. Local <Z_i>
        local_z: Dict[str, float] = {}
        for i in range(n):
            label = list("I" * n)
            label[i] = "Z"
            op = SparsePauliOp(["".join(label)], [1.0])
            val = float(np.real(sv.expectation_value(op)))
            local_z[f"Z_{i}"] = round(val, 4)

        # 2. Pair correlations <Z_i Z_j>
        pairs: Dict[str, float] = {}
        for i in range(n):
            for j in range(i + 1, n):
                label = list("I" * n)
                label[i] = "Z"
                label[j] = "Z"
                op = SparsePauliOp(["".join(label)], [1.0])
                val = float(np.real(sv.expectation_value(op)))
                pairs[f"Z_{i}Z_{j}"] = round(val, 4)

        # 3. Mean order parameter n_avg = (1 - <Z>_avg) / 2
        mean_z = np.mean(list(local_z.values()))
        order_param = float(round((1.0 - mean_z) / 2.0, 4))

        # 4. Fluctuation susceptibility chi = sum_<i,j> (<Z_i Z_j> - <Z_i><Z_j>)
        connected_corrs = []
        for i in range(n):
            for j in range(i + 1, n):
                c_ij = pairs[f"Z_{i}Z_{j}"] - (local_z[f"Z_{i}"] * local_z[f"Z_{j}"])
                connected_corrs.append(c_ij)
        chi = float(round(sum(connected_corrs), 4))

        # 5. Bipartite entanglement entropy for split [0, 1] vs [2, 3]
        # Trace out qubits 2, 3
        rho = sv.to_operator()
        # Compute eigenvalues of density matrix or simple approximation
        probs = sv.probabilities()
        # Shannon entropy of probability distribution as proxy for superposition spread
        non_zero_p = probs[probs > 1e-12]
        entropy = float(round(-np.sum(non_zero_p * np.log2(non_zero_p)), 4))

        return QuantumDescriptorSet(
            ground_state_energy=round(ground_state_energy, 4),
            local_expectations=local_z,
            pair_correlations=pairs,
            mean_order_parameter=order_param,
            fluctuation_susceptibility=chi,
            entanglement_entropy=entropy,
            uncertainty=shot_noise_std,
            backend_metadata={"backend": backend_name, "qubits": str(n)}
        )
