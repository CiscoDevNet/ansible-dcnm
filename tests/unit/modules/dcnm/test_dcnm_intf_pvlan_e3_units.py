"""Helper-level and static E3 checks (they do not replace the real-main cases in test_dcnm_intf_pvlan_e3.py).

Helper: the owned vocabulary, the observed/owned/foreign split, and a sweep over EVERY measured
discovery preview with device authority: each keeps its E2 decision under the transition's
vocabulary; adding a SYNTHETIC negation of an unowned device command turns every one into a
refusal; adding the unowned command untouched never changes the decision (no obligation).
Static: the gate passes the transition vocabulary, and the check-mode branch of the PVLAN
preflight is decided before the capability probe can be evaluated.

On the frozen E2 helper (no vocabulary API) assess() falls back to the E2 signature, so the
sweep compares behavior rather than failing at import.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ast
import inspect

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import DEVICE, TRANSITIONS, module

VOCAB = getattr(P, "transition_vocabulary", None)
ACL = "ip access-group KEEP-IN in"  # SYNTHETIC
UNOWNED = (ACL, "ip dhcp snooping trust")


def assess(body, entry, desired, pre, post):
    if VOCAB is None:
        return P.assess_target(body, entry, "Ethernet1/7", desired)
    return P.assess_target(body, entry, "Ethernet1/7", desired, VOCAB(pre, post))


def entry(phase, extra_running=None):
    running = list(phase["running_stanza"])
    if extra_running:
        running.insert(1, "  " + extra_running)
    return {"runningConfig": running, "expectedConfig": phase["expected_stanza"]}


def body(phase):
    return P.split_blocks(phase["pendingConfig"])[0].get("ethernet1/7", [])


def sides(t):
    return (t["pre_policy"], t["pre_nv"]), (t["post_policy"], t["post_nv"])


PRE_CASES = sorted(c for c in TRANSITIONS if c in DEVICE)
POST_CASES = sorted(c for c in TRANSITIONS if c in DEVICE and "post" in DEVICE[c] and c != "PU3")


# ------------------------------------------------------------------ measured sweep
@pytest.mark.parametrize("case", PRE_CASES)
def test_measured_pre_deploy_decision_is_kept(case):
    t = TRANSITIONS[case]
    pre, post = sides(t)
    decision, problems = assess(body(DEVICE[case]["pre"]), entry(DEVICE[case]["pre"]), P.render(*post), pre, post)
    assert decision == ("refuse" if t["expect"] == "reject" else "deploy"), problems


@pytest.mark.parametrize("line", UNOWNED)
@pytest.mark.parametrize("case", [c for c in PRE_CASES if TRANSITIONS[c]["expect"] != "reject"])
def test_unowned_negation_turns_every_measured_transition_into_a_refusal(case, line):
    t = TRANSITIONS[case]
    pre, post = sides(t)
    decision, problems = assess(body(DEVICE[case]["pre"]) + ["no " + line], entry(DEVICE[case]["pre"], line), P.render(*post), pre, post)
    assert decision == "refuse" and any("does not own" in p for p in problems), problems


@pytest.mark.parametrize("line", UNOWNED)
@pytest.mark.parametrize("case", [c for c in PRE_CASES if TRANSITIONS[c]["expect"] != "reject"])
def test_untouched_unowned_command_keeps_the_measured_decision(case, line):
    t = TRANSITIONS[case]
    pre, post = sides(t)
    decision, problems = assess(body(DEVICE[case]["pre"]), entry(DEVICE[case]["pre"], line), P.render(*post), pre, post)
    assert decision == "deploy", problems


@pytest.mark.parametrize("line", UNOWNED)
@pytest.mark.parametrize("case", POST_CASES)
def test_measured_convergence_survives_an_untouched_unowned_command(case, line):
    t = TRANSITIONS[case]
    pre, post = sides(t)
    assert assess([], entry(DEVICE[case]["post"], line), P.render(*post), pre, post) == ("converged", [])


# ------------------------------------------------------------------ vocabulary and model
def test_vocabulary_owns_only_the_transition_policies():
    pvlan = P.transition_vocabulary((P.PVLAN_POLICY, {}), (P.PVLAN_POLICY, {}))
    reset = P.transition_vocabulary((P.PVLAN_POLICY, {}), (P.TRUNK_HOST_POLICY, {}))
    for line in ("switchport private-vlan mapping trunk 2210 2211", "switchport mode private-vlan host", "mtu 9216", "shutdown"):
        assert pvlan.owns(line) and reset.owns(line)
    for line in ("switchport mode trunk", "switchport trunk allowed vlan none", "ip port access-group FOO in"):
        assert not pvlan.owns(line) and reset.owns(line)
    for line in (ACL, "ip dhcp snooping trust", "no ip access-group KEEP-IN in"):
        assert not pvlan.owns(line) and not reset.owns(line)


def test_unmodeled_policy_contributes_nothing():
    v = P.transition_vocabulary(("int_access_host", {"CONF": ACL}), (P.PVLAN_POLICY, {}))
    assert not v.owns("switchport mode access") and not v.owns(ACL) and v.interferes("switchport access vlan 10")


def test_freeform_lines_are_owned_only_from_either_side_conf():
    v = P.transition_vocabulary((P.PVLAN_POLICY, {"CONF": ACL + "\n ip dhcp snooping trust "}), (P.PVLAN_POLICY, {"CONF": ""}))
    assert v.owns(ACL) and v.owns("ip dhcp snooping trust") and not v.owns("ip verify unicast source reachable-via rx")


def test_interference_is_namespace_based():
    v = P.transition_vocabulary((P.PVLAN_POLICY, {}), (P.PVLAN_POLICY, {}))
    for line in ("speed 1000", "switchport access vlan 10", "spanning-tree cost 4", "no lldp transmit-tlv", "service-policy input X"):
        assert v.interferes(line)
    for line in (ACL, "ip dhcp snooping trust", "storm-control broadcast level 5.00", "ip port access-group FOO in", "switchportx"):
        assert not v.interferes(line)


def test_cli_model_separates_observed_owned_and_foreign():
    v = P.transition_vocabulary((P.PVLAN_POLICY, {}), (P.PVLAN_POLICY, {}))
    m = P.cli_model(["mtu 9216", ACL, "switchport mode private-vlan trunk promiscuous", "switchport private-vlan mapping trunk 2210 2211"], v)
    assert m.foreign == {ACL} and ACL not in m.scalars
    assert m.pairs == {(2210, 2211)} and {"mtu 9216", "switchport", "no shutdown"} <= m.scalars


def test_foreign_pre_line_is_never_removable_and_never_required():
    v = P.transition_vocabulary((P.PVLAN_POLICY, {}), (P.PVLAN_POLICY, {}))
    pre = P.cli_model(["switchport mode private-vlan host", "switchport private-vlan host-association 2210 2211", ACL], v)
    post = P.cli_model(["switchport mode private-vlan host", "switchport private-vlan host-association 2210 2211", "description x"], v)
    assert P.validate_transition(["description x"], pre, post) == []  # the ACL is not an obligation
    problems = P.validate_transition(["no " + ACL], pre, post)
    assert problems and "does not own" in problems[0]


def test_owned_withdrawals_are_still_required_and_allowed():
    v = P.transition_vocabulary((P.PVLAN_POLICY, {"DESC": "old"}), (P.PVLAN_POLICY, {}))
    pre = P.cli_model(["switchport mode private-vlan host", "description old"], v)
    post = P.cli_model(["switchport mode private-vlan host"], v)
    assert P.validate_transition(["no description old"], pre, post) == []
    assert P.validate_transition(["shutdown"], pre, post) != []  # the owned withdrawal is missing


def test_model_default_has_no_foreign_lines():
    assert P.render(P.PVLAN_POLICY, TRANSITIONS["G6-M1"]["post_nv"]).foreign == set()


# ------------------------------------------------------------------ static checks
def _source(func):
    return inspect.getsource(func)


def test_static_gate_passes_the_transition_vocabulary():
    tree = ast.parse(inspect.cleandoc("\n" + _source(module.DcnmIntf.dcnm_intf_pvlan_deploy_gate)))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "pvlan_assess_target"]
    assert len(calls) == 1 and len(calls[0].args) == 5
    vocab = calls[0].args[4]
    assert isinstance(vocab, ast.Call) and vocab.func.id == "pvlan_transition_vocabulary"


def test_static_check_mode_is_decided_before_the_capability_probe():
    src = _source(module.DcnmIntf.dcnm_intf_pvlan_preflight)
    assert src.count("self.has_bulk_api") == 1
    assert src.index("if self.module.check_mode:") < src.index("self.has_bulk_api")
    assert src.index("elif not self.has_bulk_api") > src.index("could not be verified in check mode")


def test_static_shared_bulk_helper_is_the_post_probe():
    src = inspect.getsource(module.dcnm_get_bulk_api_support)
    assert 'method = "POST"' in src and "bulk-update/networks" in src
