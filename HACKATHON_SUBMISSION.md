# Hackathon Submission

## One-Line Pitch

Trusted Agent Procurement lets autonomous business agents buy GPU capacity with identity, delegated authority, budget controls, payment, provisioning, and an audit trail.

## Why This Should Place

Most agent demos stop at task execution. This project tackles the operational layer agents need before they can run real businesses: who is calling, who authorized spend, what the agent can buy, how payment happens, and what evidence is left behind.

The demo is intentionally narrow and complete. A buyer agent presents an `AgentPassport`, CloudForge verifies identity and spend authority, a runtime provider creates a procurement plan, a safety provider gates the request, CloudForge quotes H100 capacity, a Stripe-shaped payment is recorded, provisioning is returned, and every step lands in the audit log.

## What Is Working Now

- Signed `AgentPassport` issuance and verification with Ed25519 DID keys.
- A2A-style CloudForge procurement desk with JSON-RPC and REST endpoints.
- Capability and budget enforcement before quote or payment.
- Runtime planning and safety gating through provider interfaces.
- Stripe-shaped mock payment receipts with a real `StripeProvider` upgrade path.
- Deterministic provisioning receipts and onboarding URLs.
- Agent card advertising skills and configured integration status.
- Tests and a one-command smoke demo.

## Integration Honesty

The default demo is credential-free. It does not claim live NVIDIA, Hermes, or Stripe production integration.

The repo includes explicit adapter placeholders for the next integration step:

- `Nemotron3UltraPlanner` for NVIDIA Nemotron 3 Ultra planning/model runtime.
- `NemoClawSafetyProvider` for NVIDIA NemoClaw policy and safety control.
- `NvidiaAgentSkillsProvider` for external NVIDIA agent skills.
- `HermesStripeSkillsProvider` for Hermes Stripe Skills payment/provisioning.
- `StripeProvider` for real Stripe PaymentIntents once `stripe` and `STRIPE_SECRET_KEY` are configured.

Placeholders raise at call time until exact SDK or HTTP contracts are connected. That keeps the submission credible while making the upgrade path obvious.

## Judge Path

```bash
uv sync --extra dev
make smoke
```

What to look for in the output:

- The agent card shows advertised skills and integration status.
- The audit log includes identity, capability, budget, runtime plan, safety gate, quote, payment, and provisioning events.
- The payment is clearly marked as `stripe_test_mock`.
- The runtime/safety/skills/provisioning providers are visible by name.

## Demo Talk Track

"Trusted Agent Procurement is the commerce layer for autonomous business agents. It proves an agent can identify itself, prove delegated authority, stay inside a budget, pass a safety gate, buy GPU capacity, and leave behind audit evidence. The live demo is local and credential-free, while the repo exposes clean provider adapters for NVIDIA Nemotron 3 Ultra, NemoClaw, NVIDIA agent skills, Hermes Stripe Skills, and real Stripe PaymentIntents."

## Top-3 Differentiator

This is not another chat or workflow demo. It is infrastructure for agents that need to transact safely with vendors. The narrow GPU procurement story makes the system easy to judge, but the pattern generalizes to software seats, cloud credits, data purchases, and service contracts.
