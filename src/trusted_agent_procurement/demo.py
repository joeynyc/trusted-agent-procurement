"""Video-friendly end-to-end demo."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict

from .cloudforge import CloudForgeProcurementDesk
from .identity import DemoPassportIssuer
from .models import ProcurementRequest


def _print_step(title: str, body: str = "") -> None:
    print()
    print(f"== {title} ==")
    if body:
        print(body)


def _sleep(fast: bool) -> None:
    if not fast:
        time.sleep(0.8)


def run_demo(*, fast: bool = False) -> dict:
    _print_step(
        "Trusted Agent Procurement",
        "Buyer agent verifies identity, negotiates GPU capacity, pays, and receives provisioning.",
    )
    _sleep(fast)

    issuer = DemoPassportIssuer.create()
    passport = issuer.issue_passport(
        name="Nexus Buyer Agent",
        capabilities=[
            "purchase:gpu",
            "vendor:cloudforge",
            "contract:sign",
            "budget:5000",
        ],
    )
    _print_step(
        "1. Buyer agent presents AgentPassport",
        "Capabilities: purchase:gpu, vendor:cloudforge, contract:sign, budget:5000",
    )
    _sleep(fast)

    desk = CloudForgeProcurementDesk()
    _print_step("2. CloudForge publishes A2A agent card")
    print(json.dumps(desk.agent_card(), indent=2))
    _sleep(fast)

    request = ProcurementRequest(
        buyer_agent="nexus-buyer-agent",
        workload="72-hour fine-tuning run for a customer support model",
        gpu_model="H100",
        quantity=8,
        hours=72,
        max_budget_usd=5000,
        region="us-east-1",
    )
    quote = desk.quote(request)
    _print_step("3. CloudForge returns procurement quote")
    print(json.dumps(asdict(quote), indent=2))
    _sleep(fast)

    result = desk.procure(passport_token=passport, request=request)
    _print_step("4. Stripe test-mode payment and provisioning complete")
    print(json.dumps({
        "payment": asdict(result.payment),
        "resource_id": result.provisioned_resource_id,
        "onboarding_url": result.onboarding_url,
    }, indent=2))
    _sleep(fast)

    _print_step("5. Audit log")
    for event in result.audit_log:
        print(f"- {event['event']}: " + json.dumps({k: v for k, v in event.items() if k not in {'event', 'timestamp'}}))

    _print_step("Demo complete", "Autonomous procurement finished with identity, budget, payment, and audit evidence.")
    return {
        "verified_did": result.verified_did,
        "payment_id": result.payment.payment_id,
        "resource_id": result.provisioned_resource_id,
        "audit_events": [event["event"] for event in result.audit_log],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Trusted Agent Procurement demo.")
    parser.add_argument("--fast", action="store_true", help="Skip presentation delays.")
    args = parser.parse_args()
    run_demo(fast=args.fast)


if __name__ == "__main__":
    main()
