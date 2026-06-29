# Architecture

Trusted Agent Procurement is intentionally small. It exists to prove the operational loop that autonomous business agents need before they can spend money safely.

```text
Buyer Agent
  |
  | AgentPassport + procurement request
  v
CloudForge Trusted Procurement Desk
  |-- agentid_verify
  |-- capability gate
  |-- budget gate
  |-- runtime provider
  |-- safety provider
  |-- quote engine
  |-- payment provider
  |-- provisioning provider
  |-- skills provider
  v
Audit Log
```

## Core Modules

- `trusted_agent_procurement.identity`: issues demo passports in the same signed JWT shape used by `agentid`.
- `agentid_verify`: verifies DID-backed Ed25519 passport signatures and expiry.
- `trusted_agent_procurement.cloudforge`: validates authority, generates GPU quotes, enforces budgets, triggers payment, and records audit events.
- `trusted_agent_procurement.integrations`: defines provider interfaces for runtime planning, safety gating, skill registries, and provisioning.
- `trusted_agent_procurement.payments`: contains the `MockStripeProvider` used by the demo and a `StripeProvider` upgrade path.
- `trusted_agent_procurement.server`: exposes health, agent card, JSON-RPC, and REST-style procurement routes.
- `trusted_agent_procurement.demo`: terminal-first story for recording a 1-3 minute hackathon video.

## Trust Boundary

The buyer agent must present a valid `AgentPassport`. CloudForge checks:

- Ed25519 signature
- expiry
- `purchase:gpu`
- `vendor:cloudforge`
- `contract:sign`
- `budget:<amount>`

Requests that fail identity, capability, or budget checks are rejected before quote acceptance or payment.

## Payment Boundary

The default `MockStripeProvider` avoids requiring credentials during judging. It returns Stripe-shaped test payment IDs and dashboard URLs. The interface is deliberately the same place a real Stripe PaymentIntent adapter plugs in.

`HermesStripeSkillsProvider` names the Hermes Stripe Skills integration point but does not make external calls. It should be enabled only after the Hermes endpoint/API-key contract is wired.

## NVIDIA Boundaries

The demo uses credential-free local providers:

- `LocalRuntimeProvider` produces a deterministic procurement plan.
- `LocalSafetyProvider` blocks structurally invalid requests before quote or payment.
- `StaticAgentSkillsProvider` advertises local A2A-style skills.

The NVIDIA-facing adapters are placeholders:

- `Nemotron3UltraPlanner` for runtime/model planning.
- `NemoClawSafetyProvider` for policy/safety control.
- `NvidiaAgentSkillsProvider` for an external skills registry.

They intentionally raise at call time until the exact NVIDIA SDK or HTTP contracts are added. This keeps the hackathon demo runnable without overstating live integration.

## Provisioning Boundary

`MockCloudForgeProvisioningProvider` returns deterministic resource and onboarding records after payment. A real provider can replace it with the same `provision(...)` interface once CloudForge, Stripe, or Hermes provisioning APIs are connected.
