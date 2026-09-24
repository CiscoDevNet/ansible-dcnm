"""A dot1q port-channel must accept a QoS policy like every other port-channel mode.

``int_port_channel_dot1q_tunnel_host`` declares ``ENABLE_QOS``, ``QOS_POLICY`` and
``QUEUING_POLICY`` exactly like the trunk and access templates -- read from the controller,
not assumed. The module could not reach them: ``pc_prof_spec_dot1q`` did not accept the three
keys, and the dot1q branch of ``dcnm_intf_get_pc_payload`` did not write the nvPairs. Both
had to change; fixing only the spec would have let the keys validate and then be dropped.

The visible consequence was not QoS itself. ``DISABLE_QOS_STATS`` and
``DISABLE_QUEUING_STATS`` only append ``no-stats`` to the ``service-policy`` line that
ENABLE_QOS emits, so with no way to turn QoS on, those two fields were registered and
transported but could never produce CLI -- exercised, never validated.

The QoS block was duplicated verbatim in the trunk, access and l3 branches. It is extracted
into ``dcnm_intf_set_qos_nv_pairs`` rather than copied a fourth time; these cases assert the
four modes agree, which is the property the duplication kept accidentally.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import inspect
import re

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

MODES_WITH_QOS = ("trunk", "access", "l3", "dot1q")


def _spec_keys(name):
    """Keys of one pc_prof_spec_* literal, read from the source of the validator."""
    src = inspect.getsource(dcnm_interface.DcnmIntf.dcnm_intf_validate_port_channel_input)
    body = re.search(
        r"%s = dict\((.*?)\n        \)\n" % re.escape(name), src, re.S
    )
    assert body is not None, "{0} not found in the validator".format(name)
    return set(re.findall(r"(\w+)=dict\(", body.group(1)))


@pytest.mark.parametrize("key", ["enable_qos", "qos_policy", "queuing_policy"])
def test_dot1q_spec_accepts_the_qos_keys(key):
    """The fix. Without it the validator rejects the key before anything is sent."""
    assert key in _spec_keys("pc_prof_spec_dot1q")


@pytest.mark.parametrize("key", ["enable_qos", "qos_policy", "queuing_policy"])
def test_dot1q_declares_the_qos_keys_exactly_like_access(key):
    """Same keys, and nothing invented: access is the reference that already worked."""
    assert key in _spec_keys("pc_prof_spec_access")
    assert key in _spec_keys("pc_prof_spec_dot1q")


def test_every_qos_capable_mode_writes_the_nvpairs_through_one_helper():
    """No mode may keep its own copy of the block.

    The point of extracting it is that the four branches cannot drift apart. If someone
    re-inlines the assignment into one branch, that branch starts evolving on its own --
    which is exactly how dot1q ended up without QoS in the first place.
    """
    src = inspect.getsource(dcnm_interface.DcnmIntf.dcnm_intf_get_pc_payload)
    assert 'nvPairs"]["ENABLE_QOS"]' not in src, (
        "dcnm_intf_get_pc_payload writes ENABLE_QOS inline again; it must go through "
        "dcnm_intf_set_qos_nv_pairs so every mode stays in agreement"
    )
    assert src.count("dcnm_intf_set_qos_nv_pairs") == len(MODES_WITH_QOS), (
        "expected one helper call per QoS-capable mode {0}, found {1}".format(
            MODES_WITH_QOS, src.count("dcnm_intf_set_qos_nv_pairs")
        )
    )


def test_the_helper_keeps_the_original_semantics():
    """Extraction must not change behaviour: same three outputs, same fallbacks."""
    nv = {}
    inst = dcnm_interface.DcnmIntf.__new__(dcnm_interface.DcnmIntf)

    # QoS off: both QoS nvPairs are cleared, queuing is independent of the toggle
    inst.dcnm_intf_set_qos_nv_pairs({"enable_qos": False, "qos_policy": "ignored"}, nv)
    assert nv["ENABLE_QOS"] is False
    assert nv["QOS_POLICY"] == ""
    assert nv["QUEUING_POLICY"] == ""

    # QoS on with a policy
    inst.dcnm_intf_set_qos_nv_pairs(
        {"enable_qos": True, "qos_policy": "P", "queuing_policy": "Q"}, nv
    )
    assert nv["ENABLE_QOS"] is True
    assert nv["QOS_POLICY"] == "P"
    assert nv["QUEUING_POLICY"] == "Q"

    # QoS on without a policy: the key is still written, empty
    inst.dcnm_intf_set_qos_nv_pairs({"enable_qos": True}, nv)
    assert nv["ENABLE_QOS"] is True
    assert nv["QOS_POLICY"] == ""

    # a queuing policy alone does not need ENABLE_QOS
    inst.dcnm_intf_set_qos_nv_pairs({"queuing_policy": "Q"}, nv)
    assert nv["ENABLE_QOS"] is False
    assert nv["QUEUING_POLICY"] == "Q"


def test_the_two_stats_bindings_are_registered_for_dot1q():
    """Guard the guard.

    This whole change exists so DISABLE_QOS_STATS and DISABLE_QUEUING_STATS can reach CLI on
    a dot1q port-channel. If those bindings ever left the registry, the cases above would
    still pass while the reason for the change had evaporated.
    """
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
        resolve_binding,
    )

    for key in ("disable_qos_stats", "disable_queuing_stats"):
        assert (
            resolve_binding("int_port_channel_dot1q_tunnel_host", key) is not None
        ), "{0} is no longer registered for the dot1q parent".format(key)
