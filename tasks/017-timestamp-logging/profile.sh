#!/usr/bin/env bash
set -euo pipefail
main() {
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
results="$root/tasks/017-timestamp-logging"
vtune_root=${VTUNE_ROOT:-/home/openvino-288v002/yuanx/tools/oneapi/vtune/latest}
vtune="$vtune_root/bin64/vtune"
name=${1:?Usage: profile.sh OUTPUT_NAME [hotspots|xpu-offload|opencl] [--check|--api-only|--reference|--itt-only|--runtime-profile|--gpu-metrics]}
analysis=${2:-hotspots}
[[ "$name" =~ ^[a-zA-Z0-9_-]+$ ]]
if [[ "$analysis" == opencl ]]; then
    intercept_root=${CLINTERCEPT_ROOT:-$root/artifacts/opencl-intercept-itt}
    library="$intercept_root/lib/libOpenCL.so.1"
    python=${CLINTERCEPT_PYTHON:-$intercept_root/venv/bin/python}
    [[ -f "$library" && -x "$python" ]]
    [[ ${3:-} == '' || ${3:-} == --check || ${3:-} == --api-only ]]
    if [[ ${3:-} == --check ]]; then
        printf 'OpenCL Intercept + LES; library=%s; output=%s\n' "$library" "$name"
        return 0
    fi
    native_timing=1
    merge_options=()
    if [[ ${3:-} == --api-only ]]; then
        native_timing=0
        merge_options+=(--api-only)
    fi
    [[ ! -e "$results/$name.opencl" && ! -e "$results/$name.les.json" ]]
    [[ ! -e "$results/$name.timeline.json" && ! -e "$results/$name.collect.log" ]]
    mkdir "$results/$name.opencl"
    status=0
    /usr/bin/env CLI_OpenCLFileName=/lib/x86_64-linux-gnu/libOpenCL.so.1 \
        CLI_DumpDir="$results/$name.opencl" CLI_ChromeCallLogging=1 CLI_ChromePerformanceTiming="$native_timing" \
        CLI_ChromePerformanceTimingInStages="$native_timing" CLI_ChromeFlowEvents="$native_timing" CLI_ITTCallLogging=1 \
        LES_OPENCL_PRELOAD="$library" OV_GPU_LES_TRACE="$results/$name.les.json" \
        OV_GPU_LES_ITT=1 LES_LOG_MODE=itt LES_RUNTIME=les LES_GPU_PROFILE=0 LES_LOG_STEM="$name" \
        bash "$results/run.sh" > "$results/$name.collect.log" 2>&1 || status=$?
    if [[ "$status" == 0 ]]; then
        "$python" "$results/merge_opencl_trace.py" --opencl "$results/$name.opencl" \
            --les "$results/$name.les.json" --output "$results/$name.timeline.json" "${merge_options[@]}" \
            --walltime "$results/$name.walltime.txt" \
            >> "$results/$name.collect.log" 2>&1 || status=$?
    fi
    printf '%s\n' "$status" > "$results/$name.collect.exit"
    tail -26 "$results/$name.collect.log"
    return "$status"
fi
[[ -x "$vtune" ]]
ptrace=/proc/sys/kernel/yama/ptrace_scope
if [[ $(<"$ptrace") != 0 ]]; then
    printf '0\n' | sudo -n tee "$ptrace" >/dev/null
fi
[[ $(<"$ptrace") == 0 ]]
case "$analysis" in
    hotspots) knobs=(-knob sampling-mode=sw -knob enable-stack-collection=true) ;;
    gpu-offload|xpu-offload)
        analysis=xpu-offload
        knobs=(-knob enable-characterization-insights=false)
        ;;
    *) printf 'Unsupported analysis: %s\n' "$analysis" >&2; exit 1 ;;
esac
mode=details
runtime=les
gpu_profile=0
if [[ ${3:-} == --api-only || ${3:-} == --reference ]]; then
    [[ "$analysis" == xpu-offload ]]
    knobs+=(-knob enable-user-tasks=false)
    mode=off
fi
if [[ ${3:-} == --reference ]]; then
    runtime=reference
fi
if [[ ${3:-} == --itt-only ]]; then
    [[ "$analysis" == xpu-offload ]]
    knobs+=(-knob collect-programming-api=false -knob enable-user-tasks=true -knob itt-domains=ov::intel_gpu)
fi
if [[ ${3:-} == --runtime-profile ]]; then
    [[ "$analysis" == xpu-offload ]]
    gpu_profile=1
fi
if [[ ${3:-} == --gpu-metrics ]]; then
    [[ "$analysis" == xpu-offload ]]
    knobs=(-knob enable-characterization-insights=true -knob collect-programming-api=false -knob enable-user-tasks=true -knob itt-domains=ov::intel_gpu)
fi
if [[ ${3:-} == --check ]]; then
    "$vtune" -version
    printf 'ptrace_scope=0; analysis=%s; output=%s\n' "$analysis" "$name"
    exit 0
fi
[[ ! -e "$results/$name" && ! -e "$results/$name.collect.log" ]]
cd "$root"
status=0
"$vtune" -collect "$analysis" "${knobs[@]}" -data-limit=0 -result-dir "$results/$name" \
    -- /usr/bin/env OV_GPU_LES_ITT=details LES_LOG_MODE="$mode" LES_RUNTIME="$runtime" LES_GPU_PROFILE="$gpu_profile" LES_LOG_STEM="$name" \
    bash "$results/run.sh" > "$results/$name.collect.log" 2>&1 || status=$?
printf '%s\n' "$status" > "$results/$name.collect.exit"
tail -24 "$results/$name.collect.log"
exit "$status"
}
main "$@"