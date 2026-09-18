"""Source contract for no_log plumbing in dcnm_interface.

``validate_list_of_dicts()`` reads its ``module`` argument in exactly ONE place --
inside ``if no_log:`` -- where it registers the value in ``module.no_log_values`` so
Ansible scrubs it from every output (task result, -vvv, error messages, register).
When the argument is missing it raises deliberately rather than continuing, so a
secret can never be silently logged.

Both call sites in ``dcnm_intf_validate_interface_input`` must therefore pass
``self.module``:

  - the ``prof_spec`` call carries ``ospf_auth_key`` (``no_log=True``) TODAY;
  - the ``common_spec`` call carries no sensitive field today, so passing the module
    is a no-op there -- it is pinned so that adding one later cannot reintroduce the
    crash.

The tests above are static source contracts. The RUNTIME half used to live in
``test_dcnm_intf_ospf_legacy_key.py``, which was removed with the fabric-loopback
OSPF-auth capability -- taking the only runtime coverage of the leak with it. It is
re-established at the bottom of this file, and this time against the real serialiser
rather than a mocked module, because a mock has no ``_return_formatted`` and so can
report a scrub that never happened.

Run:
    pytest tests/unit/modules/dcnm/test_dcnm_intf_no_log_contract.py
"""

import os
import re

MODULE = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..",
    "plugins", "modules", "dcnm_interface.py",
)


def _module_source():
    with open(os.path.abspath(MODULE), encoding="utf-8") as fh:
        return fh.read()


def _validate_interface_input_body(src):
    """Return the body of dcnm_intf_validate_interface_input, up to the next def."""
    start = src.index("def dcnm_intf_validate_interface_input")
    rest = src[start:]
    nxt = re.search(r"\n    def [a-z_]+\(", rest)
    return rest[: nxt.start()] if nxt else rest


# --------------------------------------------------------------------------
# 1. Both call sites pass the AnsibleModule
# --------------------------------------------------------------------------
def test_both_validate_list_of_dicts_calls_pass_the_module():
    body = _validate_interface_input_body(_module_source())

    calls = re.findall(
        r"validate_list_of_dicts\((.*?)\)", body, re.DOTALL
    )
    assert len(calls) == 2, (
        "expected exactly two validate_list_of_dicts calls in "
        "dcnm_intf_validate_interface_input, found {0}".format(len(calls))
    )

    for args in calls:
        normalized = " ".join(args.split())
        assert "self.module" in normalized, (
            "validate_list_of_dicts({0}) does not pass self.module. Without it, any "
            "no_log spec param raises \"'<param>' is a no_log parameter / Ansible "
            "module object must be passed...\" and the secret cannot be "
            "registered for scrubbing.".format(normalized)
        )


# --------------------------------------------------------------------------
# 2. Each spec is still validated by its own call (no accidental merge)
# --------------------------------------------------------------------------
def test_common_and_profile_specs_are_validated_separately():
    body = _validate_interface_input_body(_module_source())
    flat = " ".join(body.split())

    assert "validate_list_of_dicts( config, common_spec, self.module )" in flat, (
        "the common_spec call must validate `config` and pass self.module"
    )
    assert "validate_list_of_dicts( plist, prof_spec, self.module )" in flat, (
        "the prof_spec call must validate `plist` and pass self.module"
    )


# --------------------------------------------------------------------------
# 3. The sensitive field is still declared no_log
# --------------------------------------------------------------------------
def test_ospf_auth_key_is_declared_no_log_and_key_id_is_not():
    src = _module_source()

    # WITHDRAWN: ospf_auth_key left lo_prof_spec with the fabric-loopback OSPF-auth capability,
    # so there is no declaration left to assert no_log on. It is not a relaxation of the no_log
    # contract -- the plumbing that registers no_log spec params in module.no_log_values stays,
    # and the next binding that carries key material will need it.
    #
    # What replaces the assertion is stronger for today's tree: no spec may declare that key at
    # all, because accepting it and discarding it silently is what the retirement set out to
    # avoid. The explicit rejection lives in dcnm_intf_validate_lo_interface_input.
    assert 'ospf_auth_key=dict(' not in src, (
        "ospf_auth_key reappeared in a spec; it must be rejected by name, not accepted"
    )
    assert "RETIRED_LOOPBACK_OSPF_AUTH_KEYS" in src, (
        "the explicit rejection of the withdrawn keys is gone"
    )
    # A key-id is not a secret. Marking it no_log would make Ansible scrub the bare
    # integer from unrelated output, corrupting logs that merely contain that number.
    assert 'ospf_auth_key_id=dict(' not in src, (
        "ospf_auth_key_id reappeared in a spec; it was withdrawn with the key it accompanies"
    )


