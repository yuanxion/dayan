#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_dir="${OPENVINO_SOURCE_DIR:-"${script_dir}/../openvino"}"
build_dir="${OPENVINO_BUILD_DIR:-"${source_dir}/build-les"}"
build_jobs="${BUILD_JOBS:-$(nproc)}"

cmake -S "$source_dir" -B "$build_dir" \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_INTEL_GPU="${ENABLE_INTEL_GPU:-ON}" \
    -DENABLE_TESTS="${ENABLE_TESTS:-ON}" \
    -DENABLE_FUNCTIONAL_TESTS="${ENABLE_FUNCTIONAL_TESTS:-ON}" \
    -DENABLE_PYTHON=OFF \
    -DENABLE_DEBUG_CAPS:BOOL=ON \
    -DENABLE_WHEEL=OFF \
    -DENABLE_PROFILING_ITT=FULL \
    -DCMAKE_INSTALL_PREFIX="${build_dir}/install"

cmake --build "$build_dir" --parallel "$build_jobs"
