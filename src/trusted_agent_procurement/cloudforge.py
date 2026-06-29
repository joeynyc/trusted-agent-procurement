"""CloudForge trusted A2A procurement desk."""

from __future__ import annotations

import hashlib
from dataclasses import asdict

from agentid_verify import AgentIdError, PassportClaims, verify_passport

from .integrations import (
    AgentSkillsProvider,
    LocalRuntimeProvider,
    LocalSafetyProvider,
    MockCloudForgeProvisioningProvider,
    ProvisioningProvider,
    RuntimeProvider,
    SafetyProvider,
    StaticAgentSkillsProvider,
)
from .models import AuditLog, ProcurementRequest, ProcurementResult, QuoteOption
from .payments import MockStripeProvider, PaymentProvider

REQUIRED_CAPABILITIES = [
    "purchase:gpu",
    "vendor:cloudforge",
    "contract:sign",
]

GPU_PRICES = {
    "A100": 2.45,
    "H100": 4.15,
    "H200": 5.80,
    "B200": 8.50,
}

GPU_LABELS = {
    "A100": "NVIDIA A100 80GB",
    "H100": "NVIDIA H100 80GB SXM",
    "H200": "NVIDIA H200 141GB",
    "B200": "NVIDIA B200 192GB",
}


class ProcurementDenied(Exception):
    """Raised when an agent is not authorized to procure resources."""


