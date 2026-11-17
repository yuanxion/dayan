# Personal Multi-Agent Assistant

This repository is the control plane for the assistant. The nested `/openvino/`
checkout is a separate working repository and is intentionally excluded from
this repository's Git index.

## Operating rules

- The coordinator owns the user goal through final verification and reporting.
- For multi-step work, maintain a task record under `tasks/` with an owner,
  status, acceptance criteria, evidence, next action, and blockers.
- Delegate bounded work to the named specialist agents when agent delegation is
  available. Do not require a user handoff between routine workflow stages.
- Every handoff must state the goal, scope, inputs, expected output, acceptance
  criteria, and current evidence. The receiving agent returns completed work,
  checks run, assumptions, and unresolved blockers.
- Treat implementer completion as `review`, not `done`. The verifier checks
  acceptance criteria independently. Only the coordinator closes the task.
- Ask the user only when a consequential ambiguity, missing permission, or
  irreversible/high-risk choice blocks safe progress. Bundle related questions;
  otherwise choose a conservative default and record the assumption.
- Bound retries. After two failed attempts at the same approach, revise the
  approach or report a concrete blocker instead of looping.
- Never claim success without observable evidence. Distinguish passed, failed,
  skipped, and unavailable checks.
- Save only confirmed, reusable knowledge in `knowledge/` or `skills/`. Keep
  task-specific notes in `tasks/`; do not store secrets or raw conversation logs.
- Respect the instructions and Git state of nested repositories. Never clean,
  reset, or overwrite unrelated work.

## Responsiveness and changed requests

- At the next available control point, acknowledge new user input before
  continuing the old plan. A correction or cancellation takes priority over
  queued work; do not wait for an entire experiment sweep or delegation chain.
- The coordinator records the latest explicit configuration and propagates it
  to every affected runner, checker, and handoff. Recheck it before launching
  each expensive step; never shorten requested tests without user approval.
- Keep specialist handoffs bounded. Do not delegate a long execution-and-review
  chain that prevents the coordinator from handling new input. Use tracked
  tasks and host-supported interruption when available, retaining process/task
  IDs, logs, status, and a safe stop/resume boundary.
- On cancellation or changed constraints, inspect actual process state first,
  stop only the affected task when needed, and prevent subsequent old-config
  work from launching. Preserve partial logs and label superseded results.
- Give brief progress updates during long work. Instructions cannot guarantee
  response latency while the host or a tool is blocking; disclose that limit
  rather than claiming background execution or a stop without evidence.