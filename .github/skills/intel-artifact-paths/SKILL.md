---
name: intel-artifact-paths
description: "Use when locating or downloading internal OpenVINO model-cache artifacts, Windows Python wheels, or validation datasets from ov-share UNC/HTTP paths; includes removing the data path segment, WW cache fallback, commit-SHA wheel lookup, and artifact verification."
---

# Intel Artifact Paths

Use this skill before asking the user how to translate a known `ov-share` UNC
path into an HTTP artifact URL. These mappings are verified examples, not a
guarantee that every cache/version is present or accessible.

## Procedure

1. Read the exact model, dataset, runtime version, commit, and Python version
   from the failing log and test configuration. Keep the requested version as
   the reproduction target; a newer cache is only a fallback for exploratory
   comparison, not an equivalent reproduction.
2. Translate the known share path using the matching mapping below. Normalize
   backslashes to forward slashes and remove the `data` share component. Use
   the exact hostname/scheme shown for that share; the model and dataset hosts
   do not use identical aliases or schemes.
3. Probe the exact file with `HEAD` before downloading. Record HTTP status,
   content length, effective URL, and TLS result where applicable. A `404`
   means that URL/version was not found. Curl exit 60 with HTTP `000` means TLS
   verification failed before an HTTP response; do not report it as `404`.
4. Download only after the target is confirmed. Keep HTTPS certificate checks
   enabled. Some internal model-cache examples use HTTP; use those exact
   internal URLs without adding credentials or assuming they are secure for
   secrets.
5. Verify the downloaded length against `Content-Length`, parse model XML,
   check the BIN is non-empty/plausible, and calculate SHA-256 for each file.
   For large wheels or models, a stalled full GET may be retried as bounded
   HTTP Range requests; require HTTP `206`, validate every segment length,
   reassemble in order, and verify final length and SHA-256.
6. Select the dataset named by the target model's accuracy config/log. Logs
  containing several models may show different dataset directories; do not
  attribute a neighboring model's `data_source` to the target. Do not
  substitute `sts-test.csv` for ImageNet: STS-B is for tests that explicitly
  name STS-B; colorization-v2 accuracy uses ImageNet images as both inputs
  and reference targets.
7. For the official ILSVRC2012 validation archive, run the repository script
  `bash 0-download-dataset.sh [destination]`. It uses resumable GNU `wget` or
  `curl`, keeps certificate verification enabled, and has bounded connection
  timeouts/retries. Validate the completed archive with `tar -tf` before
  extracting; starting or resuming a transfer does not prove completion.

## Verified Model Cache Mapping

For model-cache paths of this form:

```text
\\ov-share-04.iotg.sclab.intel.com\data\cv_bench_cache\<CACHE>\<model-relative-path>
```

Use the internal HTTP form:

```text
http://ov-share-04.sclab.intel.com/cv_bench_cache/<CACHE>/<model-relative-path>
```

Example files for colorization-v2:

```text
http://ov-share-04.sclab.intel.com/cv_bench_cache/WW43_static_2026.5.0-23552/colorization-v2/onnx/onnx/FP16/INT8/1/ov/optimized/colorization-v2.xml
http://ov-share-04.sclab.intel.com/cv_bench_cache/WW43_static_2026.5.0-23552/colorization-v2/onnx/onnx/FP16/INT8/1/ov/optimized/colorization-v2.bin
```

Rechecked on 2026-11-21 using the exact HTTP host above: both WW42 files
returned HTTP 404, while both WW43 files returned HTTP 200 (XML 190,927 bytes;
BIN 32,283,090 bytes). The WW43 pair is already present under
`tasks/001-colorization-v2/artifacts/models/WW43_static_2026.5.0-23552/`;
the XML parses as OpenVINO IR v11 and its sibling BIN is present. SHA-256:
XML `1036E553BD5A8D75CD4AECC28485AFF0CC1B45152FAFE85B88277D43897FDC20`, BIN
`6A1F027A1DAB4DF4BAF5C6D3AEABB4FAF52389F47A45D6607FF3C7CFAA1A3C9F`. WW43 is
available for an exploratory comparison, but it does not replace the WW42
model used by the ticket.

Additional verified WW47 cache, checked on 2026-11-22:

