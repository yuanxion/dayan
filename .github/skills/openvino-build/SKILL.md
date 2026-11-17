---
name: openvino-build
description: Build the nested OpenVINO source checkout on Linux from a selected revision, including submodules, CMake configuration, and output verification.
---

# OpenVINO Linux Build

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
   options required by the task.
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