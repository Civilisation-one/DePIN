# Tessarq Quantum-Chain setup and compatibility

**Integration status:** specified / development  
**Upstream:** `Civilisation-one/Quantum-Chain`  
**Pinned upstream commit:** `cecbdcaaf21dba545ee11c071050870e775899d2`  
**Pinned software version:** `0.2.0-dev`  
**Protocol version:** `1`  
**P2P version:** `2`  
**Last reviewed:** 2026-09-28

This document defines how the Civilisation.One DePIN repository interoperates with Tessarq. It deliberately pins an exact upstream snapshot so an upgrade of the chain does not silently redefine the DePIN protocol boundary.

## 1. Responsibility boundary

```text
Physical resource
  -> DePIN measurement/evidence/provenance
  -> signed contribution envelope
  -> Tessarq transaction admission
  -> quarantine
  -> validator attestations
  -> >2/3 acceptance quorum
  -> finalised state
  -> receipt + state proof
  -> independent audit
```

DePIN owns physical-resource semantics, measurement rules, provenance and evidence requirements.

Tessarq owns native transaction encoding, post-quantum signatures, replay/freshness enforcement, BFT finality, validator attestations, state roots and chain receipts.

A Tessarq receipt proves what the validator quorum finalised. It does **not** independently prove that the underlying physical-world claim was true.

## 2. Pinned versions and primitives

| Component | Pinned value |
|---|---|
| Tessarq software | `0.2.0-dev` |
| Upstream commit | `cecbdcaaf21dba545ee11c071050870e775899d2` |
| Rust toolchain minimum | `1.85` |
| Rust edition | 2021 |
| Chain protocol version | 1 |
| P2P protocol version | 2 |
| Transaction / vote / node signatures | ML-DSA-65 (FIPS 204) |
| Hashing | SHA3-256 |
| Default validator topology | 4 validators |
| Testnet chain ID | `tessarq-testnet-0` |
| P2P port | 26650 |
| RPC port | 8650 |
| WireGuard port | UDP 51820 |
| Default peer policy | `validators_only` |

The canonical machine-readable copy is `integrations/tessarq.json`. The exact native contribution profile is `docs/TESSARQ_PROTOCOL_PROFILE.md`, with semantic regression vectors in `conformance/tessarq-v1.json`.

## 3. Important crypto compatibility rule

The local DePIN Python MVP uses Ed25519 signatures and SHA-256 commitments. Native Tessarq uses ML-DSA-65 signatures and SHA3-256.

Therefore:

```text
DePIN-MVP Ed25519/SHA-256 event
    !=
native Tessarq ML-DSA-65/SHA3-256 transaction
```

Do not reinterpret, byte-cast, hash-wrap or relabel an MVP event as a native Tessarq event.

Any migration or bridge must define a versioned transformation, preserve the original source evidence and signatures, produce a new native Tessarq transaction, and make the trust transition explicit.

## 4. Developer setup

Prerequisites:

- Rust 1.85 or newer compatible toolchain
- Cargo
- the `Civilisation-one/Quantum-Chain` source at the pinned commit

```sh
git clone https://github.com/Civilisation-one/Quantum-Chain
cd Quantum-Chain
git checkout cecbdcaaf21dba545ee11c071050870e775899d2
cargo build --release
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
```

For a disposable 4-validator local network:

```sh
Q=target/release/tessarq
$Q testnet --validators 4 --dir testnet

for i in 0 1 2 3; do
  $Q run --config testnet/node$i/config.json &
done

$Q get --rpc http://127.0.0.1:8650 status
```

All local nodes must report the same genesis hash and advancing finalised height before DePIN lifecycle testing begins.

## 5. Testnet-0 multi-machine baseline

The current upstream deployment runbook assumes:

- 4 Ubuntu 24.04 LTS validator hosts, or comparable systemd Linux;
- 4+ vCPU, 16 GB RAM and 200 GB SSD per validator;
- private WireGuard mesh;
- UDP 51820 open only between validator hosts;
- synchronised system clocks;
- Tessarq P2P on the private mesh at port 26650;
- RPC bound to `127.0.0.1:8650` unless deliberately placed behind a protected public endpoint.

Example mesh addresses:

```text
validator-1  10.77.0.1
validator-2  10.77.0.2
validator-3  10.77.0.3
validator-4  10.77.0.4
```

Build and install:

```sh
curl https://sh.rustup.rs -sSf | sh -s -- -y
. ~/.cargo/env
git clone https://github.com/Civilisation-one/Quantum-Chain
cd Quantum-Chain
git checkout cecbdcaaf21dba545ee11c071050870e775899d2
cargo build --release
sudo deploy/install.sh target/release/tessarq
```

Generate an encrypted validator key on each validator host:

```sh
sudo -u tessarq bash -c 'umask 077; head -c 32 /dev/urandom | base64 > /etc/tessarq/key.password'

sudo -u tessarq env TESSARQ_KEY_PASSWORD_FILE=/etc/tessarq/key.password \
  tessarq keygen --encrypt --out /etc/tessarq/key.enc.json

sudo -u tessarq tessarq export-pubkey \
  --key /etc/tessarq/key.enc.json \
  --out /tmp/validator.pub.json
```

Private validator keys must never be collected into this repository.

## 6. Genesis baseline

The current Testnet-0 runbook uses:

