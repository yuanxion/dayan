import argparse
import bisect
import collections
import json
from pathlib import Path

import ijson


def events(path):
    with path.open("rb") as source:
        yield from ijson.items(source, "item", use_float=True)


def merge(opencl_path, les_path, output_path, api_only=False, selected_window=False, walltime=None):
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
    token_windows = {}
    native_end = 0
    scopes = collections.defaultdict(list)
    copying_threads = {}
    for event in les:
        if event.get("name") == "expert_copying":
            args = event["args"]
            copying_threads[(args["target_layer_index"], args["expert_id"], args["generation"])] = event["tid"]
    for event in les:
        if event.get("ph") != "X" or event.get("dur", 0) <= 0:
            continue
        args = event["args"]
        if event["name"][0].isdigit():
            track = phase_tracks.setdefault(args["layer_index"], (1 << 28) + len(phase_tracks))
            thread = event["tid"]
            method = "same_thread_phase_containment"
        elif event["name"].startswith("expert_host_copy"):
            key = (args["target_layer_index"], args["slot"], args["expert_id"])
            track = load_tracks.setdefault(key, (1 << 29) + len(load_tracks))
            thread = copying_threads.get((args["target_layer_index"], args["expert_id"], args["generation"]))
            if thread is None:
                continue
            method = "load_generation_worker_containment"
        else:
            continue
        context = {field: args[field] for field in ("request", "token_index", "layer_index",
                   "target_layer_index", "expert_id", "slot", "generation", "origin") if field in args}
        context.update({"phase": event["name"], "association": method, "cpu_thread_id": thread})
        scopes[thread].append((event["ts"] - start, event["ts"] + event["dur"] - start, track, context))
    for thread in scopes:
        scopes[thread].sort(key=lambda scope: scope[0])
    scope_starts = {thread: [scope[0] for scope in values] for thread, values in scopes.items()}
    correlations = []
    named_tracks = set()
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
                if not device and event["name"].startswith("clEnqueue") and "id" in event.get("args", {}):
                    index = bisect.bisect_right(scope_starts.get(thread, []), event["ts"]) - 1
                    if index >= 0:
                        scope = scopes[thread][index]
                        if event["ts"] < scope[1]:
                            event["args"]["les_context"] = scope[3]
                            correlations.append((scope, event["ts"], thread, event["args"]["id"]))
            write(event)
        for event in les:
            base_name = event["name"]
            load_span = base_name.startswith(("expert_reserved_wait", "expert_host_copy"))
            if load_span:
                args = event["args"]
                key = (args["target_layer_index"], args["slot"], args["expert_id"])
                load_tracks.setdefault(key, (1 << 29) + len(load_tracks))
                if load_tracks[key] not in named_tracks:
                    write({"ph": "M", "name": "thread_name", "pid": process, "tid": load_tracks[key],
                           "args": {"name": f"LES layer {key[0]} expert {key[2]} slot {key[1]}"}})
                    named_tracks.add(load_tracks[key])
                event["tid"] = load_tracks[key]
            elif event.get("ph") == "X":
                thread = event["args"]["layer_index"]
                phase_tracks.setdefault(thread, (1 << 28) + len(phase_tracks))
                if phase_tracks[thread] not in named_tracks:
                    write({"ph": "M", "name": "thread_name", "pid": process, "tid": phase_tracks[thread],
                           "args": {"name": f"LES phases layer_index: {thread}"}})
                    named_tracks.add(phase_tracks[thread])
                event["tid"] = phase_tracks[thread]
            if "ts" in event:
                event["ts"] -= start
                if event["ts"] < 0 or event["ts"] + event.get("dur", 0) > native_end + 1_000_000:
                    raise ValueError("LES span is outside the OpenCL clock range")
                if event.get("dur", 0) < 0:
                    raise ValueError("Negative LES span duration")
                counts[base_name] += 1
                args = event["args"]
                event["name"] += f" [token_index: {args['token_index']} layer_index: {args['layer_index']}"
                if "expert_id" in args:
                    event["name"] += f" expert_id: {args['expert_id']}"
                event["name"] += ']'
                if event["ph"] == "X" and not load_span:
                    bounds = token_windows.setdefault(args["token_index"], [event["ts"], event["ts"]])
                    bounds[0] = min(bounds[0], event["ts"])
                    bounds[1] = max(bounds[1], event["ts"] + event["dur"])
            write(event)
        for scope, timestamp, thread, command in correlations:
            flow_id = (1 << 62) + command
            write({"ph": "s", "cat": "LES.correlation", "name": "LES to OpenCL enqueue",
                   "pid": process, "tid": scope[2], "ts": scope[0], "id": flow_id})
            write({"ph": "f", "cat": "LES.correlation", "name": "LES to OpenCL enqueue",
                   "pid": process, "tid": thread, "ts": timestamp, "id": flow_id, "bp": "e"})
        counts["LES.enqueue_flows"] = len(correlations)
        summary_track = 1 << 27
        token_track = summary_track + 1
        write({"ph": "M", "name": "thread_name", "pid": process, "tid": summary_track,
               "args": {"name": "Run timing summary (not to scale)"}})
        write({"ph": "M", "name": "thread_sort_index", "pid": process, "tid": summary_track,
               "args": {"sort_index": -2}})
        write({"ph": "M", "name": "thread_name", "pid": process, "tid": token_track,
               "args": {"name": "LES token_index"}})
        write({"ph": "M", "name": "thread_sort_index", "pid": process, "tid": token_track,
               "args": {"sort_index": -1}})
        label = f"Program wall time: {walltime:.2f} s" if walltime is not None else f"OpenCL observed interval: {native_end / 1e6:.2f} s (not full process wall time)"
        write({"ph": "X", "cat": "Run", "name": label, "pid": process, "tid": summary_track,
               "ts": window_start if selected_window else 0,
               "dur": window_end - window_start if selected_window else native_end,
               "args": {"program_wall_time_s": walltime, "opencl_observed_duration_s": native_end / 1e6,
                        "selected_decode_window_s": (window_end - window_start) / 1e6}})
        for token, (begin, end) in sorted(token_windows.items()):
            write({"ph": "X", "cat": "LES.tokens", "name": f"token_index: {token}",
                   "pid": process, "tid": token_track, "ts": begin, "dur": end - begin,
                   "args": {"token_index": token}})
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
    parser.add_argument("--walltime", type=Path)
    args = parser.parse_args()
    candidates = list(args.opencl.rglob("clintercept_trace.json")) if args.opencl.is_dir() else [args.opencl]
    les_process = next(event["pid"] for event in events(args.les) if event.get("name") == "les_clock")
    matching = [path for path in candidates if any(event.get("name") == "clintercept_start_time" and
                                                  event.get("pid") == les_process for event in events(path))]
    if len(matching) != 1:
        raise ValueError("Expected one native trace matching the LES process")
    print(json.dumps({"output": str(args.output), "api_only": args.api_only,
                      "selected_window": args.selected_window,
                      "events": merge(matching[0], args.les, args.output, args.api_only, args.selected_window,
                                      float(args.walltime.read_text().strip()) if args.walltime else None)}, indent=2))


if __name__ == "__main__":
    main()