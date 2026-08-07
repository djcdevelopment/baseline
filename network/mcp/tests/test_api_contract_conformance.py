"""Architecture regression: contracts/api-contract.json must describe this code.

PD-8 nominates the contract file as the formal boundary between `isolate` and
`baseline` — the artifact a consumer reads instead of the implementation. On
2026-08-07 it did not describe the implementation sitting beside it: /healthz
was declared to return `status`, but returns `ok`/`gateway`; /identity was
declared to return `port`, but returns `listen_port`/`published_port`; and the
transport section named 8721 as the default port, which is a host publish choice
belonging to a different repository's container.

None of that was caught, because nothing read the file. A boundary artifact that
no test reads is documentation, and documentation drifts. So this drives the real
routes and compares them against the declarations.

It asserts in BOTH directions on purpose. Checking only that declared fields are
present lets the response grow silently until the contract describes a subset of
reality — which is the same failure, arriving later and quieter.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any

from starlette.testclient import TestClient

from comfy_gateway.kernel.gateway import DEFAULT_PORT, build_server

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = REPO_ROOT / "network/mcp/contracts/api-contract.json"

# Maps the JSON Schema type names this contract uses onto Python types. bool is
# checked before int deliberately: bool is a subclass of int in Python, so an
# `ok: true` would otherwise satisfy a declared `integer`.
_JSON_TYPES: dict[str, Any] = {
    "null": type(None),
    "boolean": bool,
    "string": str,
    "integer": int,
    "number": (int, float),
    "array": list,
    "object": dict,
}


def _matches(value: Any, declared: Any) -> bool:
    names = declared if isinstance(declared, list) else [declared]
    for name in names:
        expected = _JSON_TYPES[name]
        if name == "integer" and isinstance(value, bool):
            continue
        if name != "boolean" and isinstance(value, bool) and expected is not bool:
            continue
        if isinstance(value, expected):
            return True
    return False


class ApiContractConformanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        cls.key = cls.contract["transport"]["accepted_keys"][0]
        (root / "callers.json").write_text(
            json.dumps({cls.key: {"id": "contract-test", "runner_class": "human", "node": "omen"}}),
            encoding="utf-8",
        )
        # No providers: the contract covers the kernel's own HTTP surface, and a
        # toolsurface import would drag host telemetry paths into a unit test.
        server = build_server(
            providers_spec="",
            callers_path=root / "callers.json",
            ledger_dir=root / "ledger",
        )
        cls.client = TestClient(server.streamable_http_app())
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)
        cls._tmp.cleanup()

    def _endpoint(self, path: str) -> dict:
        for endpoint in self.contract["endpoints"]:
            if endpoint["path"] == path:
                return endpoint
        self.fail(f"contract declares no endpoint {path}")

    def _conforms(self, path: str, payload: dict) -> None:
        schema = self._endpoint(path)["response"]["schema"]
        declared = schema["properties"]

        missing = sorted(set(schema["required"]) - set(payload))
        self.assertEqual(
            [], missing, f"{path} response is missing contract-required fields: {missing}"
        )

        undeclared = sorted(set(payload) - set(declared))
        self.assertEqual(
            [],
            undeclared,
            f"{path} returns fields the contract does not declare: {undeclared}. "
            "Add them to contracts/api-contract.json — a contract that describes "
            "a subset of the response has already stopped being a boundary.",
        )

        for field, value in payload.items():
            self.assertTrue(
                _matches(value, declared[field]["type"]),
                f"{path}.{field} is {type(value).__name__}, contract declares "
                f"{declared[field]['type']}",
            )

    def test_transport_default_port_matches_the_kernel(self) -> None:
        """The declared default must be the port the server actually listens on.

        Host publish ports (8721 companion, 8722 isolate lab) are deployment
        choices and must not be written here as protocol defaults.
        """
        self.assertEqual(DEFAULT_PORT, self.contract["transport"]["default_port"])

    def test_healthz_conforms(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(200, response.status_code)
        self._conforms("/healthz", response.json())

    def test_identity_conforms(self) -> None:
        response = self.client.get(
            "/identity", headers={self.contract["transport"]["auth_header"]: self.key}
        )
        self.assertEqual(200, response.status_code)
        self._conforms("/identity", response.json())

    def test_identity_requires_the_declared_auth_header(self) -> None:
        """auth_required is a claim about behaviour, so verify the behaviour.

        /identity exposes local filesystem and provenance detail; an unauthenticated
        read of it would leak the runtime's layout to anything that can reach the
        loopback port.
        """
        self.assertTrue(self._endpoint("/identity")["auth_required"])
        response = self.client.get("/identity")
        self.assertEqual(
            self.contract["transport"]["unauthorized_status"], response.status_code
        )

    def test_healthz_is_reachable_without_auth(self) -> None:
        """Liveness must not require a key, or a probe cannot distinguish
        'down' from 'running but unauthorized'."""
        self.assertFalse(self._endpoint("/healthz")["auth_required"])
        self.assertEqual(200, self.client.get("/healthz").status_code)

    def test_identity_project_is_supplied_not_assumed(self) -> None:
        """The field the whole boundary rests on, asserted through the real route.

        Both repositories build this kernel from the same Dockerfile and both
        report source_root /workspace, so a hardcoded project made /identity
        unable to name which one answered.
        """
        header = {self.contract["transport"]["auth_header"]: self.key}
        previous = os.environ.get("COMFY_MCP_PROJECT")
        try:
            os.environ["COMFY_MCP_PROJECT"] = "isolate"
            self.assertEqual(
                "isolate", self.client.get("/identity", headers=header).json()["project"]
            )
            os.environ.pop("COMFY_MCP_PROJECT")
            self.assertEqual(
                "baseline", self.client.get("/identity", headers=header).json()["project"]
            )
        finally:
            if previous is None:
                os.environ.pop("COMFY_MCP_PROJECT", None)
            else:
                os.environ["COMFY_MCP_PROJECT"] = previous


if __name__ == "__main__":
    unittest.main()
