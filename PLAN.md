# Container-Native Broker Work Plan

> **Status:** This is a tracked planning artifact. Broker work is deferred by [docs/development-strategy.md](docs/development-strategy.md). No implementation or deployment is authorized by this plan.

## Goal

Define the next safe work needed to establish a container-native broker boundary for controlled runtime communication, with production behavior gated behind explicit approval and validated using synthetic inputs only.

## Current Boundary

- This document records planning scope only; no implementation or deployment is authorized by this plan.
- The broker boundary must remain explicit, least-privileged, and fail-closed when required inputs, approvals, or runtime dependencies are absent.
- Planning and acceptance must use public-safe descriptions and synthetic evidence. No source access, private evidence, identities, credentials, provider procedures, or account procedures are part of this plan.

## Container-Native Workstreams

### 1. Runtime Contract

- Define the broker's container-facing protocol, message envelope, lifecycle states, and failure responses.
- Specify health, readiness, timeout, retry, shutdown, and restart behavior.
- Define resource, network, and filesystem boundaries so the broker does not depend on undeclared host state.
- Document configuration defaults, validation rules, and explicit behavior for missing or malformed values.

### 2. Secret and Approval Boundary

- Define how secret-bearing operations are isolated from ordinary broker traffic.
- Require explicit, durable approval before any operation can cross into a production-capable path.
- Ensure secrets are never exposed in logs, responses, fixtures, images, or generated artifacts.
- Define audit events using metadata only, without raw secret values or private source data.

### 3. Production Implementation Only After Approval

- Do not implement production-capable integrations until the runtime contract and approval boundary are reviewed and explicitly authorized.
- After approval, implement the smallest container-native slice that satisfies the approved contracts.
- Keep production configuration, credentials, external endpoints, and account-specific procedures outside public documentation and synthetic test fixtures.
- Add rollback and disable behavior before enabling any production-capable path.

### 4. Synthetic Acceptance

- Build deterministic tests with synthetic messages, placeholder configuration, and disposable container resources.
- Verify protocol validation, authorization and approval gating, fail-closed behavior, retries, timeouts, restart recovery, and redacted audit output.
- Verify that unauthorized or malformed requests cannot reach production-capable handlers.
- Record only reproducible, public-safe acceptance results; do not claim validation of external systems or private sources.

### 5. Separate Source Authorization

- Treat any request to connect the broker to a real source, provider, account, or private dataset as a separate authorization decision.
- Before such work, define scope, owner, data classification, retention, access controls, and revocation conditions.
- Keep source authorization and operational credentials out of this public-safe plan.

## Explicit Prohibitions

- Do not access, enumerate, or reproduce private sources, accounts, provider consoles, credentials, tokens, or host-specific state as part of this plan.
- Do not deploy, enable, or exercise production-capable broker behavior without explicit approval.
- Do not use real secrets or raw external data in tests, fixtures, logs, images, documentation, or artifacts.
- Do not weaken container isolation, approval gates, authentication, authorization, or fail-closed behavior for convenience.
- Do not update manifests, publication-boundary metadata, tracking state, or unrelated files under this plan.

## Completion Gates

1. The runtime contract is written, reviewed, versioned, and validated for container-only operation.
2. The secret and approval boundary is documented, tested, and shown to fail closed.
3. Synthetic acceptance covers normal, malformed, unauthorized, timeout, restart, and recovery paths.
4. Production implementation has separate explicit approval, scoped credentials, rollback, and disable procedures.
5. Any external source connection has separate authorization and documented data-handling controls.
6. Public-safe documentation and artifacts contain no secrets, private evidence, identities, account procedures, or raw external data.
7. This plan remains untracked unless the user separately authorizes tracking or manifest updates.
