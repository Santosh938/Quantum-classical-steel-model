"""Experiment manifest recording complete execution parameters and runtime provenance."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ExperimentManifest(BaseModel):
    """Reproducible record of experiment execution."""
    experiment_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    material: str = "AISI 4140"
    composition: Dict[str, float]
    heat_treatment: str
    thermal_history_source: str
    model_version: str = "0.1.0"
    parameter_version: str = "2026.1"
    random_seed: int = 42

    # Environment versions
    python_version: str
    numpy_version: str
    scipy_version: str
    qiskit_version: Optional[str] = None
    qiskit_aer_version: Optional[str] = None

    # Quantum configuration
    backend: str = "statevector_simulator"
    qubits: int = 4
    ansatz: str = "hardware_efficient_real_amplitudes"
    optimizer: str = "COBYLA"
    shots: Optional[int] = None
    noise_model: Optional[str] = None

    git_commit: str = "HEAD"
    results_summary: Dict[str, Any] = Field(default_factory=dict)


def create_experiment_manifest(
    experiment_id: str,
    composition: Dict[str, float],
    heat_treatment: str,
    thermal_history_source: str,
    random_seed: int = 42,
    results_summary: Optional[Dict[str, Any]] = None,
    backend: str = "statevector_simulator",
    qubits: int = 4,
    ansatz: str = "hardware_efficient_real_amplitudes",
    optimizer: str = "COBYLA",
    shots: Optional[int] = None,
    noise_model: Optional[str] = None
) -> ExperimentManifest:
    """Instantiate complete reproducible ExperimentManifest."""
    import numpy as np
    import scipy as sp

    qiskit_ver = None
    aer_ver = None
    try:
        import qiskit
        qiskit_ver = qiskit.__version__
    except ImportError:
        pass

    try:
        import qiskit_aer
        aer_ver = qiskit_aer.__version__
    except ImportError:
        pass

    return ExperimentManifest(
        experiment_id=experiment_id,
        material="AISI 4140",
        composition=composition,
        heat_treatment=heat_treatment,
        thermal_history_source=thermal_history_source,
        random_seed=random_seed,
        python_version=sys.version.split()[0],
        numpy_version=np.__version__,
        scipy_version=sp.__version__,
        qiskit_version=qiskit_ver,
        qiskit_aer_version=aer_ver,
        backend=backend,
        qubits=qubits,
        ansatz=ansatz,
        optimizer=optimizer,
        shots=shots,
        noise_model=noise_model,
        results_summary=results_summary or {}
    )


def save_manifest(manifest: ExperimentManifest, out_path: Path) -> None:
    """Save manifest to JSON file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2)
