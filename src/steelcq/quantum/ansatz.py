"""Ansatz architectures: Hardware-Efficient, Problem-Inspired, State Preparation, and Measurement circuits."""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector


def build_state_prep_circuit(num_qubits: int = 4, target_phase: str = "austenite") -> QuantumCircuit:
    """Build Initial State Preparation circuit (Figure Q1).

    - 'austenite': all |0> (pure parent FCC austenite phase).
    - 'martensite': all |1> (X gates on all qubits, fully transformed product).
    - 'mixed': superposition / partially transformed state using Ry rotations.
    """
    qc = QuantumCircuit(num_qubits, name="StatePrep")
    if target_phase == "martensite":
        for i in range(num_qubits):
            qc.x(i)
    elif target_phase == "mixed":
        for i in range(num_qubits):
            qc.ry(np.pi / 4.0, i)
    # If austenite, stays in |0000>
    return qc


def build_hardware_efficient_ansatz(num_qubits: int = 4, reps: int = 2) -> QuantumCircuit:
    """Build Hardware-Efficient Ansatz (HEA, Figure Q2).

    Alternates single-qubit Ry(theta) rotations with linear nearest-neighbor CZ entangling gates.
    """
    qc = QuantumCircuit(num_qubits, name="HardwareEfficientAnsatz")
    num_params = num_qubits * (reps + 1)
    theta = ParameterVector("θ_hea", num_params)

    param_idx = 0
    for r in range(reps):
        # Rotation layer
        for i in range(num_qubits):
            qc.ry(theta[param_idx], i)
            param_idx += 1
        qc.barrier()
        # Entanglement layer (CZ gates between adjacent domains)
        for i in range(num_qubits - 1):
            qc.cz(i, i + 1)
        qc.cz(num_qubits - 1, 0) # Ring boundary condition
        qc.barrier()

    # Final rotation layer
    for i in range(num_qubits):
        qc.ry(theta[param_idx], i)
        param_idx += 1

    return qc


def build_problem_inspired_ansatz(num_qubits: int = 4, reps: int = 2) -> QuantumCircuit:
    """Build Problem-Inspired Subspace Ansatz (PIA, Figure Q3).

    Uses excitation-preserving Givens rotations to conserve transformation subspace order parameter.
    """
    qc = QuantumCircuit(num_qubits, name="ProblemInspiredAnsatz")
    num_params = (num_qubits - 1) * reps + num_qubits
    theta = ParameterVector("θ_pia", num_params)

    param_idx = 0
    # Initial Ry layer
    for i in range(num_qubits):
        qc.ry(theta[param_idx], i)
        param_idx += 1
    qc.barrier()

    for r in range(reps):
        # Givens/particle-conserving rotation block between adjacent qubits
        for i in range(num_qubits - 1):
            # Givens block: CNOT(i, j) -> Cry(theta, j, i) -> CNOT(i, j)
            qc.cx(i, i + 1)
            qc.ry(theta[param_idx], i + 1)
            qc.cx(i, i + 1)
            param_idx += 1
        qc.barrier()

    return qc


def build_measurement_circuit(ansatz: QuantumCircuit) -> QuantumCircuit:
    """Append measurement operations to an ansatz (Figure Q4)."""
    n = ansatz.num_qubits
    qc = QuantumCircuit(n, n, name="MeasurementCircuit")
    qc.compose(ansatz, inplace=True)
    qc.measure(range(n), range(n))
    return qc