```sh
FAUCET=$(tessarq keygen --out faucet.json)

tessarq genesis \
  --chain-id tessarq-testnet-0 \
  --validator validator-1=validator-1.pub.json \
  --validator validator-2=validator-2.pub.json \
  --validator validator-3=validator-3.pub.json \
  --validator validator-4=validator-4.pub.json \
  --economics genesis/economics.placeholder.json \
  --faucet "$FAUCET" \
  --min-upgrade-lead-blocks 600 \
  --out genesis.json
```

The coordinator distributes `genesis.json`; operators verify the genesis hash over a separate trusted channel.

The placeholder economics file is suitable only for development/testnet rehearsal. Mainnet parameters require separate review and approval.

## 7. Validator configuration baseline

Representative upstream configuration:

```json
{
  "name": "validator-1",
  "key_file": "key.enc.json",
  "key_password_file": "key.password",
  "genesis_file": "genesis.json",
  "data_dir": "/var/lib/tessarq/data",
  "p2p_listen": "10.77.0.1:26650",
  "rpc_listen": "127.0.0.1:8650",
  "peer_policy": "validators_only",
  "trusted_peers": [],
  "snapshot_interval_blocks": 1000,
  "blocks_in_memory": 1000
}
```

Peer entries are pinned as:

```text
<validator-address>@<mesh-ip>:26650
```

## 8. Native DePIN lifecycle on Tessarq

The native chain flow is:

```text
enroll
 -> heartbeat / active lease
 -> contribute
 -> quarantine
 -> validator attestations
 -> accepted/rejected
 -> receipt proof
```

Representative development commands:

```sh
Q=target/release/tessarq

$Q keygen --out testnet/sensor.json

$Q enroll \
  --key testnet/faucet.json \
  --node-key testnet/sensor.json \
  --resource sensor \
  --capability field-array

$Q heartbeat \
  --key testnet/faucet.json \
  --node-key testnet/sensor.json \
  --lease-ms 60000

$Q contribute \
  --key testnet/faucet.json \
  --node-key testnet/sensor.json \
  --quantity 4 \
  --unit sample-batch \
  --evidence-file raw.bin \
  --observation-file field.json

# Three validators in a 4-validator equal-power testnet can cross >2/3.
$Q attest --rpc http://127.0.0.1:8650 --key testnet/node0/key.json --event <event_id> --verdict accept --label reproduced_result
$Q attest --rpc http://127.0.0.1:8651 --key testnet/node1/key.json --event <event_id> --verdict accept --label reproduced_result
$Q attest --rpc http://127.0.0.1:8652 --key testnet/node2/key.json --event <event_id> --verdict accept --label reproduced_result

$Q verify-receipt --genesis testnet/genesis.json --event <event_id>
```

The exact upstream CLI remains authoritative. Re-check the pinned upstream documentation when this manifest changes.

## 9. Protocol upgrades

Every Tessarq block carries a protocol version. The pinned chain starts at protocol version 1.

A protocol upgrade is not a normal binary update:

1. install a release that understands the proposed next protocol;
2. validators signal the same version and activation height;
3. scheduling requires more than 2/3 of voting power;
4. activation occurs deterministically at the scheduled height;
5. binaries that cannot execute the new protocol halt instead of continuing on incompatible rules.

DePIN must update `integrations/tessarq.json` and this document whenever the supported protocol version, P2P version, transaction format, signature context, hashing rule, receipt proof or node lifecycle changes.

## 10. Security and operational limits

At this pinned snapshot:

- validator membership is static from genesis;
- the validator transport is authenticated but not natively encrypted after the handshake, so the production-like testnet uses a private WireGuard mesh;
- cryptographic implementation and protocol code still require independent security review before production use;
- a running validator host can expose keys despite encrypted-at-rest key files;
- a finalised receipt is evidence of validator consensus, not direct proof of a physical-world event;
- independent physical-node pilots and class-specific evidence evaluators remain required for DePIN operational claims.

## 11. Conformance profile

The DePIN repository does not duplicate Tessarq consensus code. Instead it pins the protocol surface DePIN depends on:

- the exact `ContributionEvent` field order;
- Borsh as the signed/event-ID encoding;
- ML-DSA-65 event signatures with context `tessarq/depin/event/v1`;
- SHA3-256 evidence commitments under `tessarq/depin/evidence/v1`;
- SHA3-256 event IDs under `tessarq/depin/event-id/v1`;
- admission rules for resource class, policy version, measurement bounds, freshness, sequence/replay protection and signature verification;
- quarantine as the only state immediately after a valid submission.

See `docs/TESSARQ_PROTOCOL_PROFILE.md`. The JSON vectors in `conformance/tessarq-v1.json` are checked in the DePIN test suite and are intended to be consumed by future cross-repository integration tests.

The reviewed upstream movement from `94aa1c6382eba930fa70c5474140b0c13863f5a9` to `cecbdcaaf21dba545ee11c071050870e775899d2` changes only `deploy/README.md` (deployment instructions); protocol and consensus code are unchanged.

## 12. Upgrade checklist

Before changing the pinned Tessarq baseline:

- [ ] record exact upstream commit and software version;
- [ ] record protocol and P2P versions;
- [ ] compare native DePIN transaction schemas and signature contexts;
- [ ] run `cargo test --workspace`;
- [ ] run clippy with warnings denied;
- [ ] run a 4-validator local testnet;
- [ ] complete enroll -> heartbeat -> contribution -> attestation -> receipt verification;
- [ ] verify restart/catch-up behaviour;
- [ ] review genesis and economic parameter changes separately;
- [ ] update `integrations/tessarq.json`;
- [ ] update this document;
- [ ] retain the previous compatibility snapshot in Git history.
