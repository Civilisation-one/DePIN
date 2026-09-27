# Civilisation.One DePIN

**Status:** Development specification  
**Owner:** Civilisation.One  
**Component:** Decentralized Physical Infrastructure Network (DePIN)

## Purpose

Civilisation.One DePIN is the physical-resource layer of the Civilisation.One platform. It connects independently operated compute, storage, network, sensor, edge and research resources to a common verification and public-audit framework.

The system is designed around the principle:

```text
Physical Resource
    -> Registered Node
    -> Measured Contribution
    -> Cryptographic Evidence
    -> Verification
    -> Auditable Receipt
```

DePIN is not defined merely as a token or cryptocurrency layer. Its core engineering objective is to make real-world infrastructure contributions measurable, verifiable, attributable and auditable.

## Initial resource classes

1. Compute — CPU, GPU, accelerator and simulation capacity.
2. Storage — datasets, archives, object storage and research data.
3. Network — bandwidth, routing, relay and edge connectivity.
4. Sensors — environmental, scientific and infrastructure measurements.
5. Research hardware — laboratory, quantum, robotics and specialist equipment interfaces.
6. Energy/infrastructure — future verified physical-resource integrations where legally and technically appropriate.

## Core architecture

```text
Operator / Device
      |
      v
Node Runtime
      |
      +--> Identity + MK3A security
      +--> Resource measurement
      +--> Capability registry
      +--> Health / uptime telemetry
      |
      v
Contribution Event
      |
      v
Evidence + Provenance
      |
      v
Verification / Policy Gate
      |
      v
Signed Audit Receipt
      |
      +--> Civilisation.One public audit layer
      +--> Resource accounting
      +--> CV1 / reputation inputs
      +--> Optional settlement layer
```

## Tessarq Quantum-Chain integration

Tessarq is the current Civilisation.One Layer-1 implementation for finalising DePIN contribution state, validator attestations and independently verifiable receipts.

The DePIN repository pins a reviewed Tessarq compatibility snapshot instead of implicitly following the moving `Quantum-Chain/main` branch:

- integration guide: `docs/TESSARQ_INTEGRATION.md`
- machine-readable compatibility manifest: `integrations/tessarq.json`
- upstream repository: `Civilisation-one/Quantum-Chain`

Current pinned baseline: **Tessarq 0.2.0-dev**, protocol version **1**, P2P version **2**, upstream commit `94aa1c6382eba930fa70c5474140b0c13863f5a9`.

The local Python DePIN MVP and native Tessarq protocol use different cryptographic formats. Ed25519/SHA-256 prototype events must not be treated as native Tessarq ML-DSA-65/SHA3-256 transactions without an explicitly versioned adapter or migration procedure.

## Design requirements

- No unverifiable contribution claims.
- Every contribution event must carry provenance.
- Identity, authorization and resource capability must be separated.
- Execution authority is deny-by-default.
- Measurements must define units, sampling rules and uncertainty where applicable.
- Receipts must be tamper-evident and replay-resistant.
- Public audit records must not leak protected personal or operational data.
- Optional economic incentives must remain separate from evidence validity.

## Major subsystems

- Node Registry
- Operator Runtime
- Resource Discovery
- Capability Registry
- Measurement & Telemetry
- Proof / Evidence Generation
- Provenance Engine
- Verification Gate
- Public Audit Layer
- Signed Receipts
- Reputation / CV1 integration
- Resource Accounting
- Optional Settlement Layer
- APIs / SDK / CLI
- Monitoring & Incident Response
- Security / Privacy / Compliance

## Development maturity scale

| Level | Meaning |
|---|---|
| 0 | Concept |
| 1 | Specified |
| 2 | Prototype |
| 3 | Integrated |
| 4 | Tested |
| 5 | Production |

## Repository documentation

- `README.md` — project definition and scope
- `ARCHITECTURE.md` — system architecture and trust boundaries
- `DEVELOPMENT_TRACKER.md` — implementation tracker
- `docs/NODE_MVP.md` — local identity/verification prototype and limitations
- `docs/TESSARQ_INTEGRATION.md` — Tessarq setup, versions, compatibility and operating boundary
- `integrations/tessarq.json` — pinned Tessarq compatibility snapshot
- Future: `API.md`, `SECURITY.md`, `VALIDATION.md`, `TESTING.md`, `ROADMAP.md`, `PROVENANCE.md`

## Scientific / engineering status

This repository describes an engineering system under development. A DePIN claim is considered operational only when independently operated physical resources are actually connected, measured, verified and auditable. Architecture documents, simulated nodes, signatures or blockchain inclusion alone do not constitute proof that a physical resource delivered the claimed service.
