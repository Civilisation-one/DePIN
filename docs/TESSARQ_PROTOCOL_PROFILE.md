# Tessarq native DePIN protocol profile v1

**Status:** compatibility specification  
**Applies to:** Civilisation.One DePIN ↔ Tessarq  
**Tessarq software:** `0.2.0-dev`  
**Protocol version:** 1  
**P2P version:** 2  
**Reviewed upstream commit:** `cecbdcaaf21dba545ee11c071050870e775899d2`  
**Reviewed:** 2026-09-28

This document fixes the exact Tessarq protocol surface that the DePIN repository depends on. It is not a replacement for the Quantum-Chain source code. If this document and the pinned source disagree, the pinned source is authoritative and this profile must be updated before compatibility is claimed.

## 1. Boundary

DePIN defines the physical-resource claim and the evidence needed to assess it. Tessarq defines the native transaction, cryptographic authentication, deterministic admission rules, replicated state, validator attestation and final receipt.

```text
physical service / observation
    -> evidence bytes + provenance
    -> evidence commitment
    -> node-signed ContributionEvent
    -> SubmitContribution transaction
    -> deterministic admission
    -> Quarantined
    -> validator attestations
    -> Accepted / Rejected
    -> certified state receipt
```

A valid signature establishes key possession and integrity. A finalised receipt establishes validator consensus over chain state. Neither fact, by itself, establishes physical truth.

## 2. Native cryptography

| Purpose | Native Tessarq rule |
|---|---|
| Public-key signature | ML-DSA-65 (FIPS 204) |
| Hash | SHA3-256 |
| Serialization for signed native objects | Borsh |
| Contribution signature context | `tessarq/depin/event/v1` |
| Enrollment signature context | `tessarq/depin/enroll/v2` |
| Heartbeat signature context | `tessarq/depin/heartbeat/v1` |
| Transaction signature context | `tessarq/tx/v1` |
| Evidence hash domain | `tessarq/depin/evidence/v1` |
| Event-ID domain | `tessarq/depin/event-id/v1` |

Tessarq domain-separated hashes use SHA3-256 over length-prefixed parts:

```text
u64_le(len(domain)) || domain ||
u64_le(len(part_1)) || part_1 ||
...
```

Consequently, the evidence commitment is not plain `SHA3-256(evidence)`. It is the Tessarq domain-separated construction with the evidence bytes as one part.

## 3. Resource classes

Native protocol v1 accepts exactly:

```text
compute
storage
network
sensor
research
```

Energy/infrastructure remains a DePIN roadmap class and is not a native Tessarq `ResourceClass` in the reviewed protocol.

## 4. Enrollment state required before contributions

A contribution references an already enrolled node. Enrollment binds:

```text
chain_id
operator address
node address
resource class
capability string
node class
simulated flag
```

The node key signs the enrollment payload under `tessarq/depin/enroll/v2`; the operator is the transaction signer. Operator and node keys must differ.

The chain stores the node's public key, operator, resource, capability, revocation status and last accepted contribution sequence. A contribution does not repeat all of this state.

## 5. ContributionEvent field order

Borsh field order is consensus-significant. For protocol v1 the exact native order is:

1. `node_id: Address`
2. `sequence: u64`
3. `resource: ResourceClass`
4. `started_at_ms: u64`
5. `ended_at_ms: u64`
6. `quantity: u64`
7. `unit: String`
8. `evidence_hash: Hash32`
9. `policy_version: u32`
10. `observation: Option<FieldObservation>`

Do not reorder fields or insert a field into the native object without a Tessarq protocol upgrade.

## 6. Contribution signature

The node signs:

```text
Borsh((chain_id, ContributionEvent))
```

using ML-DSA-65 and context:

```text
tessarq/depin/event/v1
```

The signature is carried next to the event in the native `SubmitContribution` transaction payload.

## 7. Evidence commitment

Raw evidence stays off-chain. The native event stores:

```text
evidence_hash = SHA3-256-domain(
    "tessarq/depin/evidence/v1",
    raw_evidence_bytes
)
```

where `SHA3-256-domain` is Tessarq's length-prefixed domain-separated hash construction described above.

The hash commits to bytes only. Meaning, calibration, provenance and sufficiency remain evidence-layer responsibilities.

## 8. Event identifier

Tessarq derives the event identifier from the chain ID and the complete event:

```text
event_id = hash_borsh(
    "tessarq/depin/event-id/v1",
    (chain_id, ContributionEvent)
)
```

Because the chain ID is included, an event ID is network-bound.

## 9. Deterministic admission rules

Before creating a contribution record, Tessarq checks all of the following:

1. the node exists;
2. the node is not revoked;
3. the event resource equals the enrolled node resource;
4. `policy_version` equals the active chain policy version;
5. `quantity > 0`;
6. `unit` is non-empty and at most 32 bytes;
7. `started_at_ms <= ended_at_ms`;
8. the event end is not older than the configured maximum age;
9. the event end is not farther in the future than the configured future allowance;
10. `sequence > node.last_sequence`;
11. the derived `event_id` is not already present;
12. the ML-DSA-65 event signature verifies against the enrolled node public key;
13. if an observation is present, deterministic recogniser assessment succeeds.

A failure rejects the transaction before contribution state is inserted.

## 10. Accepted submission state

A successfully admitted contribution is inserted as:

```text
status = Quarantined
```

It is **not accepted at submission time**.

The chain also advances the node's `last_sequence` to the event sequence.

## 11. Validator decision

Validators attest independently.

- acceptance occurs when accept attestations reach the Tessarq validator quorum (>2/3 voting power as configured by the validator-set quorum function);
- rejection occurs once reject power reaches the weak quorum (>1/3), because a >2/3 acceptance quorum is then impossible;
- duplicate validator attestations are rejected;
- attestations after the configured attestation window are rejected;
- accepted evidence labels must meet Tessarq's acceptance-label rule;
- rewards are computed only after acceptance and are paid from an existing rewards pool, never minted by evidence validation.

## 12. DePIN MVP incompatibility

The Python DePIN MVP currently uses Ed25519 and SHA-256. It is a prototype of identity and verification semantics, not a native Tessarq wire implementation.

```text
Ed25519/SHA-256 MVP object
    -- explicit adapter/migration required -->
ML-DSA-65/SHA3-256/Borsh Tessarq object
```

A bridge must not copy an MVP signature into a Tessarq signature field or claim the original SHA-256 digest is the native Tessarq evidence commitment. The bridge must retain the source object as provenance and create a separately authenticated native transaction.

## 13. Semantic conformance vectors

`conformance/tessarq-v1.json` contains protocol-level semantic vectors. These vectors intentionally do not contain fabricated ML-DSA keys or signatures. Cryptographic byte-for-byte vectors should be generated by the pinned Tessarq implementation and then checked into both repositories in a later cross-repo test step.

The current vectors cover:

- valid minimal contribution shape with chain-state preconditions;
- zero quantity;
- empty/oversized unit;
- resource mismatch;
- policy mismatch;
- reversed time interval;
- stale/future event;
- replay/out-of-order sequence;
- invalid node signature;
- mandatory quarantine after admission.

## 14. Change control

Compatibility must be reviewed again if any of these change upstream:

- `ContributionEvent` field declaration or enum ordering;
- Borsh encoding;
- ML-DSA parameter set or signature contexts;
- SHA3/domain-separated hash framing;
- evidence or event-ID domains;
- admission rejection rules;
- quorum or attestation thresholds;
- receipt proof format;
- protocol version or P2P version.

A documentation-only upstream change can advance the pinned commit after the diff is reviewed and recorded, without pretending a protocol change occurred.
