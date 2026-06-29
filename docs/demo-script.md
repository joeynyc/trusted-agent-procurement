# Demo Script

Target length: 90-120 seconds.

## Opening

"This is Trusted Agent Procurement. It lets an autonomous business agent prove who it is, prove what it is allowed to spend, negotiate GPU capacity with a vendor agent, pay through a Stripe-style boundary, and receive provisioning with an audit trail."

## Terminal

Run:

```bash
uv run trusted-agent-demo --fast
```

Call out the visible phases:

1. The buyer agent presents an AgentPassport.
2. CloudForge publishes an A2A-style agent card.
3. CloudForge quotes 8 H100 GPUs for 72 hours.
4. Payment succeeds through the Stripe test-mode provider.
5. A GPU resource and onboarding URL are returned.
6. The audit log proves every step.

## Close

"The point is not just a GPU purchase. This is a reusable pattern for agent-run operations: identity, delegated authority, spend limits, payment, provisioning, and auditability."

## Submission Tweet Draft

Built Trusted Agent Procurement for the Hermes Agent Accelerated Business Hackathon.

Autonomous buyer agents can verify identity, prove spend authority, negotiate GPU capacity, trigger Stripe-style payment, and receive provisioning with a full audit log.

Demo: [video link]

@NousResearch
