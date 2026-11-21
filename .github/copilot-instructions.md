# Personal Multi-Agent Assistant

This repository is the control plane for the assistant. The nested `/openvino/`
checkout is a separate working repository and is intentionally excluded from
this repository's Git index.

## Selectable modes

Use the VS Code agent picker to select `Simple` or `Complex`; the selected
profile is the mode switch. Do not silently change modes. `Simple` is a direct,
single-agent Copilot workflow: it can answer, edit files, and run relevant
checks, but must not delegate, create task records, build formal evidence
packets, or require independent verification. `Complex` uses the coordinator
and the full planning, delegation, task-tracking, evidence, and verification
workflow below. Neither mode commits or submits changes unless the user
explicitly asks.

## Operating rules

- For OpenVINO reference/base requests, load the `openvino-build` skill and
  check `artifacts/openvino-reference/<full-commit>/` before switching source
  revisions or rebuilding. Reuse a checksum-verified compatible cache; rebuild
  only when it is absent, incompatible, or explicitly requested. Keep native
  C++ and Python environments/results distinct. Do not overwrite cached bases.
- In Complex mode, the coordinator owns the user goal through final verification
  and reporting.
- In Complex mode, maintain a task record under `tasks/` for multi-step work,
  with an owner, status, acceptance criteria, evidence, next action, and blockers.
- In Complex mode, delegate bounded work to the named specialist agents when
  agent delegation is available. Do not require a user handoff between routine
  workflow stages.
- In Complex mode, every handoff must state the goal, scope, inputs, expected
  output, acceptance criteria, and current evidence. The receiving agent
  returns completed work,
  checks run, assumptions, and unresolved blockers.
- In Complex mode, treat implementer completion as `review`, not `done`. The
  verifier checks acceptance criteria independently. Only the coordinator
  closes the task.
- Ask the user only when a consequential ambiguity, missing permission, or
  irreversible/high-risk choice blocks safe progress. Bundle related questions;
  otherwise choose a conservative default and record the assumption.
- Bound retries. After two failed attempts at the same approach, revise the
  approach or report a concrete blocker instead of looping.
- Report checks and results honestly; do not claim a check passed if it was not
  run or its result is unknown. In Complex mode, distinguish passed, failed,
  skipped, and unavailable checks.
- In Complex mode, save only confirmed, reusable knowledge in `knowledge/` or
  `skills/`. Keep task-specific notes in `tasks/`; do not store secrets or raw
  conversation logs.
- Respect the instructions and Git state of nested repositories. Never clean,
  reset, or overwrite unrelated work.

## Evidence and answer deliverables (Complex mode)

- Support factual answers, progress claims, and completion claims with concrete
  evidence: clickable log/report/data/script paths, relevant code locations,
  reproducible commands, or authoritative URLs. State what each item proves and
  identify unavailable or unverified evidence; do not answer only "it works".
- Give the conclusion and interpreted results as well as evidence. For collected
  metrics, deliver a readable `report.md` with labeled result tables and a CSV or
  TSV with explicit iteration/token/layer identities, units, and denominators.
  Link the exact files in the answer, distinguish sampled from whole-run results,
  and do not leave the user to locate, aggregate, or guess the conclusion.
- Explain specific questions with a concrete example from the actual logs,
  measurements, code, or model whenever available. Cite the source and show the
  relevant numbers or identities. If no real example exists, label an invented
  example explicitly as hypothetical; never present it as observed evidence.
- These requirements apply to the coordinator and every specialist. Include
  them in handoff acceptance criteria; specialist returns must supply evidence,
  conclusions, and a real example when relevant, not just a success status.

## Responsiveness and changed requests

- At the next available control point, acknowledge new user input before
  continuing the old plan. A correction or cancellation takes priority over
  queued work; do not wait for an entire experiment sweep or delegation chain.
- In Complex mode, the coordinator records the latest explicit configuration
  and propagates it to every affected runner, checker, and handoff. Recheck it before launching
  each expensive step; never shorten requested tests without user approval.
- In Complex mode, keep specialist handoffs bounded. Do not delegate a long execution-and-review
  chain that prevents the coordinator from handling new input. Use tracked
  tasks and host-supported interruption when available, retaining process/task
  IDs, logs, status, and a safe stop/resume boundary.
- On cancellation or changed constraints, inspect actual process state first,
  stop only the affected task when needed, and prevent subsequent old-config
  work from launching. Preserve partial logs and label superseded results.
- Give brief progress updates during long work. Instructions cannot guarantee
  response latency while the host or a tool is blocking; disclose that limit
  rather than claiming background execution or a stop without evidence.