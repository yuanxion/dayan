# OpenCL and LES Perfetto debugging

## Working collection path

The local OpenCL Intercept installation is `artifacts/opencl-intercept-itt/`.
Its build enables `ENABLE_ITT=ON` and uses `steady_clock`. Do not replace the
system OpenCL loader; the runner preloads Intercept only into the benchmark
and forwards to `/lib/x86_64-linux-gnu/libOpenCL.so.1`.

Intercept's ITT support emits OpenCL tasks to an ITT collector; it does not
capture arbitrary OpenVINO ITT tasks as JSON. OpenVINO exports its own LES
JSON via `OV_GPU_LES_TRACE`, and the merge script aligns that trace with
Intercept's `clintercept_start_time` metadata. Both clocks use microseconds;
LES timestamps are absolute and Intercept timestamps are relative.

Native GPU event profiling stalled during LES warmup on this host. The
verified fallback is OpenCL API-only plus LES JSON, not GPU kernel/DMA timing:

```bash
bash tasks/017-timestamp-logging/profile.sh NEW_NAME opencl --api-only
```

Always use a new output name. Keep failed/partial results and do not confuse
them with successful model completion. Intercept's raw trace covers the whole
benchmark; selected-window merging reduces the delivered JSON, not the raw
collection or the benchmark length.

## Request and token selection

The runner retains 958 input tokens, 256 output tokens, warmup 1 and measured 3.
`LES_LOG_REQUEST=measured:0` selects the first measured request, not warmup.
`LES_LOG_TOKEN_ID` uses one-based decode selectors; JSON `token_index` is
zero-based. Selector 2 therefore yields UI `token_index: 1`. Prefill is not
a single-token LES decode phase; do not identify JSON decode index 0 as prefill.

```bash
LES_LOG_REQUEST=measured:0 LES_LOG_TOKEN_ID=2 LES_TRACE_SELECTED_WINDOW=1 \
    bash tasks/017-timestamp-logging/profile.sh NEW_NAME opencl --api-only
```

This was verified to produce exactly one token track and 40 layer windows,
with all LES event requests equal to `measured:0` and token indices equal to 1.
Defaults remain measured:0 and selectors 1-8 unless explicitly overridden.

## Event and UI semantics

Perfetto's horizontal axis is time; its vertical axis consists of tracks.
LES phase titles contain token/layer identifiers. Expert tracks contain
layer, expert and slot; slots can be reused, so a slot alone is not an expert
identity. Load generation and immutable origin context identify individual
reservations even after prefetch-to-demand takeover or later tokens.

Phase args contain `layer_index`, `next_layer_index`, `current_layer` and
`next_layer`. Each layer has LRU IDs, actual top-k IDs, prediction IDs,
ready/inflight/missing IDs and `cache_events`. Unknown arrays stay empty;
predictions are never substituted for actual top-k. The last layer has no
next layer, represented by null and empty next-layer arrays.

JSON lifecycle events are `expert_reserved`, `expert_enqueued`,
`expert_copying` and `expert_completed`. Cancellation/failure/eviction are
not exported by this configuration, and must not be fabricated as completion.
Host loading spans can include file reads and waits; they are not pure DMA.

Separate phase and layer/slot/expert tracks prevent non-nested overlaps with
OpenCL API slices. Intercept may emit string-valued `sort_index`; the merger
normalizes it to a number for Perfetto. Validate with the actual Perfetto
trace processor, not just a JSON parser: check `stats` for positive error
values, including parser failures and overlapping complete-event spills.

## LES correlation and flow navigation

The merger adds `LES.correlation` flow pairs from LES scopes to OpenCL
enqueue slices. Phase association uses the original CPU thread and phase
interval; expert copy association additionally resolves the worker through
the load's target layer, expert and generation. API args expose `les_context`
and the association method. Commands on unrelated threads are not linked by
time proximity alone. These arrows describe CPU-side scope ownership, not
GPU execution or OpenCL dependency edges.

In Perfetto, open a flow-enabled JSON and select a LES phase or expert-host
copy slice. Connected arrows appear on the timeline; the details panel has
`Following Flows` and/or `Preceding Flows`, with clickable destination/source
slices. `]` follows the focused outgoing flow and `[` follows an incoming
flow. Ctrl+] / Ctrl+[ cycles branches on Linux/Windows; macOS uses Command.
With an area selected, the `Flow Events` tab lists categories and `Show`
checkboxes. Enable `LES.correlation` or `All` to show area flows. Avoid
showing all flows over a large window. These names/shortcuts were checked
against the official Perfetto v59.1 UI source, not a local browser screenshot.

Intercept's native CPU-to-GPU flow requires `ChromeCallLogging`,
`ChromePerformanceTiming` and `ChromeFlowEvents`. Its non-InStages branch
emits flow endpoints; the current InStages implementation does not emit
device flow endpoints. The runner therefore defaults `LES_TRACE_GPU_STAGES`
to 0; an explicit 1 restores staged rendering without promising native flows.

Native device profiling can emit real kernel spans yet leave the LES model
blocked in driver memcpy/event-wait paths during warmup. Partial GPU output
is not a successful selected decode capture. A tested flush-after-barrier
diagnostic did not resolve this; do not claim GPU profiling is impossible
globally or that the LES compatibility issue is fixed. Keep timeout/stop
diagnostics and do not repeat the same failed configuration indefinitely.

## Timing and clean performance

The runner records full launcher wall time in `NEW_NAME.walltime.txt` using
`/usr/bin/time`. It includes startup, warmup and all measured requests.
Reference launcher timing also includes its cached-payload verification.
The Perfetto summary label shows this wall time, but its bar covers the
selected window and is explicitly marked not to scale. A selected trace's
viewport duration is not whole-program runtime.

For clean performance, use `LES_LOG_MODE=off LES_GPU_PROFILE=0`; the runner
clears CSV/debug selectors, ITT/LES JSON flags and OpenCL preloading. Compare
sequential complete reference and LES runs using the preserved compatible
reference cache rather than switching source revisions. Check all four
958/256 requests and measured0 text equality with `analyze_decode.py`.
One three-request sequential comparison is not proof of stable speedup.

Implementation entry points: [runner](../tasks/017-timestamp-logging/run.sh),
[collector](../tasks/017-timestamp-logging/profile.sh),
[merger](../tasks/017-timestamp-logging/merge_opencl_trace.py).