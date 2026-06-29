"""Provider boundaries for hackathon integration adapters."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from .models import PaymentReceipt, ProcurementRequest, QuoteOption


@dataclass(frozen=True)
class ProcurementPlan:
    provider: str
    model: str
    summary: str
    risk_tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SafetyDecision:
    provider: str
    policy: str
    allowed: bool
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillDescriptor:
    id: str
    name: str
    provider: str
    description: str
    tags: tuple[str, ...] = ()

    def to_agent_card(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "description": self.description,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class ProvisioningReceipt:
    provider: str
    resource_id: str
    onboarding_url: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)


class RuntimeProvider(Protocol):
    provider_name: str

    def plan_procurement(self, request: ProcurementRequest) -> ProcurementPlan:
        """Plan the procurement request before quote and payment."""


class SafetyProvider(Protocol):
    provider_name: str

    def evaluate_procurement(
        self,
        *,
        request: ProcurementRequest,
        plan: ProcurementPlan,
    ) -> SafetyDecision:
        """Allow or deny a procurement before payment."""


class AgentSkillsProvider(Protocol):
    provider_name: str

    def list_skills(self) -> list[SkillDescriptor]:
        """Return skills advertised by this procurement desk."""


class ProvisioningProvider(Protocol):
    provider_name: str

    def provision(
        self,
        *,
        buyer_agent: str,
        quote: QuoteOption,
        payment: PaymentReceipt,
    ) -> ProvisioningReceipt:
        """Provision capacity after successful payment."""


class LocalRuntimeProvider:
    """Credential-free planner used by the demo."""

    provider_name = "local_runtime"
    model_name = "deterministic_procurement_rules"

    def plan_procurement(self, request: ProcurementRequest) -> ProcurementPlan:
        return ProcurementPlan(
            provider=self.provider_name,
            model=self.model_name,
            summary=(
                f"Plan {request.quantity} {request.gpu_model.upper()} GPUs for "
                f"{request.hours} hours in {request.region} under ${request.max_budget_usd:,.2f}."
            ),
            risk_tags=("budget_controlled", "gpu_capacity"),
            metadata={"workload": request.workload},
        )


class LocalSafetyProvider:
    """Small local policy gate used until an external safety provider is wired."""

    provider_name = "local_safety"
    policy_name = "procurement_allowlist_v1"

    def evaluate_procurement(
        self,
        *,
        request: ProcurementRequest,
        plan: ProcurementPlan,
    ) -> SafetyDecision:
        if request.quantity <= 0 or request.hours <= 0:
            return SafetyDecision(
                provider=self.provider_name,
                policy=self.policy_name,
                allowed=False,
                reason="quantity and hours must be positive",
                metadata={"planner": plan.provider},
            )

        return SafetyDecision(
            provider=self.provider_name,
            policy=self.policy_name,
            allowed=True,
            reason="request satisfies local procurement policy",
            metadata={"planner": plan.provider},
        )


class StaticAgentSkillsProvider:
    """Static skill registry advertised by the demo agent card."""

    provider_name = "local_static_skills"

    def list_skills(self) -> list[SkillDescriptor]:
        return [
            SkillDescriptor(
                id="trusted_gpu_procurement",
                name="Trusted GPU Procurement",
                provider=self.provider_name,
                description="Quote, authorize, pay for, and provision GPU capacity.",
                tags=("gpu", "procurement", "stripe", "agentid", "a2a"),
            ),
            SkillDescriptor(
                id="agent_passport_verification",
                name="Agent Passport Verification",
                provider=self.provider_name,
                description="Verify Ed25519 agent passports and required capabilities.",
                tags=("identity", "did", "ed25519", "capabilities"),
            ),
        ]


class MockCloudForgeProvisioningProvider:
    """Deterministic provisioning receipt used by the demo."""

    provider_name = "cloudforge_mock_provisioning"

    def provision(
        self,
        *,
        buyer_agent: str,
        quote: QuoteOption,
        payment: PaymentReceipt,
    ) -> ProvisioningReceipt:
        resource_id = "gpu-" + hashlib.sha256(
            f"{buyer_agent}:{quote.sku}:{payment.payment_id}".encode()
        ).hexdigest()[:12]
        return ProvisioningReceipt(
            provider=self.provider_name,
            resource_id=resource_id,
            onboarding_url=f"https://cloudforge.example/onboarding/{resource_id}",
            status="provisioned",
            metadata={"region": quote.region, "sku": quote.sku},
        )


class Nemotron3UltraPlanner:
    """Placeholder adapter for an NVIDIA Nemotron 3 Ultra planning runtime.

    This class names the integration point without shipping a fake API call.
    Wire the actual NVIDIA client or HTTP call inside plan_procurement once the
    hackathon runtime contract is available.
    """

    provider_name = "nvidia_nemotron_3_ultra_placeholder"

    def __init__(self, *, endpoint: str, api_key: str, model: str = "nemotron-3-ultra"):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model

    @classmethod
    def from_env(cls) -> "Nemotron3UltraPlanner":
        endpoint = _require_env("NVIDIA_NEMOTRON_ENDPOINT")
        api_key = _require_env("NVIDIA_API_KEY")
        model = os.getenv("NVIDIA_NEMOTRON_MODEL", "nemotron-3-ultra")
        return cls(endpoint=endpoint, api_key=api_key, model=model)

    def plan_procurement(self, request: ProcurementRequest) -> ProcurementPlan:
        raise RuntimeError(
            "Nemotron3UltraPlanner is a placeholder. Wire the NVIDIA runtime client "
            "before enabling it in production."
        )


class NemoClawSafetyProvider:
    """Placeholder adapter for an NVIDIA NemoClaw policy/safety gate."""

    provider_name = "nvidia_nemoclaw_placeholder"

    def __init__(self, *, endpoint: str, api_key: str, policy_id: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.policy_id = policy_id

    @classmethod
    def from_env(cls) -> "NemoClawSafetyProvider":
        return cls(
            endpoint=_require_env("NVIDIA_NEMOCLAW_ENDPOINT"),
            api_key=_require_env("NVIDIA_API_KEY"),
            policy_id=_require_env("NVIDIA_NEMOCLAW_POLICY_ID"),
        )

    def evaluate_procurement(
        self,
        *,
        request: ProcurementRequest,
        plan: ProcurementPlan,
    ) -> SafetyDecision:
        raise RuntimeError(
            "NemoClawSafetyProvider is a placeholder. Wire the NVIDIA policy API "
            "before enabling it in production."
        )


class NvidiaAgentSkillsProvider:
    """Placeholder adapter for an external NVIDIA agent skills registry."""

    provider_name = "nvidia_agent_skills_placeholder"

    def __init__(self, *, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key

    @classmethod
    def from_env(cls) -> "NvidiaAgentSkillsProvider":
        return cls(
            endpoint=_require_env("NVIDIA_AGENT_SKILLS_ENDPOINT"),
            api_key=_require_env("NVIDIA_API_KEY"),
        )

    def list_skills(self) -> list[SkillDescriptor]:
        raise RuntimeError(
            "NvidiaAgentSkillsProvider is a placeholder. Wire the NVIDIA skills "
            "registry client before advertising external skills."
        )


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
