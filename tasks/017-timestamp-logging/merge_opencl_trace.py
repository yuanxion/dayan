import argparse
import collections
import json
from pathlib import Path

import ijson


def events(path):
    with path.open("rb") as source:
        yield from ijson.items(source, "item", use_float=True)


def merge(opencl_path, les_path, output_path, api_only=False):
    starts = [event for event in events(opencl_path) if event.get("name") == "clintercept_start_time"]
    if len(starts) != 1:
        raise ValueError("Expected one Intercept start-time anchor")
    start = starts[0]["args"]["start_time"]
    process = starts[0]["pid"]
    les = list(events(les_path))
    clocks = [event for event in les if event.get("name") == "les_clock"]
    if len(clocks) != 1 or clocks[0]["args"] != {"clock": "steady_clock", "unit": "us", "absolute": True}:
        raise ValueError("LES trace must use absolute steady_clock microseconds")
    if clocks[0]["pid"] != process:
        raise ValueError("OpenCL and LES traces belong to different processes")
    counts = collections.Counter()
    tracks = {}
    native_end = 0
    with output_path.open("x", encoding="utf-8") as output:
        output.write('{"traceEvents":[\n')
        first = True

        def write(event):
            nonlocal first
            if not first:
                output.write(",\n")
            json.dump(event, output, ensure_ascii=True, separators=(",", ":"))
            first = False

        for event in events(opencl_path):
            thread = event.get("tid", 0)
            device = not isinstance(thread, int)
            if device:
                key = str(thread)
                event["tid"] = tracks.setdefault(key, (1 << 40) + len(tracks))
            if event.get("ph") == "X":
                category = "OpenCL.device" if device else "OpenCL.host"
                event.setdefault("cat", category)
                counts[category] += 1
                native_end = max(native_end, event["ts"] + event.get("dur", 0))
            write(event)
        for event in les:
            if "ts" in event:
                event["ts"] -= start
                if event["ts"] < 0 or event["ts"] + event.get("dur", 0) > native_end + 1_000_000:
                    raise ValueError("LES span is outside the OpenCL clock range")
                if event.get("dur", 0) < 0:
                    raise ValueError("Negative LES span duration")
                counts[event["name"]] += 1
            write(event)
        output.write('\n],"displayTimeUnit":"ms"}\n')
    if not counts["OpenCL.host"] or not counts["expert_reserved"]:
        raise ValueError("Merged trace is missing OpenCL API timings or LES loading events")
    if not api_only and not counts["OpenCL.device"]:
        raise ValueError("Merged trace is missing native GPU timings")
    return dict(counts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--opencl", type=Path, required=True)
    parser.add_argument("--les", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-only", action="store_true")
    args = parser.parse_args()
    candidates = list(args.opencl.rglob("clintercept_trace.json")) if args.opencl.is_dir() else [args.opencl]
    les_process = next(event["pid"] for event in events(args.les) if event.get("name") == "les_clock")
    matching = [path for path in candidates if any(event.get("name") == "clintercept_start_time" and
                                                  event.get("pid") == les_process for event in events(path))]
    if len(matching) != 1:
        raise ValueError("Expected one native trace matching the LES process")
    print(json.dumps({"output": str(args.output), "api_only": args.api_only,
                      "events": merge(matching[0], args.les, args.output, args.api_only)}, indent=2))


if __name__ == "__main__":
    main()