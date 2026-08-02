"""Local, dependency-free factory process editor.

Run ``python -m asteria_digital_twin.web`` from the repository root and open
the printed local URL.  The editor reads the validated factory contract from
``configs/factory.yaml`` by default and exports contract-compatible JSON.
"""

from .server import asset_path, factory_payload, make_server

__all__ = ["asset_path", "factory_payload", "make_server"]