# ==========================================================================================
# RUNTIME: key material must never reach the output, measured through the REAL serialiser
# ==========================================================================================
#
# WHY THE REAL SERIALISER AND NOT A MOCK
#
# The first version of this protection was verified against a Mock standing in for the
# AnsibleModule. A Mock's `no_log_values` is an ordinary set, so `add()` always "succeeds" and
# the test passes whether or not the value would actually have been scrubbed -- there is no
# `_return_formatted`, no `remove_values`, no `invocation` block. It passed while three of four
# real cases leaked.
#
# So these build a real AnsibleModule, let the module produce a real result, and read the bytes
# Ansible would actually emit.
#
# WHAT LEAKED, AND WHY
#
# `invocation.module_args` is attached to EVERY result. A value stays out of it only if it was
# registered in `no_log_values` before the result was formatted. The original scrub sat inside
# the loopback rejection loop, which rejects on the first withdrawn key it meets; `ospf_auth_key`
# is the third of three, and the loop also stops at the first offending interface. Every
# arrangement where the key was not the first thing rejected leaked it in the clear.

import json                                                       # noqa: E402
import io                                                         # noqa: E402
import contextlib                                                 # noqa: E402
from unittest.mock import patch                                   # noqa: E402

import pytest                                                     # noqa: E402

from ansible.module_utils import basic                            # noqa: E402
from ansible.module_utils.common.text.converters import to_bytes  # noqa: E402

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface  # noqa: E402

SECRET = "S3CR3T-WP98-NEVER-PRINT-ME"


def _lo(**profile):
    base = {"mode": "fabric", "ipv4_addr": "10.2.0.1"}
    base.update(profile)
    return {"name": "lo0", "type": "lo", "switch": ["10.1.1.1"], "profile": base}


def _eth(**profile):
    base = {"mode": "routed", "ipv4_addr": "10.3.0.1"}
    base.update(profile)
    return {"name": "eth1/5", "type": "eth", "switch": ["10.1.1.1"], "profile": base}


def _emitted_output(config):
    """Everything Ansible would print for this config: the real result, serialised.

    Returns the raw text of whichever of fail_json/exit_json the module reaches, so the
    assertion is made against the bytes the operator would actually see -- result, -vvv,
    `register`, CI log -- and not against an intermediate the test constructed itself.
    """
    basic._ANSIBLE_ARGS = to_bytes(json.dumps({"ANSIBLE_MODULE_ARGS": {
        "state": "merged", "fabric": "test_fabric", "config": config}}))
    module = basic.AnsibleModule(argument_spec=dict(
        state=dict(type="str"), fabric=dict(type="str"),
        config=dict(type="list", elements="dict")))

    # The controller round-trips in __init__ are irrelevant here and unreachable offline.
    # Note they happen AFTER registration, which is the point: even a failure inside __init__
    # is already covered.
    with patch.object(dcnm_interface, "dcnm_version_supported", return_value=(12, "12.6.0.267")), \
            patch.object(dcnm_interface, "get_fabric_inventory_details", return_value={}), \
            patch.object(dcnm_interface, "get_ip_sn_dict", return_value=({}, [])):
        intf = dcnm_interface.DcnmIntf(module)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            intf.dcnm_intf_validate_loopback_interface_input(module.params["config"])
        except SystemExit:
            return buf.getvalue()          # rejected: fail_json already printed
        try:
            module.exit_json(changed=False)   # accepted: force a real result to inspect
        except SystemExit:
            pass
    return buf.getvalue()


