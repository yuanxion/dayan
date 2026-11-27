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
workflow below. Local fix commits follow the standing authorization below.
Neither mode pushes or submits changes unless the user explicitly asks.

## Operating rules

- Unless the user explicitly requests a broader scope, apply their requests,
  preferences, and reusable knowledge only to the current workspace. Save them
  inside this repository; do not create or modify cross-workspace personal
  instructions or memory without an explicit request.
- Use Python for new data processing, log/CSV analysis, validation scripts,
  and bulk text-processing helpers. Do not use Perl for subsequent work.
  Preserve historical scripts/results unless replacement is explicitly needed.
- The user authorizes local commits after a requested fix, feature, or
  performance improvement is genuinely resolved and focused checks pass. Do
  not require another request to commit that verified change. Commit only the
  relevant code/tests, preserve unrelated
  staged changes, and report the commit hash and owning repository. This is
  workspace-local authorization, not permission to push, amend, or submit.
- Output equivalence does not establish model-answer correctness. Inspect and
  link the verbatim output; distinguish token-limit truncation, unfinished
  thinking, completed-answer quality, and offload/non-offload equivalence.
  Do not claim the whole output problem is fixed from equality alone or commit
  unverified diagnostic candidates as completed fixes.
- In every model-output result or status report, link the exact raw output for
  each tested mode and the named golden directly in the response. A report or
  log link alone is not enough. State whether each mode matches the golden
  separately from same-host equivalence, and show the first difference when
  available. See the [model output FAQ](../knowledge/model-output-faq.md).
- When a no-offload baseline has already been measured, lock its exact output
  files and runtime before changing code. Do not change no-offload numerics to
  make offload outputs agree. Validate both the new no-offload and offload
  outputs against that original baseline, not only against each other. For
  MiniCPM5 here, the user's golden is
  `tasks/1123-moe_offload/outputs/debug-offload85-20261123/resident-fused-complete-runtime.*.txt`.
- When a local commit is requested, use `git commit -s`. Keep the commit
  subject a short, clear single-line description; avoid long message bodies
  apart from the generated Signed-off-by trailer. For this user's local
  commits and requested rebase/replay work, use author and committer identity
  `yuan.xiong <yuan.xiong@intel.com>` and retain the Signed-off-by trailer.
  Never use `git commit
  --amend` unless the user explicitly requests it. Make one commit per feature,
  and keep functional changes and debug/logging changes in separate commits.
  Keep feature, bug-fix, and performance commits first; put optional debug,
  logging, tracing, and profiling commits at the end of the series. Split
  mixed commits by behavior, including their tests and build wiring, rather
  than classifying only by filename or commit title. Functional code must not
  depend on the optional diagnostic tail. Verify that the functional-only
  revision builds and passes focused checks, and that replaying the diagnostic
  patches restores the intended full tree. Keep diagnostic commits exportable
  individually with `git format-patch` and replayable in order with `git am`;
  document dependencies between those patches. This lets the user remove the
  diagnostic tail for submission and reapply it only when debugging. Do not
  rewrite history or remove that tail without a user request; preserve a
  recovery ref before any authorized history rewrite.
  The standing authorization above covers verified local fixes, features,
  and performance improvements only; other
  commits and all pushes still require an explicit user request.
- For OpenVINO reference/base requests, load the `openvino-build` skill and
  check `artifacts/openvino-reference/<full-commit>/` before switching source
  revisions or rebuilding. Reuse a checksum-verified compatible cache; rebuild
  only when it is absent, incompatible, or explicitly requested. Keep native
  C++ and Python environments/results distinct. Do not overwrite cached bases.
- For MiniCPM5 offload tests in this workspace, default to offload ratio 85
  unless the user explicitly requests another ratio. Preserve earlier 90%
  results; do not change LES/cache/prefetch strategy just to align outputs.
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
- When reporting results in any mode, use detailed tables with a commit column
  on every result table. Include relevant configuration columns such as offload
  ratio, model, input-token file/source and selected record, actual input/output
  token counts, LES mode, and iteration counts. Identify uncommitted patches
  separately from the base commit; never present a base commit as a committed
  patched revision. Include saved build/runtime paths and provenance when relevant.
- In Complex mode, save only confirmed, reusable knowledge in `knowledge/` or
  `skills/`. Keep task-specific notes in `tasks/`; do not store secrets or raw
  conversation logs.
- Respect the instructions and Git state of nested repositories. Never clean,
  reset, or overwrite unrelated work.
- For pip commands in this Intel environment, pass the verified proxy per
  command: `--proxy http://child-prc.intel.com:913`. The reversed hostname
  `prc-child.intel.com` does not resolve. Do not change global pip settings or
  disable TLS verification unless explicitly requested.

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
- In both Simple and Complex modes, proactively give brief progress updates
  during long work without waiting for the user to ask. Aim for an update
  every 30-60 seconds when the host provides
  control. State the current stage, verified progress or process state, and the
  next action; do not invent an ETA or equate build-step counts with time remaining.
- When performance comparison is requested after a build, the build alone is
  not completion. Run the agreed comparisons and report measured timings,
  configurations, repetitions, and correctness separately.
- Explicitly distinguish still running, completed, failed, and blocked. Do not
  use completion-style wording while requested work remains running or unfinished,
  or imply it stopped merely because no new output appeared. On a status question,
  report actual state and continue unless the user asks to pause or stop.
- Instructions cannot guarantee response latency while the host or a tool is
  blocking. Disclose that limit and report progress promptly at the next available
  control point; do not claim a guaranteed background timer, automatic continuation,
  or a stop without host support or evidence.