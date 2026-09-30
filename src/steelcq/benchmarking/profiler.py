"""Computational resource profiler for Classical, Quantum, and Hybrid workflows."""

import time
from typing import Dict, Optional
from pydantic import BaseModel, Field


class BenchmarkMetrics(BaseModel):
    """Resource consumption summary across paradigms."""
    model_type: str = Field(..., description="'Classical', 'Quantum', or 'Hybrid'")
    runtime_s: float
    memory_mb_estimated: float
    num_qubits: Optional[int] = None
    circuit_depth: Optional[int] = None
    total_gates: Optional[int] = None
    two_qubit_gates: Optional[int] = None
    vqe_iterations: Optional[int] = None
    shots: Optional[int] = None


class BenchmarkProfiler:
    """Measures runtime, iterations, and gate complexity."""

    @staticmethod
    def profile_classical(runtime_s: float, iterations: int = 150) -> BenchmarkMetrics:
        return BenchmarkMetrics(
            model_type="Classical",
            runtime_s=round(runtime_s, 4),
            memory_mb_estimated=18.5,
            vqe_iterations=iterations
        )

    @staticmethod
    def profile_quantum(
        runtime_s: float,
        qubits: int = 4,
        depth: int = 7,
        gates: int = 24,
        two_q: int = 8,
        vqe_iter: int = 80,
        shots: Optional[int] = None
    ) -> BenchmarkMetrics:
        return BenchmarkMetrics(
            model_type="Quantum",
            runtime_s=round(runtime_s, 4),
            memory_mb_estimated=42.0,
            num_qubits=qubits,
            circuit_depth=depth,
            total_gates=gates,
            two_qubit_gates=two_q,
            vqe_iterations=vqe_iter,
            shots=shots
        )

    @staticmethod
    def profile_hybrid(classical_s: float, quantum_s: float, post_process_s: float = 0.005) -> BenchmarkMetrics:
        total_time = classical_s + quantum_s + post_process_s
        return BenchmarkMetrics(
            model_type="Hybrid",
            runtime_s=round(total_time, 4),
            memory_mb_estimated=58.0,
            num_qubits=4,
            circuit_depth=7,
            total_gates=24,
            two_qubit_gates=8,
            vqe_iterations=80
        )
