---
name: api-contract
description: Contract-first rules for any frontend-backend or service boundary. Apply before implementing or changing any API endpoint, shared type, or cross-service call — and before fanning out parallel FE/BE workers.
---

# API Contract

Two sides inferring the same data shape independently is a classic rework generator — and it silently breaks parallel fan-out. The contract file is the only truth.

## Rules

1. **Contract before code.** Endpoint/shape changes edit the contract first (`contract/openapi.yaml`, shared `types/` package, or protobuf — per STACK.md), then both sides implement against it.
2. **Generate, don't restate.** Client/server types generate from the contract where the stack allows; hand-copied shapes are drift waiting to bill you.
3. **Fan-out enabler**: parallel FE and BE workers each receive the contract file — never each other's code. The contract is the entire interface between them.
4. **Versioning discipline**: breaking change = explicit PLAN step with both sides + migration listed; the reviewer checks diff-vs-contract as part of verification-gate.
5. Errors are part of the contract: shapes and status codes declared, not improvised per endpoint.

## Smallest viable contract

No spec tooling in the stack? A single `contract.md` with typed request/response examples per endpoint still beats zero — the point is one shared artifact, not the format.
