"""Pytest configuration ensuring headless matplotlib Agg backend."""

import matplotlib
matplotlib.use("Agg")
