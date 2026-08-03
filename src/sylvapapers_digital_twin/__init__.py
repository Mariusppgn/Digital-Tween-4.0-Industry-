"""Executable paper-mill digital twin for SylvaPapers."""

from .campaign import (
    CampaignConfig,
    CampaignResult,
    load_campaign_config,
    materialize_scenario,
    run_campaign,
    save_campaign,
)
from .exchange import prepare_exchange_bundle
from .graph import build_process_graph
from .kpi import KPI_NAMES, calculate_kpis
from .reporting import generate_markdown_report, generate_plots, save_result
from .simulator import DigitalTwinSimulator, SimulationResult, simulate

__all__ = [
    "KPI_NAMES",
    "CampaignConfig",
    "CampaignResult",
    "DigitalTwinSimulator",
    "SimulationResult",
    "build_process_graph",
    "calculate_kpis",
    "generate_markdown_report",
    "generate_plots",
    "load_campaign_config",
    "materialize_scenario",
    "prepare_exchange_bundle",
    "run_campaign",
    "save_campaign",
    "save_result",
    "simulate",
]
