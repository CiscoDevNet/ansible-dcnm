"""Repeatable timing of the 1,000 / 5,000-interface scenarios of test_pr725_scale_module_path.py (not collected by pytest).

Run from a tree whose `ansible_collections` root is on PYTHONPATH:

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<root> python -m \
        ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.pr725_scale_benchmark [--sizes 1000,5000] [--repeats 3] [--profile]

Same real `main()` and the same synthetic model as the regression; only inventory, transport and sleep are replaced. Each scenario
is timed as a whole and per module phase (want, have, diff, send), and the captured outbound request is serialized separately.
Medians of the repeats are printed as JSON with the environment. These are local CPU measurements of the module under a mocked
controller: not controller time, not end-to-end playbook time, not live performance, and not a CI threshold. `--profile` adds
the top cumulative functions of the populated-HAVE repeat at the largest size.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import argparse
import cProfile
import io
import json
import platform
import pstats
import statistics
import sys
import time
from unittest import mock

import ansible.release

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from . import gie_withdrawal_harness as H
from . import test_pr725_scale_module_path as S

PHASES = ("dcnm_intf_get_want", "dcnm_intf_get_have", "dcnm_intf_get_diff_merge", "dcnm_intf_get_diff_replaced",
          "dcnm_intf_get_diff_overridden", "dcnm_intf_send_message_to_dcnm")


def timed_run(cfgs, state, have=None, transport=None):
    spent = dict.fromkeys(PHASES, 0.0)
    patches = []
    for phase in PHASES:
        real = getattr(module.DcnmIntf, phase)

        def wrapper(self, *args, _real=real, _phase=phase, **kwargs):
            start = time.perf_counter()
            try:
                return _real(self, *args, **kwargs)
            finally:
                spent[_phase] += time.perf_counter() - start
        patches.append(mock.patch.object(module.DcnmIntf, phase, wrapper))
    if transport is not None:
        patches.append(mock.patch.object(H, "_transport", transport))
    for p in patches:
        p.start()
    try:
        start = time.perf_counter()
        result, calls = H.run_configs(cfgs, state, have=have, deploy=False)
        total = time.perf_counter() - start
    finally:
        for p in reversed(patches):
            p.stop()
    updates = H.split_calls(calls)["updates"]
    start = time.perf_counter()
    body = [json.dumps(c["payload"]) for c in updates]
    serialize = time.perf_counter() - start
    return {"total": total, "serialize": serialize, "phases": spent, "result": result, "calls": calls,
            "bytes": sum(len(b) for b in body)}


def scenarios(n):
    seed = H.run_configs(S.configs(n), "merged", deploy=False)[1]
    have = S.have_from(seed)
    return [
        ("create_merged_empty_have", lambda: timed_run(S.configs(n), "merged")),
        ("repeat_merged_populated_have", lambda: timed_run(S.configs(n), "merged", have=have)),
        ("omission_merged_populated_have", lambda: timed_run(S.configs(n, omit=S.REGISTERED), "merged", have=have)),
        ("omission_replaced_populated_have", lambda: timed_run(S.configs(n, omit=S.REGISTERED), "replaced", have=have)),
        ("failed_interface_read", lambda: timed_run(S.configs(n), "merged", transport=S.failing_transport)),
    ]


def measure(sizes, repeats):
    rows = []
    for n in sizes:
        for label, fn in scenarios(n):
            runs = [fn() for _repeat in range(repeats)]
            last = runs[-1]
            rows.append({
                "interfaces": n,
                "scenario": label,
                "repeats": repeats,
                "median_total_s": round(statistics.median(r["total"] for r in runs), 4),
                "median_phase_s": {p: round(statistics.median(r["phases"][p] for r in runs), 4) for p in PHASES
                                   if any(r["phases"][p] for r in runs)},
                "median_serialize_s": round(statistics.median(r["serialize"] for r in runs), 4),
                "request_bytes": last["bytes"],
                "request_bytes_per_interface": round(last["bytes"] / float(n), 1) if last["bytes"] else 0,
                "reads_by_endpoint": S.read_counts(last["calls"]),
                "writes": len(H.writes(last["calls"])),
                "changed": last["result"].get("changed"),
                "failed": bool(last["result"].get("failed")),
            })
    return rows


def profile(n):
    seed = H.run_configs(S.configs(n), "merged", deploy=False)[1]
    have = S.have_from(seed)
    prof = cProfile.Profile()
    prof.enable()
    H.run_configs(S.configs(n), "merged", have=have, deploy=False)
    prof.disable()
    out = io.StringIO()
    pstats.Stats(prof, stream=out).sort_stats("cumulative").print_stats(25)
    return out.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="1000,5000")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args(argv)
    sizes = [int(s) for s in args.sizes.split(",")]
    report = {
        "environment": {"python": platform.python_version(), "ansible_core": ansible.release.__version__,
                        "platform": platform.platform(), "machine": platform.machine(), "module": module.__file__},
        "model": "one switch; routed Ethernet; OSPF context + ospf_mtu_ignore/ospf_shutdown; synthetic 198.18.0.0/15 addresses",
        "note": "local CPU under a mocked controller; not controller, playbook or live performance; not a CI threshold",
        "rows": measure(sizes, args.repeats),
    }
    print(json.dumps(report, indent=2))
    if args.profile:
        print(profile(max(sizes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