```text
http://ov-share-04.sclab.intel.com/cv_bench_cache/WW47_static_2026.5.1-23891-RC1/colorization-v2/onnx/onnx/FP16/INT8/1/ov/optimized/colorization-v2.xml
http://ov-share-04.sclab.intel.com/cv_bench_cache/WW47_static_2026.5.1-23891-RC1/colorization-v2/onnx/onnx/FP16/INT8/1/ov/optimized/colorization-v2.bin
```

Both files returned HTTP 200. The XML is 190,967 bytes, parses as IR v11,
and has SHA-256 `40860867BB60C53AD09EB2DDD1617FE323EA525FD01296798B8EA41E87E7CFE3`;
the BIN is 32,283,090 bytes with SHA-256
`51054999E2747F440D48DE436054C69E722C02E9443F820CE1544C9429355CA8`. WW47 is
newer than the unavailable WW42 cache and is an exploratory substitute only.

## Verified Wheel Mapping

Find the full OpenVINO commit SHA in the run log, then browse:

```text
https://ov-share-03.iotg.sclab.intel.com/volatile/openvino_ci/private_builds/dldt/master/commit/<FULL_COMMIT_SHA>/private_windows_vs2022_release/wheels/
```

Choose the wheel tag matching the active Python ABI and OS, for example
`cp312-cp312-win_amd64.whl` for 64-bit Windows CPython 3.12. Do not infer the
commit from a weekly cache name if the log records the exact SHA.

Verified examples:

- WW41 commit `b9fb87c943a0c4ad8919a9b849fee605fd4c7cb1`:
  `openvino-2026.5.0.dev20261007-23368-cp312-cp312-win_amd64.whl`.
- WW42 commit `7d81aad55a539c827049ac9628ba4f8d5abb4539`:
  `openvino-2026.5.0.dev20261014-23457-cp312-cp312-win_amd64.whl`.
- Commit `000d86dbe1c6c7e2286a5e2bcd90b1576f198cbb`:
  `openvino-2027.0.0.dev20261120-23986-cp312-cp312-win_amd64.whl`.

Both examples were retrieved over HTTPS, passed Python's ZIP integrity test,
and had their size, package metadata, and SHA-256 recorded. Prefer an isolated
virtual environment when testing multiple wheel versions.

For the 2027 wheel, the HTTPS index returned it at 87,503,437 bytes. It passed
`python -m zipfile -t`; metadata reports `2027.0.0.dev20261120`; SHA-256 is
`7AF697CFFB6F7224A0A8A2AD49952D7E21BE67249DEE0CA7408C21E63226667D`.

## Verified Pip Proxy

When pip cannot reach PyPI directly from the Intel Windows environment, use
the verified proxy per command:

```powershell
python -m pip install --proxy http://child-prc.intel.com:913 <package-or-requirements>
```

Verified on 2026-11-21: `child-prc.intel.com` resolved to `10.240.252.23`, TCP
port 913 was reachable, and `pip index versions numpy` through this proxy
returned PyPI versions (exit 0). Installing the DL-Benchmark accuracy
requirements through the same proxy succeeded (exit 0). The reversed hostname
`prc-child.intel.com` did not resolve; use `child-prc`, not `prc-child`.
Pass the proxy per pip command instead of changing global pip configuration
unless a user explicitly requests persistent configuration. Keep TLS
verification enabled.

## Verified Dataset Mapping

Remove the `data` share component and use the dataset host's HTTPS alias. The
failed log contains two distinct paths, so keep them distinct when reproducing:

- The colorization-v2 config dump names `.../omz-validation-datasets/ImageNet`
  as both `data_dir` and `data_source` at lines 56479 and 56482 of
  `tasks/001-colorization-v2/colorization-v2-failed.log`.
- The shared log has `.../omz-validation-datasets/ILSVRC2012_img_val` at line
  3962. That occurrence is not the colorization-v2 config dump; do not assume
  it overrides the target model's `ImageNet` setting.

The corresponding URL form for the second path is:

```text
https://ov-share-02.iotg.sclab.intel.com/nn_icv_cv_externalN/omz-validation-datasets/ILSVRC2012_img_val/
```

