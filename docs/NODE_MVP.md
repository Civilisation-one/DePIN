# Civilisation.One DePIN: identity and verification MVP

**Status: prototype only.** This change is the first implementation slice of `ARCHITECTURE.md`, not a deployed physical network. It does not contain a node hardware adapter, actual workload executor, independently calibrated sensor, settlement service or on-chain integration.

## Run

Requires Python 3.11+ and the `cryptography` dependency. From the repository root:

```sh
python -m pip install -r requirements.txt pytest
python -m pytest -q tests
python -m scripts.demo_node
```

The demonstration generates disposable Ed25519 identities, registers a compute node, signs a contribution event, checks its evidence digest and signature, and emits an authenticated **quarantined** receipt. The SQLite database and all private keys are ephemeral in the demo. Nothing is broadcast, deployed, rewarded or written to a blockchain. Never commit a production key.

## Protocol version 1

- Identity: Ed25519 raw public key in lowercase hex; role-separated node/operator/verifier ID = SHA-256 of the role-prefixed public key bytes. Public identifiers are pseudonyms, not claims of legal identity or hardware uniqueness.
- Enrollment: both operator and node sign the exact same canonical enrollment payload with a protocol-specific signing domain. The operator proves control of its key; the node proves control of its own key. Registry binds node, operator, and one resource class; operator-signed revocation disables subsequent events.
- Event: `version`, UUID `event_id`, `node_id`, strictly increasing per-node positive integer `sequence`, resource class, timezone-aware start/end, positive integer `measurement.quantity`, declared `measurement.unit`, `sha256:` raw-evidence digest, `policy_version`, plus the node signature. The schema is intentionally minimal; there is no claim that arbitrary units are calibrated or comparable.
- Verification: check exact schema and version, freshness (start and end at most five minutes old; end no more than 30 seconds ahead), evidence-byte SHA-256 match, registered/unrevoked node and matching resource, node signature, increasing sequence and unique event ID. SQLite uses `BEGIN IMMEDIATE` to serialize check-and-record. Event ID and sequence are persisted alongside receipts; rejected/quarantined **valid** events also consume their sequence, preventing replay and after-the-fact promotion.
- Decision: **quarantined by default**. The trusted verifier process can supply an external `evaluator(payload, evidence)` to reach `accepted` only on literal `True`, or `rejected` on any other return. Errors quarantine. An evaluator must implement independently validated resource-specific evidence; the demo provides none. A verifier must never accept the submitter's `verified=true` claim as its evaluator.
- Receipt: signed by verifier key; includes node ID, event ID, event hash, decision, policy version, verifier ID, timestamp, and a domain-separated receipt digest. `verify_receipt` checks integrity/authenticity with the expected trusted verifier public key. Receipt verification is **not** a proof of actual resource delivery.

## Explicit security boundaries and limitations

1. No private keys are stored in the registry. The demo uses in-memory ephemeral keys only. Production operators require hardware-backed or securely managed keys, rotation, recovery, and an operator-identity enrollment policy.
2. SQLite persists replay state **only on this one registry database**. It is not a distributed consensus service or tamper-resistant append-only database. Protect the database with OS permissions, backups and audit trails; a multi-verifier system requires coordinated replay state and database migrations.
3. `Verifier.verify` accepts a trusted clock injection for deterministic tests; real services must use trusted server time. The verifier-supplied evaluator runs under a SQLite write transaction in this prototype: keep it fast and local; design an asynchronous claim/reservation state machine before production use.
4. A valid key signature establishes key possession, not hardware origin, identity legitimacy, measurement truth, service delivery or independence of the evaluating party. Public evidence digests can reveal information about low-entropy source data; avoid publishing private evidence or linking identifiers without review.
5. Resource types and measurement units are declarations, not validated calibration protocols. Require class-specific schemas, authorization policy, objective workload proofs and an independent physical-node pilot before paying or scoring contributions.
6. No blockchain integration yet. The draft artifact-anchor contract in `Civilisation-one/civilisation-one` PR #13 is independent and should anchor only verified receipt digests after chain selection, finality rules, access controls and integration tests. A digest on-chain cannot validate a false claim.
7. No rate limiting, networking, multi-tenant API, TLS, protected audit export, key rotation, threat-model audit or production deployment. Do not expose this prototype to untrusted networks.

## Tracker mapping and next delivery

Initial code addresses a bounded portion of D02 node identity, D03 operator binding, D04 registration/revocation, D13 minimal measurement format, D14 evidence commitment, D16 event signing, D17 replay protection, D19 verification gating, D20 quarantine, D21 signed receipts, D38 unit tests and D43 CI. These workstreams are **not complete** under the development tracker's definition of done.

Next: versioned JSON/OpenAPI schemas and explicit operator admission rules; a real node runtime + compute adapter with independently checked workload results; protected audit API; reliable, tamper-evident event storage; cross-node integration and adversarial tests. Then conduct an independently operated physical-node pilot before declaring the DePIN operational. Blockchain anchoring is an optional audit integration, not a substitute for these steps.
