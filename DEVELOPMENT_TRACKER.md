# Civilisation.One DePIN — Development Tracker

**Tracker version:** 0.1  
**Maturity scale:** 0 Concept · 1 Specified · 2 Prototype · 3 Integrated · 4 Tested · 5 Production

| ID | Workstream | Deliverable | Priority | Maturity | Status |
|---|---|---|---|---:|---|
| D01 | Architecture | Canonical DePIN architecture and boundaries | P0 | 1 | Specified |
| D02 | Node Identity | Unique cryptographic node identity | P0 | 1 | Planned |
| D03 | Operator Identity | Operator-to-node ownership/authority binding | P0 | 1 | Planned |
| D04 | Node Registry | Register, revoke and query nodes | P0 | 0 | Planned |
| D05 | Capability Registry | Machine-readable resource capability manifests | P0 | 1 | Planned |
| D06 | Node Runtime | Minimal secure node agent/runtime | P0 | 0 | Planned |
| D07 | Resource Adapters | Common adapter interface for resource classes | P0 | 0 | Planned |
| D08 | Compute Adapter | CPU/GPU workload contribution adapter | P0 | 0 | Planned |
| D09 | Storage Adapter | Storage contribution and integrity proofs | P1 | 0 | Planned |
| D10 | Network Adapter | Bandwidth/relay contribution measurement | P1 | 0 | Planned |
| D11 | Sensor Adapter | Sensor contribution schema and calibration metadata | P1 | 0 | Planned |
| D12 | Research Hardware Adapter | Laboratory / specialist-device interface | P2 | 0 | Planned |
| D13 | Measurement Schema | Canonical units, timestamps and measurement envelope | P0 | 1 | Planned |
| D14 | Evidence Schema | Evidence object and evidence commitments | P0 | 1 | Planned |
| D15 | Provenance | End-to-end provenance chain | P0 | 1 | Planned |
| D16 | Event Signing | Cryptographic signing of contribution events | P0 | 1 | Planned |
| D17 | Replay Protection | Nonce/sequence/freshness validation | P0 | 1 | Planned |
| D18 | Authorization | Least-privilege resource authorization | P0 | 1 | Planned |
| D19 | Verification Engine | Contribution verification pipeline | P0 | 1 | Planned |
| D20 | Quarantine | Invalid/suspicious event quarantine path | P0 | 0 | Planned |
| D21 | Signed Receipts | Canonical verified contribution receipt | P0 | 1 | Planned |
| D22 | Public Audit API | Public receipt/query interface | P0 | 0 | Planned |
| D23 | Audit Explorer | Human-readable audit dashboard | P1 | 0 | Planned |
| D24 | Resource Discovery | Search/selection of available resources | P1 | 0 | Planned |
| D25 | Scheduling | Workload/resource dispatch | P1 | 0 | Planned |
| D26 | Accounting | Verified resource accounting ledger | P1 | 0 | Planned |
| D27 | CV1 Integration | Feed verified contributions into CV1 scoring | P2 | 0 | Planned |
| D28 | Economic Model | Cost/reward model separate from evidence validity | P2 | 0 | Research |
| D29 | Settlement | Optional payment/settlement integration | P2 | 0 | Deferred |
| D30 | Observability | Metrics, logs, traces and node health | P0 | 0 | Planned |
| D31 | Security | Threat model and security controls | P0 | 1 | Planned |
| D32 | Privacy | Public/private data classification | P0 | 1 | Planned |
| D33 | Compliance | GDPR/data-governance analysis | P1 | 0 | Planned |
| D34 | API | OpenAPI 3.1 interface specification | P0 | 0 | Planned |
| D35 | SDK | Developer SDK for node/resource integration | P1 | 0 | Planned |
| D36 | CLI | Node operator CLI | P1 | 0 | Planned |
| D37 | Test Harness | Local multi-node simulation environment | P0 | 0 | Planned |
| D38 | Unit Tests | Core validation and schema tests | P0 | 0 | Planned |
| D39 | Integration Tests | Full contribution lifecycle tests | P0 | 0 | Planned |
| D40 | Adversarial Tests | Spoof/replay/tamper/fraud scenarios | P0 | 0 | Planned |
| D41 | Independent Node Pilot | External physical node pilot | P0 | 0 | Not started |
| D42 | Reproducibility | Repeatable deployment and test instructions | P0 | 0 | Planned |
| D43 | CI/CD | Automated checks, builds and releases | P1 | 0 | Planned |
| D44 | Deployment | Container/package deployment strategy | P1 | 0 | Planned |
| D45 | Documentation | Operator, API, security and validation docs | P0 | 1 | In progress |

## Milestones

### M0 — Specification freeze
- Architecture v1
- contribution event schema
- capability schema
- evidence schema
- receipt schema
- trust boundaries
- security threat model

**Exit condition:** all P0 data contracts are versioned and reviewable.

### M1 — Single-node prototype
- node identity
- capability advertisement
- one compute adapter
- signed contribution event
- verification pipeline
- signed receipt

**Exit condition:** one local physical machine completes the full contribution lifecycle.

### M2 — Multi-node test network
- 3+ independently configured nodes
- resource discovery
- scheduling
- public audit API
- observability
- failure/quarantine handling

**Exit condition:** reproducible multi-node operation with auditable receipts.

### M3 — Independent physical-node pilot
- at least one node operated outside the core development environment
- independently reproducible deployment
- adversarial validation
- public audit explorer

**Exit condition:** an external operator can deploy, contribute and independently verify receipts.

### M4 — Production readiness
- security review
- privacy/compliance review
- fault tolerance
- upgrade/revocation procedures
- production monitoring
- incident response
- versioned SDK/API

**Exit condition:** maturity 4 or higher on all P0 workstreams and no unresolved critical security findings.

## Current critical path

```text
Architecture
 -> Schemas
 -> Identity
 -> Node Runtime
 -> Measurement
 -> Evidence
 -> Verification
 -> Receipt
 -> Audit API
 -> External Pilot
```

## Definition of done for each tracker item

A workstream is not complete merely because code exists. Completion requires:

1. specification;
2. implementation;
3. automated tests;
4. security/edge-case review;
5. documentation;
6. reproducible validation evidence;
7. versioned release/commit.
