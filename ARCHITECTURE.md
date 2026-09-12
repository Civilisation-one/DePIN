# Civilisation.One DePIN Architecture v0.1

## 1. System boundary

Civilisation.One DePIN connects physical resources to Civilisation.One through constrained node runtimes and an evidence-first audit path.

The trusted path is:

```text
Resource -> Node -> Measurement -> Evidence -> Verification -> Receipt -> Audit
```

No resource contribution should affect accounting, reputation or settlement before verification.

## 2. Principal entities

### Resource
A physical or virtualized resource with measurable capacity or output.

### Operator
The accountable entity controlling a node or physical resource.

### Node
The software/runtime identity representing one operational resource endpoint or controlled resource group.

### Capability
A machine-readable statement of what the node is allowed and able to provide.

### Contribution Event
A bounded claim that a resource delivered a measurable service or observation.

### Evidence
Data sufficient to evaluate a contribution claim, including timestamps, measurements, hashes, signatures and provenance.

### Verification Result
A policy-bound decision accepting, rejecting or quarantining a contribution event.

### Receipt
A signed immutable record of the verified outcome.

## 3. Trust boundaries

```text
[Physical world]
      |
      | sensor / compute / storage / network interface
      v
[Untrusted resource adapter]
      |
      v
[Node Runtime]
      |
      | signed event
      v
[Verification Boundary]
      |
      v
[Audit / Accounting / Reputation]
```

The physical resource and adapter must not be assumed trustworthy merely because they are registered.

## 4. Minimum event schema

A contribution event should contain at least:

```json
{
  "event_id": "uuid",
  "node_id": "did-or-equivalent",
  "resource_type": "compute|storage|network|sensor|research",
  "capability_id": "string",
  "started_at": "RFC3339",
  "ended_at": "RFC3339",
  "measurement": {},
  "unit": "declared-unit",
  "evidence_hash": "sha256:...",
  "provenance": {},
  "signature": "...",
  "policy_version": "..."
}
```

## 5. Verification pipeline

```text
parse
-> schema
-> version
-> identity
-> signature
-> freshness
-> authorization
-> capability
-> measurement validation
-> provenance validation
-> replay protection
-> policy
-> acceptance / quarantine / rejection
```

## 6. Security baseline

- cryptographic node identity;
- signed contribution events;
- short-lived authorization where appropriate;
- replay protection;
- event nonces / sequence control;
- least-privilege capabilities;
- separation of measurement evidence from economic reward;
- immutable or append-only audit semantics;
- revocation and quarantine support;
- no autonomous escalation of authority.

## 7. Measurement model

Each resource class requires its own measurable quantities.

Examples:

| Resource | Example observables |
|---|---|
| Compute | task duration, accelerator type, verified workload output, utilization |
| Storage | bytes stored, duration, integrity challenge success |
| Network | delivered bandwidth, latency, packet loss, availability |
| Sensor | calibrated observable, sampling interval, uncertainty, location class |
| Research hardware | experiment identifier, parameters, output checksum, device provenance |

Measurements must define units and calibration/validation procedures before they are treated as evidence.

## 8. Public audit layer

The public audit layer should expose sufficient evidence to verify network activity without exposing secrets or personal data.

Recommended public fields:

- receipt identifier;
- node pseudonymous identifier;
- resource class;
- contribution class;
- verification status;
- time window;
- evidence commitment/hash;
- policy version;
- verifier signature;
- provenance reference.

Protected operational data stays outside the public receipt and is referenced by commitments where necessary.

## 9. Integration points

Civilisation.One DePIN may integrate with:

- Civilisation.One Core Platform
- MirrorME clients
- Multi-model AI Router
- MK3A identity/security
- CV1 contribution/reputation system
- Provenance & Evidence Engine
- Universal Transaction System
- monitoring and observability infrastructure

## 10. Validation condition

The DePIN component should not be described as operational until at least one independently operated physical resource completes the full lifecycle:

```text
register -> authenticate -> advertise capability -> execute/measure
-> produce evidence -> verify -> issue receipt -> audit independently
```
