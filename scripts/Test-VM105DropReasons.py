#!/usr/bin/env python3
"""VM105 only. Default compiles without attachment; --apply traces once; --self-test is offline."""
import json
import argparse
import datetime
import os
from pathlib import Path
import re
import selectors
import signal
import socket
import subprocess
import time


# Upstream v0.20.2 tests/runtime/outputs/map.json defines this NDJSON schema.
# No packet fields, addresses, locations, process information or pointers are printed.
PROGRAM = """
BEGIN { @completed = 0; }
tracepoint:skb:kfree_skb
{
  $skb = (struct sk_buff *)args->skbaddr;
  if ($skb != 0) {
    $dev = $skb->dev;
    if ($dev != 0) {
      if ($dev->ifindex == 2 && $dev->nd_net.net->ns.inum == NETNS_INUM) {
        $reason = (int64)args->reason;
        if ($reason >= 0 && $reason < 255) { @counts[$reason] = count(); }
        else { @counts[(int64)-1] = count(); }
      }
    }
  }
}
interval:s:30 { @completed = 1; exit(); }
"""
NET = Path("/sys/class/net/eth0")
FORMAT = Path("/sys/kernel/tracing/events/skb/kfree_skb/format")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def parse_reasons(body):
    if not re.search(r"field:\s*enum skb_drop_reason reason;", body):
        raise ValueError("reason_field_missing")
    pairs = re.findall(r'\{\s*(\d+)\s*,\s*"([A-Z][A-Z0-9_]+)"\s*\}', body)
    result = {}
    for number, name in pairs:
        number = int(number)
        if number in result or not 0 <= number < 255:
            raise ValueError("reason_metadata_invalid")
        result[number] = name
    if not result or result.get(56) != "UNHANDLED_PROTO" or result.get(8) != "NETFILTER_DROP":
        raise ValueError("reason_metadata_mismatch")
    return result


def parse_counts(body, reasons, shape=None):
    if shape is None:
        shape = {}
    shape.update(blank_segments=0, json_records=0, map_records=0, other_json_records=0)
    maps = {}
    for line in body.split("\n"):
        if not line.strip(" \t\r"):
            shape["blank_segments"] += 1
            continue
        try:
            obj = json.loads(line, object_pairs_hook=unique_object)
        except json.JSONDecodeError:
            raise ValueError("invalid_trace_json") from None
        shape["json_records"] += 1
        if not isinstance(obj, dict) or set(obj) != {"type", "data"} or obj["type"] != "map":
            shape["other_json_records"] += 1
            raise ValueError("unknown_trace_message")
        shape["map_records"] += 1
        if not isinstance(obj["data"], dict):
            raise ValueError("invalid_map")
        for name, value in obj["data"].items():
            if name not in {"@counts", "@completed"} or name in maps:
                raise ValueError("unexpected_map")
            maps[name] = value
    if type(maps.get("@completed")) is not int or maps["@completed"] != 1:
        raise ValueError("window_incomplete")
    counts = maps.get("@counts", {})
    if not isinstance(counts, dict) or len(counts) > 255:
        raise ValueError("invalid_counts")
    result = []
    for key, value in counts.items():
        if not re.fullmatch(r"0|[1-9][0-9]{0,2}", key) or int(key) not in reasons:
            raise ValueError("unknown_reason")
        if type(value) is not int or not 0 <= value <= 2**63 - 1:
            raise ValueError("invalid_count")
        result.append({"reason": int(key), "name": reasons[int(key)], "count": value})
    return sorted(result, key=lambda row: row["reason"])


def identity():
    if socket.gethostname() != "deepseek-harness-01":
        raise ValueError("hostname_mismatch")
    if (NET / "address").read_text().strip() != "bc:24:11:5c:49:52" or (NET / "ifindex").read_text().strip() != "2":
        raise ValueError("interface_mismatch")
    if (NET / "device/driver").resolve().name != "virtio_net":
        raise ValueError("driver_mismatch")
    if not Path("/sys/kernel/btf/vmlinux").is_file():
        raise ValueError("btf_missing")
    if os.stat("/proc/self/ns/net").st_ino != os.stat("/proc/1/ns/net").st_ino:
        raise ValueError("network_namespace_mismatch")
    import fcntl
    import struct
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        address = fcntl.ioctl(probe.fileno(), 0x8915, struct.pack("256s", b"eth0"))[20:24]
    if socket.inet_ntoa(address) != "192.168.1.139":
        raise ValueError("ipv4_mismatch")


def snapshot():
    identity()
    return {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "rx_dropped": int((NET / "statistics/rx_dropped").read_text())}


