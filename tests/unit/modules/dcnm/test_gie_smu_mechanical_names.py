"""S1 of the SMU adaptation: the mechanical UPPER_SNAKE -> camelCase wire renames.

WHAT S1 CHANGED, AND WHAT IT DID NOT

The SMU templates installed on the .90 controller renamed SOME declared variables to
camelCase. This is NOT a blanket migration: in the captured `int_access_host` body,
SERIAL_NUMBER, INTF_NAME, MTU, SPEED, DESC, CDP_ENABLE and ENABLE_ORPHAN_PORT are still
UPPER_SNAKE, while `lldpTransmit` and `aclFilter` are camelCase. So every rename in S1 was
read out of a declaration in `capture-R2/<parent>.template`, and only the 123 identities
whose new name is exactly the mechanical transform of the old one are in scope.

The public YAML contract is untouched: `flowcontrol_receive`, `acl_filter`,
`spanning_tree_port_type`, `guard_mode` and the rest are spelled exactly as before.

EXPECTATIONS ARE LITERALS, NOT DERIVED

Every expected wire name below is written out by hand from the captured declaration, with
its template line. None is computed by a casing helper or read back from the registry, so a
wrong mapping in the registry cannot make these tests agree with it.

  int_access_host.template:214   string aclFilter
  int_access_host.template:~513  enum flowcontrolReceive      (public "on"/"off")
  int_trunk_host.template:160    enum GUARD_MODE              <- deliberately NOT renamed
  int_routed_host.template       integer ospfCost

STILL PENDING (S2), deliberately absent here: the 72 special renames such as
DISABLE_LLDP_TRANSMIT -> lldpTransmit and DISABLE_QOS_STATS -> qosStatsSuppressed, the 8
enum-value/metadata changes such as no_change -> noChange, and the one unresolved
counterpart int_port_channel_trunk_host::ENABLE_VPC_PEER_LINK. S1 is partial and not
deployable on its own.

NOT LIVE TESTED. Offline only; nothing contacts a controller.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table

from .gie_withdrawal_harness import (
    ACCESS,
    TRUNK,
    base_for,
    build_have,
    run,
    split_calls,
    request_nvpairs,
    diff_nvpairs,
)

# Reviewed literals. Left side is the public option, right side the declared SMU wire key.
SMU_ACL_FILTER = "aclFilter"
SMU_FLOWCONTROL_RECEIVE = "flowcontrolReceive"
SMU_SPANNING_TREE_PORT_TYPE = "spanningTreePortType"
UNRENAMED_GUARD_MODE = "GUARD_MODE"

# The old names must not reappear anywhere in an outbound payload.
OLD_ACL_FILTER = "ACL_FILTER"
OLD_FLOWCONTROL_RECEIVE = "FLOWCONTROL_RECEIVE"

# Native module fields. They are NOT registry bindings and the captured bodies still declare
# them in UPPER_SNAKE, so a blanket casing pass would show up here.
NATIVE_UPPER = ("MTU", "SPEED", "DESC", "ADMIN_STATE", "CONF")


def rows():
    t = table.BINDING_TABLE
    return list(t.values()) if isinstance(t, dict) else list(t)


def wire_of(parent, profile_key):
    for r in rows():
        if r["parent_template"] == parent and r["profile_key"] == profile_key:
            return r["parent_nvpair"]
    raise AssertionError("no registry row for %s::%s" % (parent, profile_key))


def emitted(calls):
    """Every nvPair the module actually put on the wire, merged into one map."""
    out = {}
    for nv in request_nvpairs(calls):
        out.update(nv)
    return out


# ------------------------------------------------------- registry says the reviewed literal
def test_registry_carries_the_declared_smu_names():
    """The table's wire key equals the hand-reviewed declaration, per parent."""
    assert wire_of(ACCESS, "acl_filter") == SMU_ACL_FILTER
    assert wire_of(ACCESS, "flowcontrol_receive") == SMU_FLOWCONTROL_RECEIVE
    assert wire_of(TRUNK, "flowcontrol_receive") == SMU_FLOWCONTROL_RECEIVE
    assert wire_of(ACCESS, "spanning_tree_port_type") == SMU_SPANNING_TREE_PORT_TYPE


def test_a_field_the_smu_did_not_rename_keeps_its_upper_name():
    """GUARD_MODE is declared UPPER_SNAKE in int_trunk_host.template:160. The control that
    proves S1 renamed a confirmed SET, not everything it could reach."""
    assert wire_of(TRUNK, "guard_mode") == UNRENAMED_GUARD_MODE


