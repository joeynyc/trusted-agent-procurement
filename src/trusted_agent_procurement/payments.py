"""Stripe-compatible procurement payment providers."""

from __future__ import annotations

import os
import uuid
from typing import Protocol

from .models import PaymentReceipt, QuoteOption


class PaymentProvider(Protocol):
    def charge_procurement(self, *, buyer_agent: str, quote: QuoteOption) -> PaymentReceipt:
        """Charge for a selected procurement quote."""


class MockStripeProvider:
    """Deterministic test-mode provider with the same boundary as a Stripe adapter."""

    provider_name = "stripe_test_mock"

    def charge_procurement(self, *, buyer_agent: str, quote: QuoteOption) -> PaymentReceipt:
        payment_id = "pi_test_" + uuid.uuid4().hex[:24]
        hosted_url = f"https://dashboard.stripe.com/test/payments/{payment_id}"
        return PaymentReceipt(
            provider=self.provider_name,
            payment_id=payment_id,
            amount_usd=quote.total_usd,
            status="succeeded",
            hosted_url=hosted_url,
        )


class StripeProvider:
    """Upgrade path for real Stripe test-mode usage.

    The hackathon demo defaults to MockStripeProvider so it runs without
    credentials. Replace the provider with this adapter after installing
    stripe and setting STRIPE_SECRET_KEY.
    """

    provider_name = "stripe"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def charge_procurement(self, *, buyer_agent: str, quote: QuoteOption) -> PaymentReceipt:
        try:
            import stripe
        except ImportError as exc:
            raise RuntimeError("Install stripe to use StripeProvider") from exc

        stripe.api_key = self.api_key
        intent = stripe.PaymentIntent.create(
            amount=int(round(quote.total_usd * 100)),
            currency="usd",
            automatic_payment_methods={"enabled": True},
            metadata={
                "buyer_agent": buyer_agent,
                "sku": quote.sku,
                "gpu_model": quote.gpu_model,
                "quantity": str(quote.quantity),
                "hours": str(quote.hours),
            },
        )
        return PaymentReceipt(
            provider=self.provider_name,
            payment_id=intent.id,
            amount_usd=quote.total_usd,
            status=intent.status,
            hosted_url=None,
        )


class HermesStripeSkillsProvider:
    """Placeholder for a Hermes Stripe Skills payment/provisioning adapter.

    The public demo keeps using MockStripeProvider. Once the Hermes Stripe
    Skills contract is available, wire the SDK or HTTP client inside
    charge_procurement and keep this class behind explicit configuration.
    """

    provider_name = "hermes_stripe_skills_placeholder"

    def __init__(self, *, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key

    @classmethod
    def from_env(cls) -> "HermesStripeSkillsProvider":
        endpoint = os.getenv("HERMES_STRIPE_SKILLS_ENDPOINT")
        api_key = os.getenv("HERMES_STRIPE_SKILLS_API_KEY")
        if not endpoint:
            raise RuntimeError("Missing required environment variable: HERMES_STRIPE_SKILLS_ENDPOINT")
        if not api_key:
            raise RuntimeError("Missing required environment variable: HERMES_STRIPE_SKILLS_API_KEY")
        return cls(endpoint=endpoint, api_key=api_key)

    def charge_procurement(self, *, buyer_agent: str, quote: QuoteOption) -> PaymentReceipt:
        raise RuntimeError(
            "HermesStripeSkillsProvider is a placeholder. Wire Hermes Stripe Skills "
            "before enabling it in production."
        )
