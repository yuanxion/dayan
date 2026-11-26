# VTune Linux collection prerequisites

Use the user-specified VTune installation:
`/home/openvino-288v002/yuanx/tools/oneapi/vtune/latest/bin64/vtune`.
It reports2026.6.0 (build633341) on2026-11-22. The older installation at
`/opt/intel/oneapi/vtune/latest` reports2025.7; do not use it by default.

The reusable [profile script](../tasks/017-timestamp-logging/profile.sh) checks
ptrace_scope before every collection and sets it to0 with `sudo -n tee` only
when needed. The user explicitly authorized this recurring preparation; do not
ask for permission again. Noninteractive sudo can still require credentials:
if it fails, the user must enter their password directly in a terminal. Never
ask for or transmit passwords through chat, or retry sudo interactively.

On2026-11-22 the user executed the command successfully, and the assistant
verified the actual ptrace_scope value was0.

```bash
bash tasks/017-timestamp-logging/profile.sh vtune-new-cpu hotspots
bash tasks/017-timestamp-logging/profile.sh vtune-new-gpu xpu-offload
```

Names must be new. `--check` as the third argument validates prerequisites
without running a model. `VTUNE_ROOT` can explicitly select another installation.
VTune2026 replaces the deprecated `gpu-offload` analysis with `xpu-offload`;
the script accepts the old spelling as an alias. Use `-data-limit=0`: the default
1000MB limit can detach collection before the benchmark ends. Keep benchmark
completion and collection coverage separate. The script disables that limit.

## ptrace policy

When VTune reports that the scope of the `ptrace` system call is limited,
check `/proc/sys/kernel/yama/ptrace_scope`. This host was observed at1, and
both software hotspots launch and process attach were rejected by VTune.

The user-approved temporary workaround is:

```bash
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
cat /proc/sys/kernel/yama/ptrace_scope
```

This relaxes a system-wide tracing restriction. Record the previous value and
restore it after collection when appropriate. Do not make persistent sysctl
changes without authorization. If sudo needs a password, the user must enter it
directly in the terminal; never request or transmit passwords through chat.
`sudo -n true` can check noninteractive privilege availability without prompting.

An earlier `sudo -n true` check required a password; this was resolved by the
user setting ptrace_scope in their terminal. Recheck actual state each time.

## Independent GPU collection prerequisite

Changing ptrace_scope fixes only the ptrace restriction. GPU-offload also reported:
`Current OS kernel does not support driverless collection on hybrid CPUs`.
GPU hardware collection may additionally require an administrator-installed VTune
sampling driver or a supported OS kernel. Do not assume ptrace_scope0 resolves it.

Software CPU hotspots is a separate fallback, with explicit CPU-only conclusions:

```bash
/home/openvino-288v002/yuanx/tools/oneapi/vtune/latest/bin64/vtune \
  -collect hotspots -knob sampling-mode=sw -knob enable-stack-collection=true -data-limit=0 \
  -result-dir tasks/017-timestamp-logging/vtune-new-cpu \
  -- /usr/bin/env OV_GPU_LES_ITT=details LES_LOG_MODE=details \
     LES_LOG_STEM=vtune-new-cpu bash tasks/017-timestamp-logging/run.sh
```

Use a new result/output name. The runner retains warmup1/measured3 and958 input/
256 output tokens. Detailed ITT adds exact layer/cache snapshots and diagnostic
overhead; use `LES_LOG_MODE=itt` for lightweight ITT and `LES_LOG_MODE=off` for
clean timing. Never interpret CPU-only data as a GPU hardware timeline.

Historical2025.7 failures: [GPU collection](../tasks/017-timestamp-logging/vtune-itt-details.collect.log),
[software collection](../tasks/017-timestamp-logging/vtune-itt-cpu.collect.log),
[attach](../tasks/017-timestamp-logging/vtune-barrier-stall.collect.log).

## Confirmed2026 CPU collection

