"""Redaction around the withdrawal paths, measured against the REAL Ansible serialiser.

WHY THE REAL SERIALISER

An earlier version of this coverage asserted `MARKER not in json.dumps(result)` against a
harness whose base class replaces `exit_json`/`fail_json` with doubles that raise instead
of serialising. `_return_formatted` ran zero times, `remove_values()` never ran, and the
result carried no `invocation` block -- the one place a declared `no_log` value actually
leaks from. Replacing the serialiser with one that raises did not fail that test. It
observed nothing. That was a MISSING PROOF, not a demonstrated leak: nothing here says
material was ever exposed.

These build a real `AnsibleModule`, restore the real `exit_json`/`fail_json`, run
`main()`, and read the bytes Ansible would print.

EVERY CASE ASSERTS ITS ADVERTISED OUTCOME AS WELL AS REDACTION. A test that only checks
"the marker is absent" passes just as well when the run died early for an unrelated
reason, so each case also pins whether the module succeeded or refused, and why.

Every marker is synthetic. No lab secret, no captured controller payload.

NOT LIVE TESTED IN THIS GENERATION.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    resolve_binding as _resolve_binding,
)

from .gie_withdrawal_harness import (
    IF_A,
    ROUTED,
    base_for,
    build_have,
    cfg,
    emit_real_result,
    real_serialiser_is_genuine,
    split_calls,
    an_unclassifiable_key,
)

MARKER = "SyntheticOspfAuthMaterial9c1f"
CTRL_MARKER = "SyntheticControllerOnlyKey4d7a"
VISIBLE = "SyntheticVisibleDescription2b8e"


def _routed_cfg(**profile):
    return [cfg(IF_A, base_for(ROUTED, description=VISIBLE, **profile), deploy=False)]


def parsed(out):
    assert out.strip(), "the module printed nothing: main() never reached a real exit"
    return json.loads(out)


# ------------------------------------------------------------------ reachability guards
def test_the_captured_serialiser_is_genuine_and_not_a_test_double():
    """The guard for everything below. A double here makes every assertion vacuous."""
    assert real_serialiser_is_genuine(), (
        "exit_json/fail_json were captured from the netcommon test doubles rather than "
        "from ansible.module_utils.basic; these tests would measure the doubles")


def test_the_emitted_result_carries_a_real_invocation_block():
    """Without `invocation` there is nothing for no_log to protect and every absence
    assertion below is trivially true."""
    have = build_have(ROUTED)
    out, _calls = emit_real_result(_routed_cfg(), "replaced", have)
    doc = parsed(out)
    assert "invocation" in doc and "module_args" in doc["invocation"]


def test_an_unregistered_value_does_appear_so_absence_is_meaningful():
    """The non-vacuity control: an ordinary non-secret field must reach the output."""
    have = build_have(ROUTED)
    out, _calls = emit_real_result(_routed_cfg(), "replaced", have)
    assert VISIBLE in out, (
        "an ordinary non-secret value did not reach the emitted result; the absence of a "
        "secret would then say nothing about redaction")


# ------------------------------------------------------------------ input-side material
@pytest.mark.parametrize("state", ["replaced", "merged"])
def test_input_material_is_redacted_on_a_run_that_succeeds(state):
    have = build_have(ROUTED, enable_ospf_auth=True, ospf_auth_key=MARKER,
                      ospf_auth_key_id=9)
    out, calls = emit_real_result(
        _routed_cfg(enable_ospf_auth=True, ospf_auth_key=MARKER, ospf_auth_key_id=9),
        state, have)
    doc = parsed(out)
    assert not doc.get("failed"), (
        "this case advertises a SUCCESSFUL run; it failed with: %s" % doc.get("msg"))
    assert MARKER not in out, "declared no_log input reached the emitted result"
    assert "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER" in out, (
        "the marker is absent but so is the placeholder, which suggests the field was "
        "dropped rather than scrubbed")


def test_input_material_is_redacted_in_check_mode_and_check_mode_succeeds():
    have = build_have(ROUTED, enable_ospf_auth=True, ospf_auth_key=MARKER,
                      ospf_auth_key_id=9)
    out, calls = emit_real_result(
        _routed_cfg(enable_ospf_auth=True, ospf_auth_key=MARKER, ospf_auth_key_id=9),
        "replaced", have, check_mode=True)
    doc = parsed(out)
    assert not doc.get("failed"), doc.get("msg")
    assert len(split_calls(calls)["updates"]) == 0, "check mode sent a configuration call"
    assert MARKER not in out
    assert "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER" in out


def test_input_material_is_redacted_on_the_c8_refusal_which_must_fail_for_its_own_reason():
    """A refusal is still a result, and `invocation.module_args` rides on it.

    An unclassifiable row is present in HAVE and omitted from the request, so the withdrawal
    preflight refuses the run -- while still holding the material it was handed. The row is
    DERIVED: this named `ospf_cost` until G37 measured its reset.
    """
    unclassifiable = an_unclassifiable_key(ROUTED)
    # The VALUE is derived from the row's declared type, not hardcoded. It used to be the
    # literal `100`, which silently assumed the derived row was an integer; once a local
    # EXPERIMENTAL generation registered the last unclassifiable integers on this parent the
    # helper began returning a STRING row and `build_have` refused the int before any payload
    # existed -- the case then failed deep in the harness instead of stating the real problem.
    _b = _resolve_binding(ROUTED, unclassifiable)
    # Keep the synthetic string within ospf_tag's public length bound so the
    # C8 refusal, rather than input validation, remains the branch under test.
    probe_value = {"integer": 100, "boolean": True}.get(_b["type"], "PILOT-UNCLASSIFIED")
    have = build_have(ROUTED, enable_ospf_auth=True, ospf_auth_key=MARKER,
                      ospf_auth_key_id=9, **{unclassifiable: probe_value})
    out, calls = emit_real_result(
        _routed_cfg(enable_ospf_auth=True, ospf_auth_key=MARKER, ospf_auth_key_id=9),
        "replaced", have)
    doc = parsed(out)
    assert doc.get("failed"), "this case advertises the C8 refusal; the run succeeded"
    msg = str(doc.get("msg", ""))
    assert unclassifiable in msg and "cannot be classified" in msg, msg
    assert str(probe_value) not in msg, "the refusal named the value"
    assert len(split_calls(calls)["updates"]) == 0
    assert MARKER not in out, "a refusal serialised the material it was handed"


def test_the_key_id_is_not_registered_and_stays_readable():
    """Over-registering is its own defect: registering the id would blank every '9'."""
    have = build_have(ROUTED, enable_ospf_auth=True, ospf_auth_key=MARKER,
                      ospf_auth_key_id=9)
    out, _calls = emit_real_result(
        _routed_cfg(enable_ospf_auth=True, ospf_auth_key=MARKER, ospf_auth_key_id=9),
        "replaced", have)
    doc = parsed(out)
    prof = doc["invocation"]["module_args"]["config"][0]["profile"]
    assert prof.get("ospf_auth_key_id") == 9, (
        "the key id was scrubbed or altered; it is not secret and operators read it")


# ------------------------------------------------------------------ controller-only material
def _controller_only_have():
    have = build_have(ROUTED, enable_ospf_auth=True, ospf_auth_key_id=9)
    have[0]["interfaces"][0]["nvPairs"]["OSPF_AUTH_KEY"] = CTRL_MARKER
    return have


# `query` is the arrangement, and the reason is worth stating: it is the state that
# actually SERIALISES what the controller returned. An earlier attempt used `replaced`,
# where the run ends in a withdrawal refusal whose result carries no HAVE at all -- the
# marker was absent whether or not registration ran, so the positive test proved nothing.
# The negative control below is what caught that, and is kept for exactly that reason.
def test_controller_only_material_is_redacted_and_the_query_succeeds():
    """This material is never in `module_args`; it exists only in what NDFC returned, and
    is protected by the controller-secret walk rather than by the argument spec."""
    out, calls = emit_real_result(
        [cfg(IF_A, {"mode": "routed"}, deploy=False)], "query", _controller_only_have())
    doc = parsed(out)
    assert not doc.get("failed"), "this case advertises a successful query: %s" % doc.get("msg")
    assert len(split_calls(calls)["updates"]) == 0
    assert IF_A in out, "the query returned nothing identifying the interface"
    assert CTRL_MARKER not in out, (
        "controller-supplied key material was serialised; the HAVE walk did not register it")


def test_disabling_registration_makes_the_controller_only_check_fail():
    """THE NEGATIVE CONTROL. Disabling registration must make the test above fail.

    Without it, that test would also pass if the material simply never reached the result
    for an unrelated reason -- which is exactly what happened on the first arrangement.
    """
    out, _calls = emit_real_result(
        [cfg(IF_A, {"mode": "routed"}, deploy=False)], "query", _controller_only_have(),
        extra_patch=patch.object(
            module.DcnmIntf, "dcnm_intf_register_controller_secrets",
            lambda self, payload: None))
    assert CTRL_MARKER in out, (
        "registration was disabled and the material STILL did not appear, so the positive "
        "test does not prove registration protects it; it needs a different arrangement")
