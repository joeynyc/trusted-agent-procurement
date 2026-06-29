"""Domain models for trusted procurement."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class QuoteOption:
    sku: str
    label: str
    gpu_model: str
    quantity: int
    hours: int
    unit_price_usd: float
    total_usd: float
    region: str


@dataclass(frozen=True)
class ProcurementRequest:
    buyer_agent: str
    workload: str
    gpu_model: str
    quantity: int
    hours: int
    max_budget_usd: float
    region: str = "us-east-1"


@dataclass(frozen=True)
class PaymentReceipt:
    provider: str
    payment_id: str
    amount_usd: float
    status: str
    hosted_url: str | None = None


@dataclass(frozen=True)
class ProcurementResult:
    buyer_agent: str
    verified_did: str
    selected_quote: QuoteOption
    payment: PaymentReceipt
    provisioned_resource_id: str
    onboarding_url: str
    audit_log: list[dict[str, Any]]


@dataclass
class AuditLog:
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, event: str, **fields: Any) -> None:
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **fields,
        })
