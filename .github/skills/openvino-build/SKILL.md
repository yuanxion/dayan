---
name: openvino-build
description: Build the nested OpenVINO source checkout on Linux, or reuse a preserved reference/base runtime. Use for OpenVINO builds, reference/base measurements, cached binaries, and baseline environment reuse.
---

# OpenVINO Linux Build

## Reference/base reuse first

Before changing the checkout or compiling a reference/base, check
`artifacts/openvino-reference/<full-commit>/README.md`. Verify the revision,
build options, benchmark/GenAI provenance, system ABI/GPU driver, and
`SHA256SUMS`. Use a compatible cache without rebuilding or requiring the active
source HEAD to match. A runtime snapshot is not a CMake build directory.
Rebuild only for an absent/incompatible cache or an explicit build request;
never overwrite a verified cache with different artifacts/configuration.

The verified native reference is
`artifacts/openvino-reference/caa59b5b8a3874d2b7cb0651a56e99a9f38dc450/`.
Its `run-benchmark.sh` pins cached OpenVINO/GenAI/tokenizer/TBB libraries,
verifies checksums, and accepts the original `benchmark_vlm` arguments. The
README contains the complete repeat command and validation log links. It ran
successfully after restoring the LES checkout and LES runtime. The Python
bindings were disabled; this is not a cached Python benchmark environment.
Model weights and system GPU drivers remain external.

## Procedure

1. Confirm the OpenVINO checkout path and inspect its Git status before changing
   branches. Preserve local changes. Only create/reset a requested branch after
   confirming the requested commit exists and the worktree is safe to change.
2. Read `docs/dev/build_linux.md` and the target revision's CMake options. Do not
   assume a script's option names or defaults are valid for that revision.
3. From the OpenVINO root, run `git submodule update --init --recursive` and
   verify `git submodule status --recursive` has no leading `-`, `+`, or `U`.
4. Ensure required system dependencies are installed. The official guide
   references `install_build_dependencies.sh`; use appropriate privileges only
   when available and authorized. Do not claim dependencies were installed
   merely because configuration succeeded.
5. Configure into a dedicated build directory with a resource-appropriate job
   count. Prefer `cmake -S <source> -B <build>` and pass explicit feature
   options required by the task. This workspace uses `-j12`. Never run concurrent
   builds in the same build directory; a dependency's "no work to do" is not
   evidence that the whole build completed.
6. Build the default `all` target and capture the command's exit status. If the
   output is truncated, rerun the incremental build with output filtering and
   `pipefail`; do not infer success from one completed dependency target.
7. Verify the CMake cache has the requested option values, inspect expected
   runtime/plugin outputs under `bin/intel64/Release/`, and check their file
   types. Compiling test executables is not the same as running tests.
8. Recheck branch, commit, submodule state, and worktree status. Report build,
   tests, and unverified checks separately.

## Verified revision-specific note

At commit `caa59b5b8a`, ITT profiling uses
`-DENABLE_PROFILING_ITT=FULL` (`OFF`, `BASE`, or `FULL`). The spelling
`ENABLE_PROFILE_ITT` is incorrect for this revision. The Linux guide lists
Python 3.11-3.15 for the Python API; this native build disables Python, so it
does not require selecting a Python executable.