[Collection log](../tasks/017-timestamp-logging/vtune-2026-cpu.collect.log) and
[summary](../tasks/017-timestamp-logging/vtune-2026-cpu.summary.txt) confirm
successful software sampling with ITT and stacks. Both collector and benchmark
exit0. However, collection detached at104.046s because of the1000MB raw-data
limit; this is a partial profile. The benchmark still completed warmup1/measured3,
958/256, and its strict CSV event-coverage validation passed for320 windows.
Do not present its TPOT126.60ms/token as clean performance.

[Task TSV](../tasks/017-timestamp-logging/vtune-2026-cpu.tasks.tsv) contains
unquoted multiline labels. Plain DictReader splits labels into pseudo-records
and can falsely show zero task counts. The existing
[analysis parser](../tasks/017-timestamp-logging/analyze_decode.py) reconstructs
the complete label before reading metrics. It verifies5305 numbered tasks,
including320 stream-finish tasks averaging855.86us and320 top-k-readback tasks
averaging402.01us. These are host-task wall times, not GPU kernel durations.

Release plugin addresses lack complete debugging symbols. An addr2line nearest
symbol is not enough to name an unresolved hotspot; report it as unresolved
unless a matching binary/build ID and usable symbols establish attribution.

The [metadata report](../tasks/017-timestamp-logging/vtune-2026-cpu.metadata-tasks.tsv)
does not expose token_layer values for the numbered tasks. Do not claim packed
metadata was validated in VTune; use independently validated CSV identities.

## Confirmed2026 GPU limitation

[XPU-offload](../tasks/017-timestamp-logging/vtune-2026-xpu.collect.log) launched
and captured GPU API/kernel activity, but warmup aborted with
`clFinish: CL_OUT_OF_RESOURCES(-5)`; benchmark exit134, collector exit4.
The2.0GB result and645.040s elapsed time are failed-workload data, not valid
decode measurements. Do not calculate decode GPU idle percent from them.

A bounded [API-only retry](../tasks/017-timestamp-logging/vtune-2026-xpu-api.collect.log)
used `--api-only`, disabling ITT tasks and detailed logging without shortening
the958/256 warmup1/measured3 workload. It also aborted during warmup with
`CL_OUT_OF_RESOURCES(-5)`, including oneDNN's OpenCL kernel.cpp:196 error.
The failure is therefore not explained by detailed ITT alone. Do not repeat
this configuration or install drivers without authorization. CPU software
sampling remains the working fallback; GPU runtime/tracer compatibility needs
separate investigation. The observed OpenCL driver is25.40.35563.4.

## Tested decode hypothesis

Moving actual top-k readback before prediction retained stream.finish and all
barriers, passed120 neighboring tests and full model output validation, but
clean candidate TPOT110.60ms/token exceeded original-control106.13ms/token.
One run per variant is not a stable regression estimate; no speedup was shown,
so the change was reverted. Do not cite anomalous post-XPU baseline249.89 as
a speedup denominator. See [analysis](../tasks/017-timestamp-logging/vtune-analysis/report.md).

## Reference XPU isolation passed

The checksum-verified native reference at
`artifacts/openvino-reference/caa59b5b8a3874d2b7cb0651a56e99a9f38dc450/`
was reused without recompiling or switching the active checkout. Reproduce with
a new output name:

```bash
bash tasks/017-timestamp-logging/profile.sh new-reference-xpu xpu-offload --reference
```

This selects the cached launcher/libraries, omits LES, disables ITT user tasks
and detailed logging, and keeps958 input/256 output, warmup1/measured3.
[Benchmark](../tasks/017-timestamp-logging/vtune-2026-reference-xpu.benchmark.log)
shows runtime build `caa59b5b8a3`, all four requests and exact measured0 reference
text. Benchmark and collector exited0, with no data-limit truncation or resource
error. [Summary](../tasks/017-timestamp-logging/vtune-2026-reference-xpu.summary.txt)
reports368.118s elapsed and a1.7GB result.
[GPU task TSV](../tasks/017-timestamp-logging/vtune-2026-reference-xpu.gpu-tasks.tsv)
contains MoE gate/up and down kernels with40,800 instances each, totaling6.492764s
and3.512087s respectively. The instance count matches4 requests x255 decode
steps x40 layers. Profiled TPOT184.47ms/token is not clean performance.

