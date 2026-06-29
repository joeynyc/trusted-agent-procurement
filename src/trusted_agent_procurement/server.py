"""Local Starlette server for the Trusted Agent Procurement demo."""

from __future__ import annotations

import os
from dataclasses import asdict

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .cloudforge import CloudForgeProcurementDesk, ProcurementDenied
from .models import ProcurementRequest


desk = CloudForgeProcurementDesk()


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "trusted-agent-procurement"})


async def agent_card(request: Request) -> JSONResponse:
    return JSONResponse(desk.agent_card())


async def procure(request: Request) -> JSONResponse:
    passport = request.headers.get("authorization", "")
    if passport.startswith("AgentPassport "):
        passport = passport.removeprefix("AgentPassport ").strip()

    if not passport:
        return JSONResponse({"error": "missing AgentPassport authorization"}, status_code=401)

    try:
        body = await request.json()
        procurement_request = ProcurementRequest(**body)
        result = desk.procure(passport_token=passport, request=procurement_request)
    except ProcurementDenied as exc:
        return JSONResponse({"error": str(exc)}, status_code=403)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    return JSONResponse({
        "buyer_agent": result.buyer_agent,
        "verified_did": result.verified_did,
        "selected_quote": asdict(result.selected_quote),
        "payment": asdict(result.payment),
        "provisioned_resource_id": result.provisioned_resource_id,
        "onboarding_url": result.onboarding_url,
        "audit_log": result.audit_log,
    })


async def jsonrpc(request: Request) -> JSONResponse:
    """Minimal JSON-RPC surface for A2A-style agent clients."""
    try:
        envelope = await request.json()
    except Exception:
        return JSONResponse(_jsonrpc_error(None, -32700, "Parse error"), status_code=400)

    request_id = envelope.get("id")
    if envelope.get("jsonrpc") != "2.0":
        return JSONResponse(_jsonrpc_error(request_id, -32600, "Invalid Request"), status_code=400)

    if envelope.get("method") != "procurement/procure":
        return JSONResponse(_jsonrpc_error(request_id, -32601, "Method not found"), status_code=404)

    params = envelope.get("params") or {}
    passport = params.get("passport", "")
    procurement_payload = params.get("request", {})
    if not passport:
        return JSONResponse(_jsonrpc_error(request_id, 401, "missing AgentPassport"), status_code=401)

    try:
        procurement_request = ProcurementRequest(**procurement_payload)
        result = desk.procure(passport_token=passport, request=procurement_request)
    except ProcurementDenied as exc:
        return JSONResponse(_jsonrpc_error(request_id, 403, str(exc)), status_code=403)
    except Exception as exc:
        return JSONResponse(_jsonrpc_error(request_id, -32602, str(exc)), status_code=400)

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": _serialize_result(result),
    })


def _serialize_result(result):
    return {
        "buyer_agent": result.buyer_agent,
        "verified_did": result.verified_did,
        "selected_quote": asdict(result.selected_quote),
        "payment": asdict(result.payment),
        "provisioned_resource_id": result.provisioned_resource_id,
        "onboarding_url": result.onboarding_url,
        "audit_log": result.audit_log,
    }


def _jsonrpc_error(request_id, code: int, message: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def create_app() -> Starlette:
    return Starlette(routes=[
        Route("/", jsonrpc, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
        Route("/.well-known/agent-card.json", agent_card, methods=["GET"]),
        Route("/procure", procure, methods=["POST"]),
    ])


def main() -> None:
    port = int(os.getenv("PORT", "9998"))
    print(f"Trusted Agent Procurement server: http://127.0.0.1:{port}")
    print(f"Agent card: http://127.0.0.1:{port}/.well-known/agent-card.json")
    uvicorn.run(create_app(), host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
