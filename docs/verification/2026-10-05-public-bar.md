# Public example verification — 2026-10-05

This report records the local acceptance of commit
`27230be3eb3fb1533181bed5480bfb94e761e61a` on 2026-10-05 in
America/Los_Angeles. The all-lanes report was generated at
`2026-10-06T03:55:45Z` by public-bar `1.1.3`.

## Result

| Criterion | Result | Proof |
| --- | --- | --- |
| 1. Runs | PASS | Expanso Edge v2.1.21 matched all 3 expected replay records, and the secured runtime produced all 7 broker outputs. |
| 2. Platform | PASS | Compose and MQTT declarations passed; TLS, generated authentication, named volumes, pinned images, non-root services, read-only filesystems, and dropped capabilities were exercised. |
| 3. Structure | PASS | Explanation, six fixture-backed stages, run instructions, and Cloud deployment instructions were found. |
| 4. Usability | PASS | Light and dark passed at 320, 400, 768, and 1440 pixels with no horizontal overflow, WCAG AA contrast, or axe violations. Keyboard paging, JSON formatting, and local copy/download feedback passed. |
| 5. Regressions | PASS | The retained-feature manifest and initial baseline passed. Ignition's removed runtime behavior is retained by the direct OPC UA and Sparkplug publisher. |

## Commands

Repository gate:

```bash
just check
```

The command passed Expanso validation, Compose rendering, XML validation,
ShellCheck, fixture consistency, protobuf decoding, JavaScript syntax,
anti-slop checks, rendered browser checks, and secured runtime acceptance.

Shared public-bar self-test:

```bash
uv run -s .demo-kit/public-bar.py --selftest
```

The self-test accepted both known-good repositories and rejected each of the
five criterion-isolated failure repositories under the expected criterion.

All-lanes public-bar proof:

```bash
PUBLIC_BAR_AXE_PATH="$PUBLIC_BAR_AXE_PATH" \
  uv run -s .demo-kit/public-bar.py \
  --repo . \
  --manifest public-bar.toml \
  --report artifacts/public-bar.md \
  --lane all \
  --base-ref origin/master
```

Result: criteria 1 through 5 passed. The checker also confirmed that every
declared service and browser host was stopped during teardown.

Workflow syntax and vendored-kit drift:

```bash
actionlint .github/workflows/public-bar.yml
uv run -s ../_demo-kit/sync-public-bar.py . --check
```

Both commands passed. The vendored lock records demo-kit commit
`2b2fac927f2c8eb39d6e15cb00d06cc2ffb6cbfe`.

## Pipeline evidence

The input fixture SHA-256 was
`fde2b3e94d51cddca909219a50f8fffb9a7602dc89653c9c2ca28e6ff9ab7224`.
The expected output SHA-256 was
`10977292c0833069e7d842984653985742d578404d9c2dbcd9df677f8135dbf0`.
The Edge replay output SHA-256 was
`f834f2f2f327034c2052f85cc0639a930ddefdb4f765296ee18dc8364b738532`.

The secured MQTT verifier observed:

- 2 primary Sparkplug B protobuf records;
- 2 gzip archive records that decoded to the primary records;
- 2 JSON metrics records;
- 1 quarantine JSON record for the out-of-range temperature;
- only `DoorSensor` in sequence 18 after stateful deadbanding;
- an accepted authenticated TLS connection;
- a rejected anonymous TLS connection; and
- a retained marker after the HiveMQ container was recreated, proving that
  broker state survived in the named volume.

The local Compose lane proves the shipped processing configuration and secured
broker path. It does not claim an Expanso Cloud execution. Production lifecycle
and assignment remain Cloud-managed as described in the README.

## Runtime pins

| Component | Pin |
| --- | --- |
| Expanso Edge | `v2.1.21@sha256:2a9ec67c90075b0bf33811232971cd4ee03326181ed4186c799986cf9d371b38` |
| Expanso CLI | `v2.1.21@sha256:d46fc6f21bbb1e53df800b2f89bca6a20b9cb116984fec336a47f7490161189d` |
| HiveMQ CE | `2025.5@sha256:7ae39e84654a41ced6e946dd84f131d508bc2b862ec96265b7f23d241db214da` |
| Mosquitto | `2.0.22@sha256:199ea8ef2e35ec2b1b37e59cfd1dbae538ed4dfa4a2251a121a52215a6248a21` |
| Nginx | `1.27.5-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10` |
| Alpine init base | `3.22.2@sha256:4b7ce07002c69e8f3d704a9c5d6fd3053be500b7f1c69fc0d80990c2ad8dd412` |

At completion, ports `8877`, `8883`, and `8888` had no task-owned listeners,
and `docker compose ps -a` returned no project containers.
