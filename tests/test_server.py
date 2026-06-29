from starlette.testclient import TestClient

from trusted_agent_procurement.identity import DemoPassportIssuer
from trusted_agent_procurement.server import create_app


def _passport(capabilities: list[str] | None = None) -> str:
    return DemoPassportIssuer.create().issue_passport(
        name="Nexus Buyer Agent",
        capabilities=capabilities
        or ["purchase:gpu", "vendor:cloudforge", "contract:sign", "budget:5000"],
    )


def _request_payload(max_budget_usd: float = 5000) -> dict:
    return {
        "buyer_agent": "nexus-buyer-agent",
        "workload": "test procurement",
        "gpu_model": "H100",
        "quantity": 8,
        "hours": 72,
        "max_budget_usd": max_budget_usd,
        "region": "us-east-1",
    }


def test_health_and_agent_card_routes():
    client = TestClient(create_app())

    health = client.get("/health")
    card = client.get("/.well-known/agent-card.json")

    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert card.status_code == 200
    assert card.json()["name"] == "CloudForge Trusted Procurement Desk"


def test_rest_procure_route_accepts_agent_passport():
    client = TestClient(create_app())

    response = client.post(
        "/procure",
        headers={"Authorization": f"AgentPassport {_passport()}"},
        json=_request_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["payment"]["status"] == "succeeded"
    assert body["provisioned_resource_id"].startswith("gpu-")


def test_jsonrpc_procurement_route():
    client = TestClient(create_app())
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "procurement/procure",
            "params": {
                "passport": _passport(),
                "request": _request_payload(),
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == "test-1"
    assert body["result"]["payment"]["status"] == "succeeded"


def test_jsonrpc_rejects_missing_capability():
    client = TestClient(create_app())
    response = client.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "id": "test-2",
            "method": "procurement/procure",
            "params": {
                "passport": _passport(["purchase:gpu", "vendor:cloudforge", "budget:5000"]),
                "request": _request_payload(),
            },
        },
    )

    assert response.status_code == 403
    assert "contract:sign" in response.json()["error"]["message"]