def bounded_run(argv, limit=1048576):
    # Own process group only. 40 seconds execution + at most 4 seconds cleanup.
    env = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "HOME": "/root",
           "BPFTRACE_MAX_MAP_KEYS": "256", "BPFTRACE_MAX_PROBES": "4",
           "BPFTRACE_BTF": "/sys/kernel/btf/vmlinux"}
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True, env=env)
    data = {"stdout": bytearray(), "stderr": bytearray()}
    failure = None
    started = time.monotonic()
    try:
        with selectors.DefaultSelector() as selector:
            for name, pipe in (("stdout", process.stdout), ("stderr", process.stderr)):
                selector.register(pipe, selectors.EVENT_READ, name)
            while selector.get_map():
                if time.monotonic() - started >= 40:
                    failure = "process_timeout"
                    break
                for key, _ in selector.select(0.2):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    elif sum(map(len, data.values())) + len(chunk) > limit:
                        failure = "output_limit"
                        break
                    else:
                        data[key.data].extend(chunk)
                if failure:
                    break
            if not failure:
                try:
                    process.wait(timeout=max(0.01, 40 - (time.monotonic() - started)))
                except subprocess.TimeoutExpired:
                    failure = "process_timeout"
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    failure = "cleanup_not_proven"
        process.stdout.close()
        process.stderr.close()
    return data, {"returncode": process.returncode, "cleanup_reaped": process.returncode is not None,
                  "failure": failure, "elapsed_seconds": round(time.monotonic() - started, 3)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    report = {"status": "NOT PROVEN", "mode": "apply" if args.apply else "compile_only",
              "interface": "eth0", "window_seconds": 30, "counts": []}
    try:
        identity()
        reasons = parse_reasons(FORMAT.read_text())
        data, check = bounded_run(["/usr/bin/bpftrace", "--version"], 4096)
        report["version_process"] = check
        if check["failure"] or check["returncode"] != 0 or data["stderr"] or data["stdout"].decode().strip() != "bpftrace v0.20.2":
            raise ValueError("bpftrace_version_mismatch")
        report["before"] = snapshot()
        argv = ["/usr/bin/bpftrace", "-kk", "-q", "-f", "json"]
        if not args.apply:
            argv.append("-d")
        program = PROGRAM.replace("NETNS_INUM", str(os.stat("/proc/self/ns/net").st_ino))
        data, report["process"] = bounded_run(argv + ["-e", program])
        report["after"] = snapshot()
        report["rx_dropped_delta"] = report["after"]["rx_dropped"] - report["before"]["rx_dropped"]
        if report["process"]["failure"] or report["process"]["returncode"] != 0:
            raise ValueError("trace_process_failed")
        if data["stderr"]:
            raise ValueError("stderr_present_suppressed")
        if report["rx_dropped_delta"] < 0:
            raise ValueError("counter_reset")
        if args.apply:
            report["parse_shape"] = {}
            report["counts"] = parse_counts(data["stdout"].decode("utf-8"), reasons, report["parse_shape"])
            report["status"] = "OBSERVED"
        else:
            report["status"] = "COMPILE_ONLY"
        report["limit"] = "Reason counts are not proof of RX counter attribution or application impact."
    except (OSError, ValueError, UnicodeError, TypeError) as error:
        # Never expose bpftrace body, diagnostics, pointers or arbitrary exception text.
        safe = str(error)
        report["failure"] = safe if re.fullmatch(r"[a-z_]{1,64}", safe) else "preflight_or_parse_failed"
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] in {"COMPILE_ONLY", "OBSERVED"} else 1


def self_test():
    reasons = {8: "NETFILTER_DROP", 56: "UNHANDLED_PROTO"}
    good = '{"type":"map","data":{"@counts":{"56":3}}}\n{"type":"map","data":{"@completed":1}}\n'
    assert parse_counts(good, reasons) == [{"reason": 56, "name": "UNHANDLED_PROTO", "count": 3}]
    # v0.20.2 src/main.cpp:1015 prints two newlines before print_maps(), even with -q.
    shape = {}
    assert parse_counts("\n\n" + good, reasons, shape) == parse_counts(good, reasons)
    assert shape == {"blank_segments": 3, "json_records": 2, "map_records": 2, "other_json_records": 0}
    for bad in (good + '{"type":"lost_events","data":1}', good.replace('"56":3', '"99":3'),
                good.replace('"56":3', '"56":true'), good.replace('"@completed":1', '"@completed":0'),
                good + good, good.replace('"56":3', '"56":3,"56":4'), "\v" + good,
                "\n\n" + good + '{"type":"helper_error","msg":"suppressed"}', "\n\n"):
        try:
            parse_counts(bad, reasons)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe output accepted")
    assert parse_reasons('field:enum skb_drop_reason reason; __print_symbolic(REC->reason, { 8, "NETFILTER_DROP" }, { 56, "UNHANDLED_PROTO" })') == reasons
    print(json.dumps({"self_test": "PASS", "live_attachment": False}))


if __name__ == "__main__":
    raise SystemExit(main())