# Each case is an arrangement that the rejection-time scrub got wrong. The names say which.
LEAK_CASES = {
    "key_alone_is_the_only_one_the_old_scrub_caught": [_lo(ospf_auth_key=SECRET)],
    "key_id_is_rejected_first_so_the_key_was_never_reached": [
        _lo(ospf_auth_key_id=7, ospf_auth_key=SECRET)],
    "the_boolean_is_rejected_first_so_the_key_was_never_reached": [
        _lo(enable_ospf_auth_message_digest=True, ospf_auth_key=SECRET)],
    "a_second_interface_is_never_reached_at_all": [
        _lo(enable_ospf_auth_message_digest=True), _lo(ospf_auth_key=SECRET)],
    "nor_is_a_third": [
        _lo(ospf_auth_key_id=1), _lo(enable_ospf_auth_message_digest=True),
        _lo(ospf_auth_key=SECRET)],
}


@pytest.mark.parametrize("case", sorted(LEAK_CASES), ids=sorted(LEAK_CASES))
def test_the_key_never_appears_in_the_emitted_result(case):
    output = _emitted_output(LEAK_CASES[case])
    assert SECRET not in output, (
        "key material was serialised in the clear. Registration must cover the WHOLE config on "
        "arrival; it cannot depend on which key some later check happens to reject first."
    )
    assert "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER" in output or "ospf_auth_key" not in output, (
        "the key is absent but so is the placeholder, which suggests the field was dropped "
        "rather than scrubbed -- check this is still measuring what it thinks it is"
    )


def test_the_key_is_scrubbed_even_where_nothing_rejects_it():
    """The forward-compatible half, and the reason this does not belong to the rejection.

    ospf_auth_key is about to be a LEGITIMATE field on int_routed_host, int_subif and int_vlan:
    the global validators that used to refuse it outside a loopback were withdrawn so it could
    be. On those parents no rejection fires, so a scrub owned by a rejection would protect the
    key exactly where it is refused and nowhere it is accepted.
    """
    output = _emitted_output([_eth(ospf_auth_key=SECRET)])
    assert SECRET not in output


def test_an_empty_key_is_not_registered():
    """Registering "" would make Ansible scrub every empty string in every result.

    That is not a smaller version of the protection, it is a different and worse bug: it
    corrupts unrelated output wholesale while protecting nothing, since "" is not key material.
    """
    basic._ANSIBLE_ARGS = to_bytes(json.dumps({"ANSIBLE_MODULE_ARGS": {
        "state": "merged", "fabric": "test_fabric", "config": [_lo(ospf_auth_key="")]}}))
    module = basic.AnsibleModule(argument_spec=dict(
        state=dict(type="str"), fabric=dict(type="str"),
        config=dict(type="list", elements="dict")))
    intf = object.__new__(dcnm_interface.DcnmIntf)
    intf.module = module
    intf.dcnm_intf_register_secret_values(module.params["config"])
    assert "" not in module.no_log_values


@pytest.mark.parametrize("malformed", [
    None, "not a list", [None], ["not a dict"], [{}], [{"profile": None}],
    [{"profile": "not a dict"}], [{"profile": {}}],
])
def test_registration_is_total_and_never_raises(malformed):
    """It runs in __init__, before every validator, so it must survive any shape of input.

    If it raised on a malformed config the operator would get a traceback instead of the
    validator's message -- and a module that crashes before validating is worse than one that
    logs a key.
    """
    basic._ANSIBLE_ARGS = to_bytes(json.dumps({"ANSIBLE_MODULE_ARGS": {
        "state": "merged", "fabric": "test_fabric", "config": []}}))
    module = basic.AnsibleModule(argument_spec=dict(
        state=dict(type="str"), fabric=dict(type="str"),
        config=dict(type="list", elements="dict")))
    intf = object.__new__(dcnm_interface.DcnmIntf)
    intf.module = module
    intf.dcnm_intf_register_secret_values(malformed)   # must simply return


def test_registration_happens_in_init_not_in_a_validator():
    """Placement is the whole fix, so it is pinned.

    Moving this call into a validator, or after dispatch by interface type, reopens every case
    above -- the field would be protected only on the paths that happen to run.
    """
    src = _module_source()
    init = src[src.index("    def __init__(self, module):"):]
    init = init[: init.index("\n    def ", 1)]
    assert "self.dcnm_intf_register_secret_values(self.config)" in init, (
        "secret registration is no longer in __init__"
    )
    assert init.index("self.config = ") < init.index("dcnm_intf_register_secret_values"), (
        "registration must come after self.config is populated"
    )
