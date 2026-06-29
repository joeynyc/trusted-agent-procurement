import pytest

from trusted_agent_procurement.cloudforge import CloudForgeProcurementDesk, ProcurementDenied
from trusted_agent_procurement.identity import DemoPassportIssuer
from trusted_agent_procurement.integrations import (
    LocalRuntimeProvider,
    LocalSafetyProvider,
    NemoClawSafetyProvider,
    Nemotron3UltraPlanner,
    NvidiaAgentSkillsProvider,
)
from trusted_agent_procurement.models import ProcurementRequest
from trusted_agent_procurement.payments import HermesStripeSkillsProvider


def _request(quantity: int = 8, hours: int = 72) -> ProcurementRequest:
    return ProcurementRequest(
        buyer_agent="nexus-buyer-agent",
        workload="fine-tuning run",
        gpu_model="H100",
        quantity=quantity,
        hours=hours,
        max_budget_usd=5000,
    )


def _passport() -> str:
    return DemoPassportIssuer.create().issue_passport(
        name="Nexus Buyer Agent",
        capabilities=["purchase:gpu", "vendor:cloudforge", "contract:sign", "budget:5000"],
    )


def test_agent_card_exposes_configured_integration_status():
    card = CloudForgeProcurementDesk().agent_card()

    assert card["integration_status"] == {
        "payment_provider": "stripe_test_mock",
        "runtime_provider": "local_runtime",
        "safety_provider": "local_safety",
        "skills_provider": "local_static_skills",
        "provisioning_provider": "cloudforge_mock_provisioning",
    }
    assert card["skills"][0]["provider"] == "local_static_skills"


def test_local_safety_provider_can_deny_before_payment():
    desk = CloudForgeProcurementDesk()

    with pytest.raises(ProcurementDenied, match="quantity and hours must be positive"):
        desk.procure(passport_token=_passport(), request=_request(quantity=0))


def test_placeholder_adapters_require_explicit_configuration(monkeypatch):
    for name in [
        "HERMES_STRIPE_SKILLS_ENDPOINT",
        "HERMES_STRIPE_SKILLS_API_KEY",
        "NVIDIA_NEMOTRON_ENDPOINT",
        "NVIDIA_NEMOCLAW_ENDPOINT",
        "NVIDIA_NEMOCLAW_POLICY_ID",
        "NVIDIA_AGENT_SKILLS_ENDPOINT",
        "NVIDIA_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="HERMES_STRIPE_SKILLS_ENDPOINT"):
        HermesStripeSkillsProvider.from_env()

    with pytest.raises(RuntimeError, match="NVIDIA_NEMOTRON_ENDPOINT"):
        Nemotron3UltraPlanner.from_env()

    with pytest.raises(RuntimeError, match="NVIDIA_NEMOCLAW_ENDPOINT"):
        NemoClawSafetyProvider.from_env()

    with pytest.raises(RuntimeError, match="NVIDIA_AGENT_SKILLS_ENDPOINT"):
        NvidiaAgentSkillsProvider.from_env()


def test_placeholder_adapters_do_not_fake_external_calls(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    monkeypatch.setenv("NVIDIA_NEMOTRON_ENDPOINT", "https://example.test/nemotron")
    monkeypatch.setenv("NVIDIA_NEMOCLAW_ENDPOINT", "https://example.test/nemoclaw")
    monkeypatch.setenv("NVIDIA_NEMOCLAW_POLICY_ID", "policy-test")
    monkeypatch.setenv("NVIDIA_AGENT_SKILLS_ENDPOINT", "https://example.test/skills")
    monkeypatch.setenv("HERMES_STRIPE_SKILLS_ENDPOINT", "https://example.test/stripe-skills")
    monkeypatch.setenv("HERMES_STRIPE_SKILLS_API_KEY", "test-key")

    planner = Nemotron3UltraPlanner.from_env()
    safety = NemoClawSafetyProvider.from_env()
    skills = NvidiaAgentSkillsProvider.from_env()
    payment = HermesStripeSkillsProvider.from_env()
    local_plan = LocalRuntimeProvider().plan_procurement(_request())
    quote = CloudForgeProcurementDesk().quote(_request())

    with pytest.raises(RuntimeError, match="placeholder"):
        planner.plan_procurement(_request())

    with pytest.raises(RuntimeError, match="placeholder"):
        safety.evaluate_procurement(request=_request(), plan=local_plan)

    with pytest.raises(RuntimeError, match="placeholder"):
        skills.list_skills()

    with pytest.raises(RuntimeError, match="placeholder"):
        payment.charge_procurement(buyer_agent="nexus-buyer-agent", quote=quote)


def test_local_runtime_and_safety_are_credential_free():
    request = _request()
    plan = LocalRuntimeProvider().plan_procurement(request)
    decision = LocalSafetyProvider().evaluate_procurement(request=request, plan=plan)

    assert plan.provider == "local_runtime"
    assert "H100" in plan.summary
    assert decision.allowed is True