Therefore this VTune/native OpenCL tracing chain works on the reference workload.
Earlier failures must not be described as blanket GPU collection unavailability;
the difference involving the LES runtime/path remains to be isolated. The script
also supports `--itt-only`: disable native OpenCL tracing, enable user tasks and
restrict ITT to `ov::intel_gpu`. This tests host labels, not GPU kernel timings.

## LES ITT isolation passed

After the reference check, `--itt-only` completed the LES workload with native
OpenCL tracing disabled. [Collection](../tasks/017-timestamp-logging/vtune-2026-les-itt-only.collect.log)
and benchmark exited0; [summary](../tasks/017-timestamp-logging/vtune-2026-les-itt-only.summary.txt)
reports an11.2GB result. [Task TSV](../tasks/017-timestamp-logging/vtune-2026-les-itt-only.tasks.tsv)
contains5248 numbered host tasks matching5248 CSV records. All320 selected
token/layer windows passed strict event coverage, and full958/256 warmup1/
measured3 matched the reference measured0 output byte-for-byte.

There are320 stream-finish tasks averaging686.70us and320 top-k readback tasks
averaging347.43us. This table has no sampled CPU-time column; the parser leaves
that metric unavailable, not zero. No native GPU execution timing is captured
in this mode. ITT labels work; the earlier failure is associated with enabling
native OpenCL profiling on the LES runtime/path. A precise driver/event/kernel
root cause remains unproven. Do not conflate these isolated successes with a
successful combined LES native-GPU-plus-ITT collection.

## Distinguish the three profiling switches

`enable-user-tasks=true` collects application ITT tasks, including newly added
LES phase labels. `collect-programming-api=true` traces OpenCL host APIs and
device commands. `--itt-only` disables the latter while retaining LES execution
and its new phase labels; it is not a test of old OpenVINO labels alone.
The earlier API-only failure disabled ITT, so it does not establish that the new
ITT labels cause native GPU collection failure.

