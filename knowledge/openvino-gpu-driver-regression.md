# OpenVINO GPU Driver Regression Triage

## Scope

Use this note when an OpenVINO GPU accuracy regression may depend on the Intel GPU driver. It records a verified Arc 140V / colorization-v2 FP16-INT8 A/B result and a repeatable way to interpret similar tests.

## Verified Case

On the same Core Ultra 7 258V / Arc 140V system (PCI ID `64A0`), same Windows build `28000`, Python `3.12.10`, OpenVINO wheel, model, config, dataset, source revisions, and local runner, the 2,000-image `colorization-v2` FP16-INT8 Accuracy Checker result differed by the installed GPU driver:

| GPU driver | PSNR mean (reference `26.8326013816`) | PSNR status | SSIM mean (reference `0.8962253114`) | SSIM status | Overall |
| --- | ---: | --- | ---: | --- | --- |
| `32.0.101.8991` | `26.529603542071097` | DOWNGRADE | `0.8524936115805105` | DOWNGRADE | DOWNGRADE |
| `32.0.101.9175` | `27.32672297012814` | IMPROVEMENT | `0.901529532631834` | PASSED | PASSED |

Both runs used the same OpenVINO wheel source commit `7314e7a6f3bdcabfa8b7811d27ff4bcfd27dcd28`, runtime build `2026.5.0-23836-f36b4c17f38-releases/2026/5`, and wheel SHA-256 `28E05350E0CA32599BE960A21764BA3618C10EF486DD4624CC088D2CB85C72C4`. Each processed 2,000 objects and returned process exit code 0. The WW46 Jenkins log used driver `32.0.101.8991` and also recorded the downgrade.

This is strong evidence that the result is driver-version or GPU-stack-state associated. It does not isolate the driver binary as the sole cause: there was one run per version, and a driver installation can update or reset related components and device state. Repeat each version after controlled reboot/state checks before making a strict causal claim.

## Reusable Procedure

1. Record the exact accuracy failure: model and precision, target device, dataset, sample count, metric references, OpenVINO runtime build, and the original driver version.
2. Verify the active driver through independent OS sources (for example, WMI and PnP signed-driver inventory); record the device PCI ID and driver date. Do not rely only on a user-reported installer result.
3. Keep the comparison paired: same machine, runtime wheel hashes, model/config/data hashes, Python environment, runner/source revisions, target GPU, sample order/count, and Accuracy Checker flags. Change only the driver version where possible.
4. Before a long run, import the exact task-local OpenVINO runtime, confirm the GPU plugin/device name, read the exact model, and compile it for GPU.
5. Save every driver run to a separate directory. Preserve the exact command, stdout/stderr, raw JSON, Accuracy Checker log, environment, input hashes, process exit code, and elapsed time.
6. Compare unrounded metric values and statuses from raw JSON, not only rounded console output. Include means, standard deviations, references, deltas, units, denominators, and overall status in the report and CSV.
7. Phrase the conclusion proportionally to the evidence: “associated with / strongly implicates driver or GPU-stack state” for a single A/B pair; reserve “caused by the driver” for repeatable controlled results.

## Known Environment Caveat

For this case, local Python `3.12.10` and Windows build `28000` differed from Jenkins Python `3.12.2` and Windows kernel build `26200`. Those values were held constant across the local A/B, so they do not explain its within-machine difference, but they remain possible contributors to local-versus-Jenkins metric deltas.

## Provenance

The full task evidence, per-run reports, raw JSON, logs, and checksums are retained locally under `tasks/1126-csv-197623-colorization-v2/`; task artifacts are Git-ignored and are not part of this knowledge-only commit. The repo-level summary is in `tasks/1126-csv-197623-colorization-v2/artifacts/driver-comparison.md` while available in the originating workspace.
