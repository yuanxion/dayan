#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
results="$root/tasks/017-timestamp-logging"
stem="$results/${LES_LOG_STEM:-dual-layer-details}"
base="$root/artifacts/openvino-reference/caa59b5b8a3874d2b7cb0651a56e99a9f38dc450"
model="$root/models/MiniCPM-V-4.7-35B-A3B-int4-ov"
for suffix in log csv benchmark.log exit walltime.txt; do
    [[ ! -e "$stem.$suffix" ]]
done
(
    cd "$base"
    sha256sum --check --quiet SHA256SUMS
)
unset LOG_TOKEN_ID LOG_REQUEST LOG_REQUEST_CONTEXT LOG_BASELINE_CSV_PATH LOG_HANDOFF_CSV_PATH
unset LOG_CSV_PATH LOG_RUN_ID OV_GPU_MOE_LOG_PATH
unset OV_GPU_LES_TIMELINE OV_GPU_LES_TIMELINE_COMPLETION OV_GPU_LES_TIMELINE_SAMPLE
unset OV_GPU_LES_PREDICT_COMPARE MOE_OTD_LAYER_PERF_LOG MOE_REF_WAVE_HIT_COUNT
if [[ ${LES_LOG_MODE:-details} == off ]]; then
    unset OV_GPU_LES_ITT OV_GPU_LES_TRACE LES_OPENCL_PRELOAD LD_PRELOAD
fi
runtime=${LES_RUNTIME:-les}
case "$runtime" in
    les)
        plugin_dir="$root/openvino/bin/intel64/Release"
        export LD_LIBRARY_PATH="$plugin_dir:$base/lib"
        benchmark=("$base/bin/benchmark_vlm" --les)
        ;;
    reference)
        [[ ${LES_LOG_MODE:-details} == off ]]
        plugin_dir="$base/lib"
        benchmark=(bash "$base/run-benchmark.sh")
        ;;
    *) printf 'Unknown LES_RUNTIME: %s\n' "$runtime" >&2; exit 1 ;;
esac
case ${LES_GPU_PROFILE:-0} in
    0) ;;
    1) benchmark+=(--profile) ;;
    *) printf 'Unknown LES_GPU_PROFILE: %s\n' "$LES_GPU_PROFILE" >&2; exit 1 ;;
esac
if [[ -n ${LES_OPENCL_PRELOAD:-} ]]; then
    [[ "$runtime" == les && -f "$LES_OPENCL_PRELOAD" ]]
    benchmark=(/usr/bin/env "LD_PRELOAD=$LES_OPENCL_PRELOAD${LD_PRELOAD:+:$LD_PRELOAD}" "${benchmark[@]}")
fi
mode=${LES_LOG_MODE:-details}
case "$mode" in
    details)
        export OV_GPU_MOE_LOG_PATH="$stem.log"
        export LOG_CSV_PATH="$stem.csv"
        ;;
    off|itt) ;;
    *) printf 'Unknown LES_LOG_MODE: %s\n' "$mode" >&2; exit 1 ;;
esac
if [[ "$mode" == off ]]; then
    unset OV_GPU_LES_ITT
else
    export LOG_TOKEN_ID='1,2,3,4,5,6,7,8'
    export LOG_REQUEST='measured:0'
fi
if [[ "$mode" == itt ]]; then
    export OV_GPU_LES_ITT=1
fi
sha256sum "$plugin_dir/libopenvino_intel_gpu_plugin.so" \
    "$base/bin/benchmark_vlm" > "$stem.sha256"
status=0
/usr/bin/time -f '%e' -o "$stem.walltime.txt" "${benchmark[@]}" --model "$model" --device GPU --offload-ratio 90 \
    --weights-path "$model/openvino_language_model.bin" --request-metrics \
    --max_new_tokens 256 --num_warmup 1 --num_iter 3 \
    --prompt "$(cat "$base/prompt.txt")" > "$stem.benchmark.log" 2>&1 || status=$?
printf '%s\n' "$status" > "$stem.exit"
tail -16 "$stem.benchmark.log"
exit "$status"