OpenVINO runtime profiling is a third independent switch. The preserved
[benchmark source](../artifacts/openvino-reference/caa59b5b8a3874d2b7cb0651a56e99a9f38dc450/provenance/benchmark_vlm.cpp#L146)
maps `--profile` to `ov::enable_profiling(true)`.
[Queue construction](../openvino/src/plugins/intel_gpu/src/runtime/ocl/ocl_stream.cpp#L215)
uses that setting for queue profiling, and
[sync selection](../openvino/src/plugins/intel_gpu/src/runtime/stream.cpp#L11)
selects explicit events when profiling is enabled versus barriers for a
nonprofiling out-of-order queue. Do not assume VTune's external instrumentation
changes the runtime's internal sync selection.

The script accepts `--runtime-profile` to test this difference while retaining
native OpenCL tracing and detailed LES ITT. It adds `--profile` without changing
the ordinary benchmark default or cached reference. This is a diagnostic
configuration, not a confirmed fix until collection, workload, output and
joint GPU/ITT task records all pass. Its timings are not clean performance.

The first runtime-profile experiment did not pass: after15minutes the initial
warmup had not completed. The model PID1609439 was stopped with SIGTERM and
[benchmark exit](../tasks/017-timestamp-logging/vtune-2026-les-runtime-profile.exit)
is143. [Thread stacks](../tasks/017-timestamp-logging/vtune-2026-les-runtime-profile.stacks.log)
show the main thread in unresolved Intel OpenCL driver frames; a GPU-plugin
background thread was in a condition-variable wait at that observation. Its
specific LES function was not resolved. This is not an exact
function-level root cause or proof the new ITT labels caused failure.

Editing the shell launcher while its collection command was running caused a
subsequent shell read-position error (`esult-dir: command not found`), launcher
exit127, and overwrite of the external collection text log. Do not mistake127
for a proven VTune collector exit or treat that text log as intact collection
output. The raw result/configuration and model/stacks logs remain. The script
now parses its execution body as a function before running; avoid editing a
live launcher anyway. Never overwrite cached reference binaries or old results.

`--gpu-metrics` tests a different path: GPU hardware metrics enabled, native
OpenCL API tracing disabled, LES and its ITT tasks retained. This could provide
GPU activity alongside CPU phase labels, but it does not provide per-kernel or
transfer-queue event records. The initial `/usr/bin/true` hardware probe reported
`Cannot stop collection of GPU events` and0.000s elapsed despite CLI exit0; it
does not prove valid GPU metric capture. Validate a real workload and positive
hardware metric samples before claiming a usable alternative timeline.

In the failed native-combined configuration, `LOG_REQUEST=measured:0` and
`LOG_TOKEN_ID=1,2,3,4,5,6,7,8` select only the first measured request.
[Phase selection](../openvino/src/plugins/intel_gpu/src/graph/impls/ocl_v2/moe/moe_3gemm_swiglu_opt.cpp#L2016)
requires the current request label to match before setting tracing=true.
The failures occurred during warmup, before these new LES phase ITT tasks
were enabled. Together with failure when ITT was disabled entirely, this is
evidence against attributing the failure to new phase label contents or
taskBegin/taskEnd emission. It does not rule out other runtime, synchronization,
driver or instrumentation interactions introduced by the LES execution path.

The full hardware-metrics-plus-ITT attempt did not complete: model PID1610349
remained in the first warmup for more than11minutes with high CPU usage and
was stopped with SIGTERM. Collector exit4, benchmark exit143. Preserve its
[configuration](../tasks/017-timestamp-logging/vtune-2026-les-gpu-metrics/config/runss.options),
[model log](../tasks/017-timestamp-logging/vtune-2026-les-gpu-metrics.benchmark.log)
and [collection log](../tasks/017-timestamp-logging/vtune-2026-les-gpu-metrics.collect.log).
The configuration selected GPU_BUSY/XVE hardware metrics and ITT with no native
OpenCL tracing, but it is not a validated joint timeline. Neither new diagnostic
mode is a fix; exclude incomplete runs from all performance claims.

## LES plus OpenCL Perfetto design

This is a source-grounded proposal, not an implemented export backend.
[LES phase hooks](../openvino/src/plugins/intel_gpu/src/graph/impls/ocl_v2/moe/moe_3gemm_swiglu_opt.cpp#L72)
already delimit phases in mark/finish. Add a JSON backend there rather than
instrumenting every LES call again. Record precise begin/end times, OS process
and thread IDs, stable phase names, and token/layer/cache state as structured
arguments. Keep ITT optional and retain empty arrays for unknown state.

An automatic merge can align existing CSV timestamps using the
[clintercept_start_time metadata](../opencl-intercept-layer/intercept/src/chrometracer.h#L76):
relative microseconds = absolute LES microseconds - intercept start microseconds.
[LES timestamps](../openvino/src/plugins/intel_gpu/src/graph/impls/ocl_v2/moe/lru_cache.cpp#L13)
use steady_clock. The intercept layer also uses steady_clock by default, but
[common.h](../opencl-intercept-layer/intercept/src/common.h#L89) permits a
high_resolution_clock build: check the actual clock before applying the offset.
Different clocks require paired clock calibration, not subtraction alone.
CSV snapshot-to-snapshot durations include logging gaps and omit a final phase
end; they are not interchangeable with exact ITT task durations.

For a single JSON directly at runtime, add an optional C host-span interface to
the intercept layer and call it from LES phase hooks. The interface should use
the intercept layer's clock/normalization and buffered, synchronized JSON writer;
it does not exist currently. This avoids file merging and clock mismatch, but
requires changes/builds to both active LES and intercept modules, not the cached
reference. It must handle nesting, escaping, thread/queue track separation and
normal shutdown flushing. Verify nonzero durations, token/layer identities and
host/GPU correlation in Perfetto; do not infer GPU hardware metrics from spans.