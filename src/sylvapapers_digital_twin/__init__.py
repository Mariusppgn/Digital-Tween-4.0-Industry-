"""Executable paper-mill digital twin for SylvaPapers."""

from .graph import build_process_graph
from .kpi import KPI_NAMES, calculate_kpis
from .reporting import generate_markdown_report, generate_plots, save_result
from .simulator import DigitalTwinSimulator, SimulationResult, simulate

__all__ = [
    "KPI_NAMES",
    "DigitalTwinSimulator",
    "SimulationResult",
    "build_process_graph",
    "calculate_kpis",
    "generate_markdown_report",
    "generate_plots",
    "save_result",
    "simulate",
]
