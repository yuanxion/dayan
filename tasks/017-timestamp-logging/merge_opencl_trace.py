import argparse
import collections
import json
from pathlib import Path

import ijson


def events(path):
    with path.open("rb") as source:
        yield from ijson.items(source, "item", use_float=True)


def merge(opencl_path, les_path, output_path, api_only=False, selected_window=False):
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
    timed_les = [event for event in les if "ts" in event]
    window_start = min(event["ts"] for event in timed_les) - start
    window_end = max(event["ts"] + event.get("dur", 0) for event in timed_les) - start
    counts = collections.Counter()
    tracks = {}
    load_tracks = {}
    phase_tracks = {}
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
            if event.get("ph") == "M" and event.get("name") in {"thread_sort_index", "process_sort_index"}:
                index = event["args"]["sort_index"]
                if isinstance(index, str):
                    event["args"]["sort_index"] = int(index)
            if "ts" in event:
                native_end = max(native_end, event["ts"] + event.get("dur", 0))
                if selected_window and (event["ts"] > window_end or
                                        event["ts"] + event.get("dur", 0) < window_start):
                    continue
            thread = event.get("tid", 0)
            device = not isinstance(thread, int)
            if device:
                key = str(thread)
                event["tid"] = tracks.setdefault(key, (1 << 40) + len(tracks))
            if event.get("ph") == "X":
                category = "OpenCL.device" if device else "OpenCL.host"
                event.setdefault("cat", category)
                counts[category] += 1
            write(event)
        for event in les:
            if event.get("name") in {"expert_reserved_wait", "expert_host_copy"} and event["tid"] < (1 << 29):
                args = event["args"]
                key = (args["target_layer_index"], args["slot"])
                if key not in load_tracks:
                    load_tracks[key] = (1 << 29) + len(load_tracks)
                    write({"ph": "M", "name": "thread_name", "pid": process, "tid": load_tracks[key],
                           "args": {"name": f"LES layer {key[0]} slot {key[1]}"}})
                event["tid"] = load_tracks[key]
            elif event.get("ph") == "X" and event.get("name") not in {"expert_reserved_wait", "expert_host_copy"}:
                thread = event["tid"]
                if thread not in phase_tracks:
                    phase_tracks[thread] = (1 << 28) + len(phase_tracks)
                    write({"ph": "M", "name": "thread_name", "pid": process, "tid": phase_tracks[thread],
                           "args": {"name": f"LES phases (CPU thread {thread})"}})
                event["tid"] = phase_tracks[thread]
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
    parser.add_argument("--selected-window", action="store_true")
    args = parser.parse_args()
    candidates = list(args.opencl.rglob("clintercept_trace.json")) if args.opencl.is_dir() else [args.opencl]
    les_process = next(event["pid"] for event in events(args.les) if event.get("name") == "les_clock")
    matching = [path for path in candidates if any(event.get("name") == "clintercept_start_time" and
                                                  event.get("pid") == les_process for event in events(path))]
    if len(matching) != 1:
        raise ValueError("Expected one native trace matching the LES process")
    print(json.dumps({"output": str(args.output), "api_only": args.api_only,
                      "selected_window": args.selected_window,
                      "events": merge(matching[0], args.les, args.output, args.api_only, args.selected_window)}, indent=2))


if __name__ == "__main__":
    main()