class CloudForgeProcurementDesk:
    """Business-facing procurement desk adapted from the CloudForge A2A front desk."""

    def __init__(
        self,
        payment_provider: PaymentProvider | None = None,
        runtime_provider: RuntimeProvider | None = None,
        safety_provider: SafetyProvider | None = None,
        skills_provider: AgentSkillsProvider | None = None,
        provisioning_provider: ProvisioningProvider | None = None,
    ):
        self.payment_provider = payment_provider or MockStripeProvider()
        self.runtime_provider = runtime_provider or LocalRuntimeProvider()
        self.safety_provider = safety_provider or LocalSafetyProvider()
        self.skills_provider = skills_provider or StaticAgentSkillsProvider()
        self.provisioning_provider = provisioning_provider or MockCloudForgeProvisioningProvider()

    def agent_card(self) -> dict:
        """Return the A2A-style agent card advertised to buyer agents."""
        return {
            "name": "CloudForge Trusted Procurement Desk",
            "version": "0.1.0",
            "description": (
                "A2A procurement front desk for GPU cloud purchases. Verifies "
                "agent passports, enforces spend capabilities, accepts Stripe-style "
                "payments, and returns provisioning records."
            ),
            "protocol": "A2A JSON-RPC compatible",
            "capabilities": {"streaming": False},
            "supported_interfaces": [
                {
                    "protocol_binding": "JSONRPC",
                    "url": "http://127.0.0.1:9998/",
                }
            ],
            "skills": [skill.to_agent_card() for skill in self.skills_provider.list_skills()],
            "integration_status": self.integration_status(),
        }

    def integration_status(self) -> dict:
        """Return configured integration providers without claiming external services are live."""
        return {
            "payment_provider": getattr(self.payment_provider, "provider_name", type(self.payment_provider).__name__),
            "runtime_provider": self.runtime_provider.provider_name,
            "safety_provider": self.safety_provider.provider_name,
            "skills_provider": self.skills_provider.provider_name,
            "provisioning_provider": self.provisioning_provider.provider_name,
        }

    def quote(self, request: ProcurementRequest) -> QuoteOption:
        model = request.gpu_model.upper()
        if model not in GPU_PRICES:
            raise ValueError(f"unsupported GPU model: {request.gpu_model}")

        unit_price = GPU_PRICES[model]
        subtotal = unit_price * request.quantity * request.hours
        discount = self._volume_discount(request.quantity)
        total = round(subtotal * (1 - discount), 2)
        sku_seed = f"{model}:{request.quantity}:{request.hours}:{request.region}:{total}"
        sku = "cf-" + hashlib.sha256(sku_seed.encode()).hexdigest()[:10]
        label = f"{request.quantity}x {GPU_LABELS[model]} for {request.hours} hours"
        return QuoteOption(
            sku=sku,
            label=label,
            gpu_model=GPU_LABELS[model],
            quantity=request.quantity,
            hours=request.hours,
            unit_price_usd=unit_price,
            total_usd=total,
            region=request.region,
        )

    def procure(self, *, passport_token: str, request: ProcurementRequest) -> ProcurementResult:
        audit = AuditLog()
        audit.record("a2a_request_received", buyer_agent=request.buyer_agent, workload=request.workload)

        claims = self._verify_authority(passport_token, audit)
        self._require_capabilities(claims, audit)
        self._require_budget(claims, request.max_budget_usd, audit)

        plan = self.runtime_provider.plan_procurement(request)
        audit.record("runtime_plan_created", plan=asdict(plan))

        safety = self.safety_provider.evaluate_procurement(request=request, plan=plan)
        audit.record("safety_gate_evaluated", decision=asdict(safety))
        if not safety.allowed:
            audit.record("procurement_denied", reason="safety_gate_denied", detail=safety.reason)
            raise ProcurementDenied(f"safety gate denied procurement: {safety.reason}")

        quote = self.quote(request)
        audit.record("quote_generated", quote=asdict(quote))

        if quote.total_usd > request.max_budget_usd:
            audit.record(
                "procurement_denied",
                reason="quote_exceeds_request_budget",
                quote_total_usd=quote.total_usd,
                max_budget_usd=request.max_budget_usd,
            )
            raise ProcurementDenied(
                f"quote ${quote.total_usd:,.2f} exceeds request budget ${request.max_budget_usd:,.2f}"
            )

        payment = self.payment_provider.charge_procurement(
            buyer_agent=request.buyer_agent,
            quote=quote,
        )
        audit.record("stripe_payment_triggered", payment=asdict(payment))

        provisioning = self.provisioning_provider.provision(
            buyer_agent=request.buyer_agent,
            quote=quote,
            payment=payment,
        )
        audit.record(
            "resource_provisioned",
            provisioning=asdict(provisioning),
        )

        return ProcurementResult(
            buyer_agent=request.buyer_agent,
            verified_did=claims.sub,
            selected_quote=quote,
            payment=payment,
            provisioned_resource_id=provisioning.resource_id,
            onboarding_url=provisioning.onboarding_url,
            audit_log=audit.events,
        )

    def _verify_authority(self, passport_token: str, audit: AuditLog) -> PassportClaims:
        try:
            claims = verify_passport(passport_token)
        except AgentIdError as exc:
            audit.record("passport_rejected", reason=str(exc))
            raise ProcurementDenied(f"invalid AgentPassport: {exc}") from exc

        audit.record(
            "passport_verified",
            agent_name=claims.name,
            subject=claims.sub,
            issuer=claims.iss,
            capabilities=claims.capabilities,
        )
        return claims

    def _require_capabilities(self, claims: PassportClaims, audit: AuditLog) -> None:
        missing = [capability for capability in REQUIRED_CAPABILITIES if not claims.has_capability(capability)]
        if missing:
            audit.record("procurement_denied", reason="missing_capabilities", missing=missing)
            raise ProcurementDenied("missing required capabilities: " + ", ".join(missing))
        audit.record("capabilities_authorized", required=REQUIRED_CAPABILITIES)

    def _require_budget(self, claims: PassportClaims, requested_budget: float, audit: AuditLog) -> None:
        passport_budget = _extract_budget(claims.capabilities)
        if passport_budget is None:
            audit.record("procurement_denied", reason="missing_budget_capability")
            raise ProcurementDenied("missing budget capability, expected budget:<amount>")

        if requested_budget > passport_budget:
            audit.record(
                "procurement_denied",
                reason="request_budget_exceeds_passport_budget",
                requested_budget_usd=requested_budget,
                passport_budget_usd=passport_budget,
            )
            raise ProcurementDenied(
                f"request budget ${requested_budget:,.2f} exceeds passport budget ${passport_budget:,.2f}"
            )
        audit.record("budget_authorized", passport_budget_usd=passport_budget, request_budget_usd=requested_budget)

    @staticmethod
    def _volume_discount(quantity: int) -> float:
        if quantity >= 100:
            return 0.25
        if quantity >= 50:
            return 0.18
        if quantity >= 10:
            return 0.10
        return 0.0


def _extract_budget(capabilities: list[str]) -> float | None:
    for capability in capabilities:
        if capability.startswith("budget:"):
            try:
                return float(capability.split(":", 1)[1])
            except ValueError:
                return None
    return None
