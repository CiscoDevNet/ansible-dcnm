"""OSPF dependent fields after a disable: authentication, merged disable, explicit contradictions, reset guidance.

Template evidence (int_routed_host 6d37ea6a, int_subif e9f9bd9c, int_vlan f32ef586, static reads):
  * every OSPF option is rendered only when `ospf` is true, and a non-neutral option is refused while it is false;
  * the simple-key encryption type is used and validated only with a non-empty `ospfAuthenticationKey`;
  * the message-digest key ID and key are validated and rendered only when `ospfAuthentication` is true;
  * `ospfTag` is required while `ospf` is true.
NDFC 12.6.0.267 stores `OSPF_AUTH_KEY` as "" with authentication off (read back); a set -> "" transition of a real key
is NOT measured.

Real main() through gie_withdrawal_harness. Synthetic secrets only; no message may contain them.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import test_dcnm_intf_default_reset_registered_f2 as F2
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import test_gie_ospf_gate_inert_withdrawal as G
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import test_gie_thin_engine as thin

SYN_MD5 = "SYNTH-MD5-KEY-NOT-REAL-0001"
SYN_SIMPLE = "SYNTH-SIMPLE-NOT-REAL-02"
PARENTS = (h.ROUTED, h.SUBIF, h.SVI)
NO_REQUEST = "No configuration or deployment request was sent"


def sent(calls):
    pol = F2.reset_policies(calls)
    return pol[0]["interfaces"][0]["nvPairs"] if pol else None


def assert_no_secret(result):
    text = json.dumps(result.get("msg", ""))
    assert SYN_MD5 not in text and SYN_SIMPLE not in text


def refused(result, calls, *needles):
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    for n in needles:
        assert n in result["msg"], result["msg"]
    assert NO_REQUEST in result["msg"]
    assert_no_secret(result)


def accepted(result, calls):
    assert not result.get("failed"), result.get("msg")
    assert_no_secret(result)
    return sent(calls)


def routed_have(**nv):
    base = dict(ospf="true")
    base.update(nv)
    return G.real_have(**base)


def disable_profile(parent):
    return G.OSPF_OFF if parent == h.ROUTED else h.base_for(parent, enable_ospf=False)


def run_parent(parent, profile, state, have):
    if parent == h.ROUTED:
        return F2.run(state, have, "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    return h.run(profile, state, have=have, parent=parent)


def have_for(parent, **profile):
    if parent == h.ROUTED:
        return G.real_have(**dict((table.resolve_binding(parent, k)["parent_nvpair"], v if not isinstance(v, bool)
                                   else json.dumps(v)) for k, v in profile.items()))
    return h.build_have(parent, **profile)


# ------------------------------------------------------------------ R1: reset guidance on a same-parent role default
@pytest.mark.parametrize("state", ("deleted", "overridden"))
def test_border_reset_with_ospf_on_disables_the_gate_in_the_same_reset(state):
    """D-3: the border default is int_routed_host itself and its reset sends ospf "false", so the stored tag is inert under
    the final gate: one reset, no remedy needed (test_gie_border_ospf_reset.py has the full matrix)."""
    result, calls = F2.run(state, G.real_have(), "border", configs=None if state == "deleted" else [])
    accepted(result, calls)
    nv = F2.nvpairs_of_reset(calls)
    assert nv["ospf"] == "false" and "ospfTag" not in nv


@pytest.mark.parametrize("state", ("deleted", "overridden"))
def test_border_reset_after_disable_is_accepted(state):
    result, calls = F2.run(state, G.ospf_off_have(), "border", configs=None if state == "deleted" else [])
    accepted(result, calls)


# ------------------------------------------------------------------ simple key and its encryption type
@pytest.mark.parametrize("keytype", ("0", "7"))
@pytest.mark.parametrize("with_key", (True, False))
def test_disable_with_a_stored_encryption_type_is_accepted_and_keeps_it_inert(keytype, with_key):
    have = routed_have(ospfAuthenticationKeyType=keytype, ospfAuthenticationKey=SYN_SIMPLE if with_key else "")
    result, calls = G.replaced(G.OSPF_OFF, have)
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv["ospfAuthenticationKey"] == ""
    assert nv["ospfAuthenticationKeyType"] == keytype, "the type configures nothing without a key: kept as stored"


@pytest.mark.parametrize("parent", (h.SUBIF, h.SVI))
def test_disable_with_a_stored_encryption_type_on_subif_and_svi(parent):
    have = h.build_have(parent, ospf_authentication_key_type="7", ospf_authentication_key=SYN_SIMPLE, **h.OSPF_CTX)
    result, calls = h.run(h.base_for(parent, enable_ospf=False), "replaced", have=have, parent=parent)
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv["ospfAuthenticationKey"] == "" and nv["ospfAuthenticationKeyType"] == "7"


def test_clearing_the_simple_key_with_ospf_on_keeps_the_type_inert():
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthenticationKeyType="7", ospfAuthenticationKey=SYN_SIMPLE)
    result, calls = G.replaced(dict(G.OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF"), have)
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfAuthenticationKey"] == "" and nv["ospfAuthenticationKeyType"] == "7"


def test_keeping_the_simple_key_and_omitting_its_type_is_still_refused():
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthenticationKeyType="7", ospfAuthenticationKey=SYN_SIMPLE)
    profile = dict(G.OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF", ospf_authentication_key=SYN_SIMPLE)
    result, calls = G.replaced(profile, have)
    refused(result, calls, "ospf_authentication_key_type on int_routed_host")


# ------------------------------------------------------------------ message-digest key
@pytest.mark.parametrize("parent", PARENTS)
def test_disabling_ospf_clears_the_message_digest_key(parent):
    have = have_for(parent, enable_ospf=True, ospf_tag="LAB-OSPF", ospf_area_id="0.0.0.0", enable_ospf_auth=True,
                    ospf_auth_key_id=5, ospf_auth_key=SYN_MD5)
    result, calls = run_parent(parent, disable_profile(parent), "replaced", have)
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv["ospfAuthentication"] == "false"
    assert nv["OSPF_AUTH_KEY"] == "" and nv["OSPF_AUTH_KEY_ID"] == "1"
    assert SYN_MD5 not in json.dumps(nv)


def test_disabling_authentication_only_clears_the_key_and_keeps_ospf():
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthentication="true", OSPF_AUTH_KEY_ID="5", OSPF_AUTH_KEY=SYN_MD5)
    result, calls = G.replaced(dict(G.OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF"), have)
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfAuthentication"] == "false" and nv["OSPF_AUTH_KEY"] == ""


def test_the_disable_after_clearing_is_a_noop():
    have = routed_have(ospfAuthentication="true", OSPF_AUTH_KEY_ID="5", OSPF_AUTH_KEY=SYN_MD5)
    first, calls = G.replaced(G.OSPF_OFF, have)
    assert not first.get("failed"), first.get("msg")
    result, calls = G.replaced(G.OSPF_OFF, F2.as_have(calls))
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("state", ("deleted", "overridden"))
def test_leaf_reset_after_disable_with_leftover_authentication_is_accepted(state):
    leftover = dict(G.OSPF_OPTIONS_NEUTRAL, ospfAuthenticationKeyType="7", OSPF_AUTH_KEY=SYN_MD5, OSPF_AUTH_KEY_ID="5")
    have = G.real_have(ospf="false", **leftover)
    result, calls = F2.run(state, have, "leaf", configs=None if state == "deleted" else [])
    nv = accepted(result, calls)
    assert F2.reset_policies(calls)[0]["policy"] == "int_trunk_host"
    assert not [k for k in nv if k.upper().startswith("OSPF")], "a source-only nvPair is never written to the destination"


@pytest.mark.parametrize("state", ("deleted", "overridden"))
def test_border_reset_clears_a_leftover_message_digest_key(state):
    have = G.real_have(ospf="false", **dict(G.OSPF_OPTIONS_NEUTRAL, OSPF_AUTH_KEY=SYN_MD5))
    result, calls = F2.run(state, have, "border", configs=None if state == "deleted" else [])
    nv = accepted(result, calls)
    assert nv.get("OSPF_AUTH_KEY") == "", "same policy: key material is cleared, not kept"


# ------------------------------------------------------------------ merged: explicit disable versus omission
@pytest.mark.parametrize("parent", PARENTS)
def test_merged_explicit_disable_neutralizes_the_stored_options(parent):
    option = {h.ROUTED: ("ospf_passive_mode", "passive", "ospfPassiveMode", "noChange"),
              h.SUBIF: ("ospf_passive_mode", "passive", "ospfPassiveMode", "noChange"),
              h.SVI: ("ospf_passive_mode", "passive", "ospfPassiveMode", "noChange")}[parent]
    have = have_for(parent, enable_ospf=True, ospf_tag="LAB-OSPF", ospf_area_id="0.0.0.0", ospf_cost=10,
                    enable_ospf_auth=True, ospf_auth_key_id=5, ospf_auth_key=SYN_MD5, **{option[0]: option[1]})
    result, calls = run_parent(parent, disable_profile(parent), "merged", have)
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv[option[2]] == option[3] and nv["ospfCost"] == ""
    assert nv["ospfAuthentication"] == "false" and nv["OSPF_AUTH_KEY"] == "" and nv["OSPF_AUTH_KEY_ID"] == "1"
    assert nv["ospfTag"] == "LAB-OSPF", "the tag has no neutral value: kept as stored, it configures nothing"


def test_merged_explicit_authentication_disable_clears_only_its_dependents():
    have = routed_have(ospfTag="LAB-OSPF", ospfPassiveMode="passive", ospfAuthentication="true",
                       OSPF_AUTH_KEY_ID="5", OSPF_AUTH_KEY=SYN_MD5)
    profile = {"mode": "routed", "enable_ospf_auth": False, "ipv4_addr": "192.0.2.17", "ipv4_mask_len": 30}
    result, calls = F2.run("merged", have, "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfPassiveMode"] == "passive"
    assert nv["ospfAuthentication"] == "false" and nv["OSPF_AUTH_KEY"] == "" and nv["OSPF_AUTH_KEY_ID"] == "1"


def test_merged_omission_of_the_gate_still_preserves_everything():
    have = routed_have(ospfTag="LAB-OSPF", ospfPassiveMode="passive", ospfCost="10")
    profile = {"mode": "routed", "description": "only-this", "ipv4_addr": "192.0.2.17", "ipv4_mask_len": 30}
    result, calls = F2.run("merged", have, "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfPassiveMode"] == "passive" and nv["ospfCost"] == "10"


def test_merged_explicit_disable_repeated_is_a_noop():
    have = routed_have(ospfTag="LAB-OSPF", ospfPassiveMode="passive")
    first, calls = F2.run("merged", have, "border", configs=[h.cfg(h.IF_A, G.OSPF_OFF, deploy=False)])
    assert not first.get("failed"), first.get("msg")
    result, calls = F2.run("merged", F2.as_have(calls), "border", configs=[h.cfg(h.IF_A, G.OSPF_OFF, deploy=False)])
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ explicit contradictions
@pytest.mark.parametrize("state", ("merged", "replaced"))
def test_an_explicit_option_while_disabling_ospf_is_refused(state):
    profile = dict(G.OSPF_OFF, ospf_cost=10)
    result, calls = F2.run(state, G.real_have(), "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    refused(result, calls, "ospf_cost (needs enable_ospf) on %s, parent int_routed_host" % h.IF_A)


@pytest.mark.parametrize("parent", (h.SUBIF, h.SVI))
def test_an_explicit_option_while_disabling_ospf_is_refused_on_subif_and_svi(parent):
    result, calls = h.run(h.base_for(parent, enable_ospf=False, ospf_cost=10), "replaced",
                          have=h.build_have(parent, **h.OSPF_CTX), parent=parent)
    refused(result, calls, "ospf_cost (needs enable_ospf)")


def test_an_explicit_neutral_option_while_disabling_ospf_is_accepted():
    profile = dict(G.OSPF_OFF, ospf_passive_mode="no_change")
    result, calls = F2.run("merged", G.real_have(), "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv["ospfPassiveMode"] == "noChange"


def test_an_explicit_option_on_a_new_interface_with_ospf_off_is_refused():
    profile = dict(G.OSPF_OFF, ospf_cost=10)
    result, calls = F2.run("merged", [], "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    refused(result, calls, "ospf_cost (needs enable_ospf)")


@pytest.mark.parametrize("state", ("merged", "replaced"))
def test_an_explicit_empty_tag_while_ospf_is_enabled_is_refused(state):
    profile = dict(G.OSPF_OFF, enable_ospf=True, ospf_tag="")
    result, calls = F2.run(state, G.real_have(), "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    refused(result, calls, "ospf_tag (with enable_ospf enabled) on %s" % h.IF_A)


def test_an_explicit_empty_tag_under_merged_with_ospf_on_only_in_have_is_refused():
    profile = {"mode": "routed", "ospf_tag": "", "ipv4_addr": "192.0.2.17", "ipv4_mask_len": 30}
    result, calls = F2.run("merged", G.real_have(), "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    refused(result, calls, "ospf_tag (with enable_ospf enabled)")


def test_an_explicit_empty_tag_while_disabling_ospf_is_accepted():
    profile = dict(G.OSPF_OFF, ospf_tag="")
    result, calls = G.replaced(profile, G.real_have())
    nv = accepted(result, calls)
    assert nv["ospf"] == "false" and nv["ospfTag"] == ""


def test_an_explicit_empty_message_digest_key_with_authentication_on_is_refused():
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthentication="true", OSPF_AUTH_KEY_ID="5", OSPF_AUTH_KEY=SYN_MD5)
    profile = dict(G.OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF", enable_ospf_auth=True, ospf_auth_key_id=5,
                   ospf_auth_key="")
    result, calls = G.replaced(profile, have)
    refused(result, calls, "ospf_auth_key (with enable_ospf_auth enabled)")


# ------------------------------------------------------------------ re-enable
def test_replaced_reenable_with_a_tag_after_disable_is_accepted():
    result, calls = G.replaced(dict(G.OSPF_OFF, enable_ospf=True, ospf_tag="NEW-TAG"), G.ospf_off_have())
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfTag"] == "NEW-TAG"


def test_merged_reenable_without_a_tag_reuses_the_stored_tag():
    """Merged preservation, documented: the tag kept by the disable is reused."""
    profile = dict(G.OSPF_OFF, enable_ospf=True)
    result, calls = F2.run("merged", G.ospf_off_have(), "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    nv = accepted(result, calls)
    assert nv["ospf"] == "true" and nv["ospfTag"] == G.FIXTURE["nvPairs"]["ospfTag"]


@pytest.mark.parametrize("state", ("merged", "replaced"))
def test_reenabling_authentication_over_a_cleared_key_needs_a_key(state):
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthentication="false", OSPF_AUTH_KEY_ID="1", OSPF_AUTH_KEY="")
    profile = dict(G.OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF", enable_ospf_auth=True, ospf_auth_key_id=5)
    result, calls = F2.run(state, have, "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])
    refused(result, calls, "ospf_auth_key (with enable_ospf_auth enabled)")


def test_reenabling_authentication_with_a_new_key_is_accepted():
    have = routed_have(ospfTag="LAB-OSPF", ospfAuthentication="false", OSPF_AUTH_KEY_ID="1", OSPF_AUTH_KEY="")
    profile = dict(G.OSPF_OFF, enable_ospf=True, ospf_tag="LAB-OSPF", enable_ospf_auth=True, ospf_auth_key_id=5,
                   ospf_auth_key=SYN_MD5)
    result, calls = G.replaced(profile, have)
    nv = accepted(result, calls)
    assert nv["ospfAuthentication"] == "true" and nv["OSPF_AUTH_KEY"] == SYN_MD5


# ------------------------------------------------------------------ registry, engine and generator contract
def test_declared_dependencies_cover_the_three_parents_and_the_loopback_contract():
    for parent in PARENTS:
        rows = dict((r["parent_nvpair"], r.get("inert_when")) for r in table.BINDING_TABLE if r["parent_template"] == parent)
        assert rows["ospfTag"] == {"nvpair": "ospf", "value": "false", "required": True}
        assert rows["OSPF_AUTH_KEY"] == {"nvpair": "ospfAuthentication", "value": "false", "required": True, "clear": ""}
        assert rows["ospfAuthenticationKeyType"] == {"nvpair": "ospfAuthenticationKey", "value": ""}
        assert rows["ospfCost"] == {"nvpair": "ospf", "value": "false", "strict": True}
        assert rows["ospf"] is None and rows["OSPF_AREA_ID"] is None
    # int_loopback: the same authentication gates; the tag and the options also stay live in the default VRF.
    lo = dict((r["parent_nvpair"], r.get("inert_when")) for r in table.BINDING_TABLE if r["parent_template"] == h.LOOPBACK)
    vrf = {"nvpair": "INTF_VRF", "values": ("", "default")}
    assert lo["ospfTag"] == {"nvpair": "ospf", "value": "false", "required": True, "unless": vrf}
    assert lo["ospfCost"] == {"nvpair": "ospf", "value": "false", "strict": True, "unless": vrf}
    assert lo["OSPF_AUTH_KEY"] == {"nvpair": "ospfAuthentication", "value": "false", "required": True, "clear": ""}
    assert lo["ospfAuthenticationKeyType"] == {"nvpair": "ospfAuthenticationKey", "value": ""}
    assert lo["ospf"] is None and lo["OSPF_AREA_ID"] is None


def test_engine_plan_chains_gates_and_never_judges_an_unknown_gate():
    have = {"ospf": "true", "ospfAuthentication": "true", "OSPF_AUTH_KEY_ID": "5", "OSPF_AUTH_KEY": SYN_MD5,
            "ospfCost": "10", "ospfTag": "T"}
    writes, conflicts = engine.gie_dependency_plan("int_routed_host", {"ospf": "false"}, have, {"ospf"}, True,
                                                   "12.6.0.267", h.SUPPORTED_PATCH)
    assert writes == {"ospfAuthentication": "false", "OSPF_AUTH_KEY_ID": "1", "OSPF_AUTH_KEY": "", "ospfCost": ""}
    assert conflicts == []
    writes, conflicts = engine.gie_dependency_plan("int_routed_host", {"ospfTag": ""}, {}, {"ospfTag"}, True,
                                                   "12.6.0.267", h.SUPPORTED_PATCH)
    assert writes == {} and conflicts == [], "no gate in WANT or HAVE: not judged"
    writes, conflicts = engine.gie_dependency_plan("int_routed_host", {"ospf": "false"}, have, {"ospf"}, True,
                                                   "12.6.0.267", None)
    assert writes == {} and conflicts == [], "capability disabled: nothing is written or refused"


def _rows_with(parent, nvpair, **row_update):
    rows = thin._as_slice_rows(table.BINDING_TABLE)
    for r in rows:
        if r["parent_template"] == parent and r["parent_nvpair"] == nvpair:
            r.update(row_update)
    return rows


@pytest.mark.parametrize("nvpair, inert_when, match", [
    ("ospfCost", {"nvpair": "ospf", "value": "false", "strict": "yes"}, "marker is a boolean"),
    ("ospfTag", {"nvpair": "ospf", "value": "false", "strict": True}, "strict without a reset_wire"),
    ("ospfTag", {"nvpair": "ospf", "value": "false", "clear": "x"}, "only an empty clear"),
    ("ospfCost", {"nvpair": "ospf", "value": "false", "clear": ""}, "only an empty clear"),
    ("ospfTag", {"nvpair": "ospf", "value": "false", "other": True}, "must be a mapping"),
])
def test_generator_rejects_malformed_dependency_markers(nvpair, inert_when, match):
    generator = thin._load_generator()
    with pytest.raises(ValueError, match=match):
        generator.compile_rows(_rows_with("int_routed_host", nvpair, inert_when=inert_when))


def test_generator_rejects_a_dependency_loop():
    generator = thin._load_generator()
    rows = _rows_with("int_routed_host", "ospfAuthentication", inert_when={"nvpair": "OSPF_AUTH_KEY_ID", "value": "1"})
    with pytest.raises(ValueError, match="loops"):
        generator.compile_rows(rows)