In the CVS-197623 investigation, a GET of this directory returned HTTP 200
(6,650,498-byte HTML listing) and included `ILSVRC2012_val_00000001.JPEG`.
PowerShell retrieved that JPEG with HTTP 200 (109,527 bytes), and a separate
1 KiB Range request returned HTTP 206. A full `curl` GET later timed out, so
record the successful PowerShell GET and the `curl` timeout separately; neither
proves that the complete dataset has been downloaded. A 1 KiB Range request to
the corresponding `ImageNet/ILSVRC2012_val_00000001.JPEG` URL also returned
HTTP 206; this does not establish that the two directories are equivalent.

For example, the UNC path
`\\ov-share-02.iotg.sclab.intel.com\data\nn_icv_cv_externalN\omz-validation-datasets\stsbenchmark\sts-test.csv`
maps to the HTTPS URL below by removing the `data` share component and using
the dataset host alias. The parent test-data directory also listed
`stsbenchmark/sts-test.csv` at:

```text
https://ov-share-02.iotg.sclab.intel.com/nn_icv_cv_externalN/omz-validation-datasets/stsbenchmark/sts-test.csv
```

That CSV returned HTTP 200 (282,419 bytes) in this investigation but belongs to
STS-B, not the colorization-v2 ImageNet evaluation. Follow the config's
`subsample_size`, ordering, annotations, and preprocessing when selecting
images; do not assume an arbitrary 2,000-image subset reproduces a logged run.

The repository download script uses the official archive URL:

```text
https://image-net.org/data/ILSVRC/2012/ILSVRC2012_img_val.tar
```

Run it from Bash and pass a destination directory as its optional first
argument. Without one, it writes to
`tasks/001-colorization-v2/artifacts/datasets/`. GNU `wget` uses `--continue`;
the curl fallback uses `--continue-at -`. Neither path disables TLS checks.
In the 2026-11-19 Windows session, Git Bash was available with curl at
`/ucrt64/bin/curl` but without GNU wget; `bash -n 0-download-dataset.sh`
passed. The actual direct script run made two connection attempts, both timing
out after 10 seconds (curl exit 28); no archive was created. A separate direct
HEAD also timed out. A `proxy-dmz` HEAD reached HTTP `200 Connection
established`, then Windows Schannel failed certificate revocation checking
(curl exit 35, HTTP 000). This is neither a 404 nor proof the archive is absent;
do not disable TLS or revocation checks to force the download. Invoking a `.sh`
file directly from PowerShell produced no output and did not establish that the
script ran.
The previously reachable internal sample URL does not prove this full archive
can be fetched from the host.

## Controlled Direct Accuracy Runs

For a local reproduction, pin the test/config/model-source commits and capture
the active Python, package versions, runtime commit, GPU, and driver first. If
the intent is to vary only OpenVINO, install the chosen wheel with
`pip install --no-deps --force-reinstall <wheel>` and verify the other package
versions remain unchanged; do not combine this with a model-cache or driver
change. Keep the invocation on `scripts/accuracy/accuracy_check.py`, as in the
Jenkins log, rather than substituting a separate GPU harness.

Set `PYTHONPATH` to the DL-Benchmark checkout and run from that checkout so the
direct script can import `scripts`. Keep the target config's dataset path,
precision tag, device, model search path, sample count, ordering, and annotation
conversion fixed. Capture the full command, stdout/stderr log, Accuracy Checker
JSON, model and wheel hashes, and a metrics CSV with metric identity, unit,
reference, object count, and status. A passing result with a different model
cache or driver is exploratory evidence, not proof of the original failure's
root cause. See the WW47/OpenVINO 2027 run under
`tasks/001-colorization-v2/artifacts/accuracy-runs/` for a concrete example:
it passes, but changes the cache and runtime relative to WW42 and uses the
current driver.

## Access And Evidence Rules

- A reachable SMB port does not prove that the share is mounted or authorized.
  Check the exact UNC path and report access-denied separately from network
  reachability.
- Use the exact original model cache first. If it is absent, a later cache may
  help test a hypothesis, but report it as a different artifact and preserve
  the original cache/version in all results.
- Keep downloaded files and a small provenance record under the task's
  `artifacts/` directory. Record source URL, status, expected/actual bytes,
  SHA-256, runtime commit, ABI, and whether the file was actually used.
- Never claim artifact identity from matching names or sizes alone. Never
  disable TLS verification to work around an internal certificate error.