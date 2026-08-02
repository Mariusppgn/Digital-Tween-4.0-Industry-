"""Small standard-library HTTP server for the factory process editor."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit

import yaml

from asteria_contracts import FactoryConfig, load_factory_config

EDITOR_ROOT: Final = Path(__file__).resolve().parent
ASSETS: Final = {
    "/": ("editor.html", "text/html; charset=utf-8"),
    "/editor.html": ("editor.html", "text/html; charset=utf-8"),
    "/factory-editor.css": ("factory-editor.css", "text/css; charset=utf-8"),
    "/factory-editor.js": ("factory-editor.js", "text/javascript; charset=utf-8"),
}


def asset_path(name: str) -> Path:
    """Return one known editor asset without accepting arbitrary paths."""

    known = {asset_name for asset_name, _ in ASSETS.values()}
    if name not in known:
        raise ValueError(f"unknown factory editor asset: {name}")
    return EDITOR_ROOT / name


def factory_payload(config_path: str | Path) -> dict[str, object]:
    """Load and validate a factory file, then make it JSON-ready for the editor."""

    factory: FactoryConfig = load_factory_config(config_path)
    return factory.model_dump(mode="json", exclude_none=True)


def _handler(config_path: Path) -> type[BaseHTTPRequestHandler]:
    class FactoryEditorHandler(BaseHTTPRequestHandler):
        server_version = "SylvaPapersFactoryEditor/1.0"

        def do_GET(self) -> None:
            request_path = urlsplit(self.path).path
            if request_path == "/factory.json":
                try:
                    body = json.dumps(
                        factory_payload(config_path), ensure_ascii=False, indent=2
                    ).encode("utf-8")
                except (OSError, ValueError) as error:
                    self._send(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"),
                        "application/json; charset=utf-8",
                    )
                    return
                self._send(HTTPStatus.OK, body, "application/json; charset=utf-8")
                return

            asset = ASSETS.get(request_path)
            if asset is None:
                self._send(HTTPStatus.NOT_FOUND, b"Not found\n", "text/plain; charset=utf-8")
                return
            filename, content_type = asset
            self._send(HTTPStatus.OK, asset_path(filename).read_bytes(), content_type)

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/factory.json":
                self._send(HTTPStatus.NOT_FOUND, b"Not found\n", "text/plain; charset=utf-8")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                if not 0 < content_length <= 2_000_000:
                    raise ValueError("factory payload must contain between 1 byte and 2 MB")
                raw_payload = json.loads(self.rfile.read(content_length))
                factory = FactoryConfig.model_validate(raw_payload)
                payload = factory.model_dump(mode="json", exclude_none=True)
                if config_path.suffix.lower() == ".json":
                    serialised = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
                elif config_path.suffix.lower() in {".yaml", ".yml"}:
                    serialised = yaml.safe_dump(
                        payload, allow_unicode=True, sort_keys=False, default_flow_style=False
                    )
                else:
                    raise ValueError(f"unsupported contract format: {config_path.suffix}")
                temporary = config_path.with_suffix(config_path.suffix + ".editor-tmp")
                temporary.write_text(serialised, encoding="utf-8")
                temporary.replace(config_path)
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
                return
            body = json.dumps({"written": True, "path": config_path.name}).encode("utf-8")
            self._send(HTTPStatus.OK, body, "application/json; charset=utf-8")

        def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    return FactoryEditorHandler


def make_server(
    config_path: str | Path,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ThreadingHTTPServer:
    """Build a local editor server. A port of zero asks the OS for a free port."""

    source = Path(config_path).resolve()
    factory_payload(source)
    return ThreadingHTTPServer((host, port), _handler(source))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the local SylvaPape factory editor")
    parser.add_argument("--config", default="configs/factory.yaml", help="Factory JSON/YAML file")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (local by default)")
    parser.add_argument("--port", type=int, default=8765, help="TCP port")
    args = parser.parse_args(argv)

    server = make_server(args.config, args.host, args.port)
    host, port = server.server_address[:2]
    display_host = host.decode() if isinstance(host, bytes) else host
    print(f"Factory editor: http://{display_host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