def test_the_public_option_names_did_not_change():
    """The YAML contract is the thing S1 must NOT move."""
    keys = {r["profile_key"] for r in rows()}
    for public in ("acl_filter", "flowcontrol_receive", "spanning_tree_port_type", "guard_mode"):
        assert public in keys, public


# ------------------------------------------------------------------- production, real main()
def test_public_input_emits_the_smu_key_and_not_the_old_one():
    """Unchanged public input -> the SMU key, correct value, and no duplicate old key."""
    profile = base_for(ACCESS, flowcontrol_receive="on", acl_filter="ACL-PILOT")
    result, calls = run(profile, "merged")

    assert not result.get("failed"), result.get("msg")
    nv = emitted(calls)
    assert nv.get(SMU_FLOWCONTROL_RECEIVE) == "on", nv
    assert nv.get(SMU_ACL_FILTER) == "ACL-PILOT", nv
    assert OLD_FLOWCONTROL_RECEIVE not in nv, "the old wire key was emitted as well"
    assert OLD_ACL_FILTER not in nv, "the old wire key was emitted as well"


def test_native_fields_were_not_swept_into_camel_case():
    """Only declared renames moved. The native payload keys are still UPPER_SNAKE."""
    result, calls = run(base_for(ACCESS, flowcontrol_receive="on"), "merged")
    assert not result.get("failed"), result.get("msg")
    nv = emitted(calls)
    for key in NATIVE_UPPER:
        assert key in nv, "native field %s vanished from the payload: %s" % (key, sorted(nv))
    for key in NATIVE_UPPER:
        camel = key.lower() if "_" not in key else key.split("_")[0].lower() + "".join(p.capitalize() for p in key.split("_")[1:])
        assert camel not in nv, "native field %s was camelCased to %s" % (key, camel)


def test_have_carrying_the_smu_key_is_preserved_under_merged():
    """A HAVE written with the SMU key is read, and an omission under merged keeps it.

    The HAVE is built with the literal SMU key injected by hand rather than taken from the
    module's own output, so the read path is tested against the declaration, not against
    whatever the producer happens to emit.
    """
    have = build_have(ACCESS, "acl_filter", "ACL-PILOT")
    nv = have[0]["interfaces"][0]["nvPairs"]
    assert SMU_ACL_FILTER in nv, "the producer did not use the SMU key: %s" % sorted(nv)
    # Injected literal: prove the reader keys on this name and nothing else.
    nv.pop(OLD_ACL_FILTER, None)
    nv[SMU_ACL_FILTER] = "ACL-PILOT"

    result, calls = run(base_for(ACCESS), "merged", have=copy.deepcopy(have))

    assert not result.get("failed"), result.get("msg")
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "merged omission did not preserve; it configured again"
    assert buckets["deploys"] == []


def test_registered_binding_still_withdraws_under_the_new_name():
    """replaced / check / rerun for a registered binding, all through real main()."""
    have = build_have(ACCESS, "flowcontrol_receive", "on")
    want = base_for(ACCESS)  # omits flowcontrol_receive -> withdrawal

    # check mode: reports the reset, writes nothing
    checked, check_calls = run(want, "replaced", have=copy.deepcopy(have), check_mode=True)
    assert not checked.get("failed"), checked.get("msg")
    assert split_calls(check_calls)["updates"] == [], "check mode configured"
    reported = {}
    for nv in diff_nvpairs(checked):
        reported.update(nv)
    assert reported.get(SMU_FLOWCONTROL_RECEIVE) == "off", reported
    assert OLD_FLOWCONTROL_RECEIVE not in reported

    # real run: the reset reaches the wire under the SMU key
    applied, apply_calls = run(want, "replaced", have=copy.deepcopy(have))
    assert not applied.get("failed"), applied.get("msg")
    nv = emitted(apply_calls)
    assert nv.get(SMU_FLOWCONTROL_RECEIVE) == "off", nv
    assert OLD_FLOWCONTROL_RECEIVE not in nv

    # rerun against a HAVE already at the reset: nothing left to send
    at_reset = build_have(ACCESS, "flowcontrol_receive", "off")
    rerun, rerun_calls = run(want, "replaced", have=at_reset)
    assert not rerun.get("failed"), rerun.get("msg")
    assert split_calls(rerun_calls)["updates"] == [], "the rerun configured again"
