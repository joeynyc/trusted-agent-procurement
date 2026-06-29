"""Call the local procurement desk over the JSON-RPC interface."""

from __future__ import annotations

import json
import urllib.request

from trusted_agent_procurement.identity import DemoPassportIssuer


def main() -> None:
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

    envelope = {
        "jsonrpc": "2.0",
        "id": "demo-1",
        "method": "procurement/procure",
        "params": {
            "passport": passport,
            "request": {
                "buyer_agent": "nexus-buyer-agent",
                "workload": "72-hour fine-tuning run",
                "gpu_model": "H100",
                "quantity": 8,
                "hours": 72,
                "max_budget_usd": 5000,
                "region": "us-east-1",
            },
        },
    }

    request = urllib.request.Request(
        "http://127.0.0.1:9998/",
        data=json.dumps(envelope).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        print(json.dumps(json.loads(response.read()), indent=2))


if __name__ == "__main__":
    main()
