from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from sylvapapers_contracts import FactoryConfig
from sylvapapers_digital_twin.web import asset_path, factory_payload, make_server

ROOT = Path(__file__).resolve().parents[1]


def test_factory_payload_is_contract_compatible_and_keeps_editor_positions() -> None:
    payload = factory_payload(ROOT / "configs" / "factory.yaml")
    factory = TypeAdapter(FactoryConfig).validate_python(payload)

    assert factory.name == "SylvaPapers Manufacture"
    assert factory.machine_types
    assert all(
        machine_type.failure_density.family == "weibull" for machine_type in factory.machine_types
    )
    assert all(node.position is not None for node in factory.process_graph.nodes)
    assert any(
        node.input_materials and node.output_materials for node in factory.process_graph.nodes
    )


@pytest.mark.parametrize(
    ("name", "marker"),
    [
        ("editor.html", 'id="graph-canvas"'),
        ("factory-editor.css", ".process-node"),
        ("factory-editor.js", "validateFactory"),
    ],
)
def test_editor_assets_are_available(name: str, marker: str) -> None:
    content = asset_path(name).read_text(encoding="utf-8")
    assert marker in content


def test_editor_uses_native_accessible_controls_and_json_interop() -> None:
    html = asset_path("editor.html").read_text(encoding="utf-8")
    script = asset_path("factory-editor.js").read_text(encoding="utf-8")

    assert "<button" in html
    assert '<link rel="stylesheet" href="factory-editor.css">' in html
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html
    assert 'type="file"' in html
    assert "pointerdown" in script
    assert "ArrowLeft" in script
    assert "JSON.stringify(state.factory" in script
    assert "process_graph.edges.push" in script
    assert "failure_density" in script
    assert "function undo()" in script
    assert "function autoLayout()" in script
    assert "function duplicateSelected()" in script
    assert "type-location" not in html


def test_local_server_serves_validated_factory_and_security_headers() -> None:
    server = make_server(ROOT / "configs" / "factory.yaml", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        connection = HTTPConnection(host, port, timeout=5)
        connection.request("GET", "/factory.json")
        response = connection.getresponse()
        payload = json.loads(response.read())
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]
        connection.close()
        FactoryConfig.model_validate(payload)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_asset_path_rejects_path_traversal() -> None:
    with pytest.raises(ValueError, match="unknown factory editor asset"):
        asset_path("../factory.yaml")
