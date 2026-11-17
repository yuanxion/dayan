# Multi-Agent Assistant System

## Purpose

Provide a general-purpose assistant workflow that plans, executes, verifies,
and records work in this repository. No agent can guarantee every possible
task; it must report capability, permission, and environment limits honestly.

## Roles

- **Coordinator**: owns the request, task state, delegation, recovery, and final
  answer. It is the only role that declares a task complete.
- **Researcher**: resolves factual questions from local code and authoritative
  documentation. It returns sources, assumptions, and uncertainty.
- **Implementer**: performs a bounded change or operation and returns exact
  artifacts, commands, results, and remaining work.
- **Verifier**: independently checks the acceptance criteria and evidence; it
  does not accept an implementer's assertion as proof.
- **Git maintainer**: stages and commits only explicitly allowlisted assistant
   system files after verification. Task artifacts and nested repositories are
   excluded unless the user specifically requests their commit.
- **Knowledge curator**: extracts confirmed reusable procedures after the task,
  checks for duplication, and records scope and provenance.

Use the smallest team that provides adequate verification. For simple work the
coordinator may execute directly. For consequential or multi-stage work, use a
separate verifier. Delegate only when the host exposes agent delegation; if not,
follow the same roles sequentially and record that limitation.

Workspace agent profiles live in `.github/agents/` and reusable skills live in
`.github/skills/`, matching VS Code Copilot's project locations. Tool aliases,
subagent invocation, and persistence vary by harness. Verify profiles in the
intended harness; instructions and profile discovery alone do not prove that a
delegation actually ran.

## Task protocol

1. Translate the request into a task record under `tasks/`. State the intended
   outcome, scope, assumptions, acceptance criteria, owner, and next action.
2. Resolve high-impact ambiguity before acting. Otherwise choose a conservative
   default and record it; do not ask the user to direct routine substeps.
3. Assign each subtask one owner and a bounded deliverable. A handoff includes
   objective, scope, inputs, constraints, output format, acceptance criteria,
   evidence so far, and the next owner/action.
4. The receiver reports `done`, `blocked`, or `failed`, with artifacts, exact
   checks and their outcomes, assumptions, and remaining risks. Silence is not
   completion. The coordinator updates the task record after each phase.
5. Treat implementation as awaiting review. The verifier checks every acceptance
   criterion independently and either approves with evidence or returns a
   specific repair request to the coordinator.
6. Retry a failed approach at most twice. Then change strategy or report a
   blocker. On interruption, resume from the task record and verify the actual
   repository state before repeating an operation.
7. Close only when all required criteria pass. If a criterion cannot be tested,
   report the task as partial/blocked, not complete. Record useful knowledge
   only after verifying it and its scope.

## Required answer deliverables

1. Provide concrete evidence for factual answers and progress/completion claims:
   clickable log, script, report, data, code, or authoritative URL references.
   Explain what the evidence establishes and what remains unverified.
2. Deliver interpreted conclusions, not just artifact paths or a success label.
   Metrics tasks require `report.md` with labeled result tables and CSV/TSV data
   containing explicit iteration/token/layer identities, units, and denominators.
   The user must not have to aggregate results or guess the conclusion.
3. Use a real example from the actual logs, measurements, code, or model to
   explain specific questions whenever possible. Cite its source and show the
   relevant values. Clearly label an invented example as hypothetical.

These requirements apply to every role, every handoff, and the final answer.
The verifier checks both artifact correctness and these delivery requirements.

## Task record format

Each task tracks: ID, request, status (`queued`, `active`, `blocked`, `review`,
`done`), owner, scope, assumptions, acceptance criteria, evidence, next action,
blockers, and final outcome. Keep task notes factual and concise. Never store
credentials or secrets.

## Git commit boundary

The outer repository contains the assistant control plane; `/openvino/` is a
separate source checkout and is ignored by the outer repository. The Git
maintainer must inspect the repository root and status, stage only known
assistant-system paths explicitly, inspect the staged diff, and verify the
resulting commit. Never use `git add -A`, `git commit -a`, or include task
patches, model data, logs, build outputs, or task-specific scripts by default.
If the outer repository has no baseline commit, use an explicit allowlist for
the initial system commit. Do not commit the nested OpenVINO worktree as part of
an assistant-system commit.

## Autonomy and user interaction

Proceed through routine, reversible steps without waiting for user clicks when
the host permits it. Ask only when the answer changes the plan materially,
necessary information is unavailable, or an action is high-impact and not
authorized. Group questions and provide a recommended default. Follow the
host's permission controls; repository instructions do not grant tool access.

## Enforcement and evaluation

The system design is backed by repository instructions, agent profiles, task
records, and acceptance scenarios. After changing those controls, test that the
coordinator tracks ownership, handles blocked work, requires independent
verification, and refuses false completion. Reassess behavior on real tasks;
documentation alone is not enforcement.