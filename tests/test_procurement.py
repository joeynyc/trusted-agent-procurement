import pytest

from trusted_agent_procurement.cloudforge import CloudForgeProcurementDesk, ProcurementDenied
from trusted_agent_procurement.identity import DemoPassportIssuer
from trusted_agent_procurement.models import ProcurementRequest


def _request(max_budget_usd: float = 5000) -> ProcurementRequest:
    return ProcurementRequest(
        buyer_agent="nexus-buyer-agent",
        workload="fine-tuning run",
        gpu_model="H100",
        quantity=8,
        hours=72,
        max_budget_usd=max_budget_usd,
    )


def _passport(capabilities: list[str]) -> str:
    return DemoPassportIssuer.create().issue_passport(
        name="Nexus Buyer Agent",
        capabilities=capabilities,
    )


def test_successful_procurement_verifies_identity_pays_and_provisions():
    desk = CloudForgeProcurementDesk()
    token = _passport(["purchase:gpu", "vendor:cloudforge", "contract:sign", "budget:5000"])

    result = desk.procure(passport_token=token, request=_request())

    assert result.payment.status == "succeeded"
    assert result.payment.provider == "stripe_test_mock"
    assert result.selected_quote.total_usd == 2390.40
    assert result.provisioned_resource_id.startswith("gpu-")
    assert [event["event"] for event in result.audit_log] == [
        "a2a_request_received",
        "passport_verified",
        "capabilities_authorized",
        "budget_authorized",
        "quote_generated",
        "stripe_payment_triggered",
        "resource_provisioned",
    ]


def test_missing_capability_blocks_procurement():
    desk = CloudForgeProcurementDesk()
    token = _passport(["purchase:gpu", "vendor:cloudforge", "budget:5000"])

    with pytest.raises(ProcurementDenied, match="contract:sign"):
        desk.procure(passport_token=token, request=_request())


def test_request_budget_cannot_exceed_passport_budget():
    desk = CloudForgeProcurementDesk()
    token = _passport(["purchase:gpu", "vendor:cloudforge", "contract:sign", "budget:2000"])

    with pytest.raises(ProcurementDenied, match="exceeds passport budget"):
        desk.procure(passport_token=token, request=_request(max_budget_usd=5000))


def test_quote_cannot_exceed_request_budget():
    desk = CloudForgeProcurementDesk()
    token = _passport(["purchase:gpu", "vendor:cloudforge", "contract:sign", "budget:5000"])

    with pytest.raises(ProcurementDenied, match="exceeds request budget"):
        desk.procure(passport_token=token, request=_request(max_budget_usd=2000))
