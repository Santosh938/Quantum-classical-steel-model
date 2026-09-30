"""Pipeline orchestration, manifest tracking, and CLI interface."""

from .manifest import ExperimentManifest, create_experiment_manifest
from .cli import main

__all__ = ["ExperimentManifest", "create_experiment_manifest", "main"]
