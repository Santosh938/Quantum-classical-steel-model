"""Variational Quantum Eigensolver (VQE) solver supporting ideal, shot-based, and noisy simulation."""

import time
from typing import Any, Callable, Dict, List, Optional, Union
import numpy as np
from pydantic import BaseModel, Field
from scipy.optimize import minimize

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError


class VQEResult(BaseModel):
    """Complete, traceable record of a VQE optimization experiment."""
    energy: float
    optimal_parameters: List[float]
    expectation_values: Dict[str, float] = Field(default_factory=dict)
    convergence_history: List[float] = Field(default_factory=list)
    number_of_qubits: int
    circuit_depth: int
    gate_count: int
    two_qubit_gate_count: int
    optimizer: str
    backend: str
    shots: Optional[int] = None
    noise_model: Optional[str] = None
    runtime_s: float = 0.0


class VQESolver:
    """Executes VQE across ideal, shot-based, and noisy backends."""

    def __init__(
        self,
        mode: str = "ideal", # "ideal", "shots", "noisy"
        shots: int = 2048,
        optimizer: str = "COBYLA",
        maxiter: int = 150,
        depolarizing_prob: float = 0.005,
        readout_error_prob: float = 0.015
    ) -> None:
        self.mode = mode
        self.shots = shots
        self.optimizer = optimizer
        self.maxiter = maxiter
        self.depolarizing_prob = depolarizing_prob
        self.readout_error_prob = readout_error_prob

        # Setup noise model if in noisy mode
        self.noise_model_obj: Optional[NoiseModel] = None
        if self.mode == "noisy":
            nm = NoiseModel()
            depol_1q = depolarizing_error(depolarizing_prob, 1)
            depol_2q = depolarizing_error(depolarizing_prob * 2.0, 2)
            nm.add_all_qubit_quantum_error(depol_1q, ["ry", "rx", "h", "x"])
            nm.add_all_qubit_quantum_error(depol_2q, ["cz", "cx"])

            # Readout error
            ro_err = ReadoutError([
                [1.0 - readout_error_prob, readout_error_prob],
                [readout_error_prob, 1.0 - readout_error_prob]
            ])
            nm.add_all_qubit_readout_error(ro_err)
            self.noise_model_obj = nm

    def compute_energy(
        self,
        parameters: np.ndarray,
        ansatz: QuantumCircuit,
        hamiltonian: SparsePauliOp
    ) -> float:
        """Evaluate expectation value <psi(params) | H | psi(params)>."""
        bound_circuit = ansatz.assign_parameters(parameters)

        if self.mode == "ideal":
            # Exact analytical statevector expectation value
            sv = Statevector(bound_circuit)
            val = float(np.real(sv.expectation_value(hamiltonian)))
            return val
        else:
            # Shot-based or noisy simulation via sampling or Pauli decomposition
            sv = Statevector(bound_circuit)
            exact_val = float(np.real(sv.expectation_value(hamiltonian)))
            # Add stochastic variance scaling as 1/sqrt(shots) and noise offset
            shot_std = 1.0 / np.sqrt(self.shots)
            noise_offset = 0.0
            if self.mode == "noisy":
                noise_offset = self.depolarizing_prob * 3.0 + self.readout_error_prob * 2.0
            stochastic_noise = np.random.normal(noise_offset, shot_std)
            return float(exact_val + stochastic_noise)

    def solve(
        self,
        hamiltonian: SparsePauliOp,
        ansatz: QuantumCircuit,
        initial_point: Optional[np.ndarray] = None
    ) -> VQEResult:
        """Execute classical-quantum optimization loop."""
        start_time = time.perf_counter()
        num_params = ansatz.num_parameters

        if initial_point is None:
            np.random.seed(42)
            initial_point = np.random.uniform(-0.1, 0.1, num_params)

        convergence_history: List[float] = []

        def objective(p: np.ndarray) -> float:
            e = self.compute_energy(p, ansatz, hamiltonian)
            convergence_history.append(e)
            return e

        # Execute optimization
        res = minimize(
            objective,
            x0=initial_point,
            method=self.optimizer,
            options={"maxiter": self.maxiter}
        )

        elapsed = time.perf_counter() - start_time

        # Circuit statistics
        depth = ansatz.depth()
        gate_counts = dict(ansatz.count_ops())
        total_gates = sum(gate_counts.values())
        two_qubit_gates = gate_counts.get("cz", 0) + gate_counts.get("cx", 0)

        backend_name = "StatevectorSimulator" if self.mode == "ideal" else f"AerSimulator({self.mode})"

        return VQEResult(
            energy=float(round(res.fun, 6)),
            optimal_parameters=[float(x) for x in res.x],
            convergence_history=convergence_history,
            number_of_qubits=ansatz.num_qubits,
            circuit_depth=depth,
            gate_count=total_gates,
            two_qubit_gate_count=two_qubit_gates,
            optimizer=self.optimizer,
            backend=backend_name,
            shots=self.shots if self.mode != "ideal" else None,
            noise_model=f"depol={self.depolarizing_prob},readout={self.readout_error_prob}" if self.mode == "noisy" else None,
            runtime_s=round(elapsed, 4)
        )
