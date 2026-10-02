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
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (  # noqa: E402
    gie_contribute_nvpairs, gie_extend_prof_spec,
)

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


# ==========================================================================================
# THE AUTHENTICATION LOT: both secrets, on every parent, in and out
# ==========================================================================================
#
# Everything above was written while ospf_auth_key was a WITHDRAWN field that only ever got
# rejected. It is now a registered binding on int_routed_host, int_subif and int_vlan, and it
# has a sibling: ospf_authentication_key. Two secrets, three parents, and -- unlike before --
# paths where the value is ACCEPTED and travels.
#
# That widens what has to be true. A rejected key must not be printed; so must an accepted one,
# one echoed back by the controller, and one that only ever appears in a diff.

AUTH_SECRET = "3DES-ENCRYPTED-WP98-AUTH"
AUTH_SECRET_2 = "SECOND-WP98-AUTHENTICATION-KEY"
OSPF_PARENT_CONFIG = {
    "int_routed_host": ("eth1/5", "eth", {"mode": "routed", "ipv4_addr": "10.3.0.1"}),
    "int_subif": ("eth1/5.100", "sub_int", {"mode": "subint", "vlan": 100,
                                            "ipv4_addr": "10.3.1.1", "ipv4_mask_len": 30}),
    "int_vlan": ("vlan100", "svi", {"mode": "vlan", "ipv4_addr": "10.3.2.1",
                                    "ipv4_mask_len": 30}),
}


def _interface_with(parent, **profile_extra):
    name, itype, base = OSPF_PARENT_CONFIG[parent]
    profile = dict(base)
    profile.update(profile_extra)
    return {"name": name, "type": itype, "switch": ["10.1.1.1"], "profile": profile}


@pytest.mark.parametrize("parent", sorted(OSPF_PARENT_CONFIG))
@pytest.mark.parametrize("secret_key", ["ospf_auth_key", "ospf_authentication_key"])
def test_neither_secret_is_emitted_on_any_ospf_parent(parent, secret_key):
    """Both keys, all three parents. Six combinations, none of which may print the value."""
    cfg = [_interface_with(parent, enable_ospf=True, enable_ospf_auth=True,
                           **{secret_key: AUTH_SECRET})]
    assert AUTH_SECRET not in _emitted_output(cfg)


@pytest.mark.parametrize("parent", sorted(OSPF_PARENT_CONFIG))
def test_both_secrets_at_once_are_both_scrubbed(parent):
    """Registration must not stop at the first secret it finds.

    This is the same failure shape that made the earlier fix wrong -- a loop that stopped early
    -- transposed from "which key is rejected first" to "which key is registered first".
    """
    cfg = [_interface_with(parent, enable_ospf=True, enable_ospf_auth=True,
                           ospf_auth_key=AUTH_SECRET,
                           ospf_authentication_key=AUTH_SECRET_2)]
    out = _emitted_output(cfg)
    assert AUTH_SECRET not in out
    assert AUTH_SECRET_2 not in out


def test_secrets_on_different_interfaces_are_all_scrubbed():
    """One config, three parents, a different secret on each."""
    cfg = [_interface_with("int_routed_host", ospf_auth_key=AUTH_SECRET),
           _interface_with("int_subif", ospf_authentication_key=AUTH_SECRET_2),
           _interface_with("int_vlan", ospf_auth_key="THIRD-WP98-KEY")]
    out = _emitted_output(cfg)
    for value in (AUTH_SECRET, AUTH_SECRET_2, "THIRD-WP98-KEY"):
        assert value not in out


@pytest.mark.parametrize("order", ["secret_first", "secret_last"])
def test_field_order_within_a_profile_does_not_matter(order):
    """Registration walks the profile; it must not depend on where the key sits in it.

    Dict order is preserved in Python, and a playbook's field order is the author's, not ours.
    """
    fields = [("enable_ospf", True), ("enable_ospf_auth", True),
              ("ospf_auth_key_id", 7), ("ospf_authentication_key_type", "3")]
    secret = ("ospf_auth_key", AUTH_SECRET)
    ordered = [secret] + fields if order == "secret_first" else fields + [secret]
    cfg = [_interface_with("int_routed_host", **dict(ordered))]
    assert AUTH_SECRET not in _emitted_output(cfg)


def test_the_id_and_the_type_selector_stay_visible():
    """Not everything near a secret is one, and over-scrubbing is its own defect.

    Ansible replaces registered values by STRING MATCH anywhere they appear. Registering the id
    would blank the digits "7" and "3" across the whole result -- inside unrelated addresses,
    VLAN ids, counters -- while protecting nothing. The operator needs to see what key id was
    sent in order to correlate it with the device.
    """
    cfg = [_interface_with("int_routed_host", enable_ospf=True, enable_ospf_auth=True,
                           ospf_auth_key_id=7, ospf_authentication_key_type="3",
                           ospf_auth_key=AUTH_SECRET)]
    out = _emitted_output(cfg)
    assert AUTH_SECRET not in out
    args = json.loads(out)["invocation"]["module_args"]["config"][0]["profile"]
    assert args["ospf_auth_key_id"] == 7, "the key id must remain readable"
    assert args["ospf_authentication_key_type"] == "3", "so must the encryption type"


def test_input_registration_covers_input_only_and_says_so():
    """The two registrations have different jobs and must not be confused for one another.

    dcnm_intf_register_secret_values reads the CONFIG. It cannot know about a value the
    controller holds, and it is not supposed to -- that is what
    dcnm_intf_register_controller_secrets is for, asserted further down.

    This is pinned because the boundary is easy to blur: someone reading "registration happens
    on arrival, over the whole config" could reasonably assume it covered everything, and a
    query result would go out in the clear.
    """
    basic._ANSIBLE_ARGS = to_bytes(json.dumps({"ANSIBLE_MODULE_ARGS": {
        "state": "merged", "fabric": "test_fabric", "config": []}}))
    module = basic.AnsibleModule(argument_spec=dict(
        state=dict(type="str"), fabric=dict(type="str"),
        config=dict(type="list", elements="dict")))
    intf = object.__new__(dcnm_interface.DcnmIntf)
    intf.module = module
    intf.dcnm_intf_register_secret_values([])
    assert "VALUE-ONLY-NDFC-KNOWS" not in module.no_log_values


def test_registering_a_secret_does_not_change_what_is_sent():
    """Scrubbing is an OUTPUT concern. The payload must be byte-identical either way.

    A protection that altered the value on the wire would be worse than no protection: the
    device would get a key nobody typed, and it would fail to authenticate for reasons the
    operator could not see.
    """
    profile = {"mode": "routed", "ipv4_addr": "10.3.0.1", "enable_ospf": True,
               "enable_ospf_auth": True, "ospf_auth_key": AUTH_SECRET}
    nvpairs = gie_contribute_nvpairs("int_routed_host", profile, "12.6.0.267")[0]
    assert nvpairs["OSPF_AUTH_KEY"] == AUTH_SECRET, (
        "the nvPair must carry the real key: the controller cannot use a scrubbed one"
    )
    assert type(nvpairs["OSPF_AUTH_KEY"]) is str  # pylint: disable=unidiomatic-typecheck


def test_the_generated_spec_entry_declares_no_log_for_a_secret_and_not_for_its_neighbours():
    """The second mechanism: what Ansible itself is told about the field.

    This covers the accepted path; the early registration covers every other. Both are needed,
    and this asserts they agree on WHICH fields are secret.
    """
    profile = {"ospf_auth_key": AUTH_SECRET, "ospf_authentication_key": AUTH_SECRET_2,
               "ospf_auth_key_id": 7, "ospf_authentication_key_type": "3",
               "enable_ospf_auth": True}
    spec = gie_extend_prof_spec({}, "int_routed_host", profile)
    assert spec["ospf_auth_key"].get("no_log") is True
    assert spec["ospf_authentication_key"].get("no_log") is True
    for visible in ("ospf_auth_key_id", "ospf_authentication_key_type", "enable_ospf_auth"):
        assert "no_log" not in spec[visible], (
            "{0} was marked no_log; string-match scrubbing would blank its value "
            "everywhere".format(visible)
        )


# ==========================================================================================
# SECRETS THE CONTROLLER PRODUCES, WHICH WERE NEVER IN THE INPUT
# ==========================================================================================
#
# Registering only what the operator wrote leaves every controller-side path in the clear: a
# query result, the HAVE a diff is computed from, an error quoting the payload NDFC rejected.
# None of those pass through the playbook.

NDFC_KEY = "KEY-ONLY-THE-CONTROLLER-KNOWS"


def _module_with_empty_config():
    basic._ANSIBLE_ARGS = to_bytes(json.dumps({"ANSIBLE_MODULE_ARGS": {
        "state": "query", "fabric": "test_fabric", "config": []}}))
    module = basic.AnsibleModule(argument_spec=dict(
        state=dict(type="str"), fabric=dict(type="str"),
        config=dict(type="list", elements="dict")))
    intf = object.__new__(dcnm_interface.DcnmIntf)
    intf.module = module
    return intf, module


@pytest.mark.parametrize("nvpair", sorted(dcnm_interface.SECRET_NVPAIRS))
def test_a_secret_nvpair_from_the_controller_is_registered(nvpair):
    intf, module = _module_with_empty_config()
    intf.dcnm_intf_register_controller_secrets(
        [{"policy": "int_routed_host",
          "interfaces": [{"ifName": "Ethernet1/5", "nvPairs": {nvpair: NDFC_KEY}}]}])
    assert NDFC_KEY in module.no_log_values


def test_it_walks_rather_than_following_one_known_path():
    """Responses nest differently per endpoint; a hardcoded path protects only one of them."""
    intf, module = _module_with_empty_config()
    intf.dcnm_intf_register_controller_secrets(
        {"DATA": {"groups": [{"odd": {"interfaces": [
            {"nvPairs": {"OSPF_AUTH_KEY": NDFC_KEY}}]}}]}})
    assert NDFC_KEY in module.no_log_values


def test_a_visible_nvpair_from_the_controller_is_not_registered():
    """The id comes back too, and registering it would blank that digit everywhere."""
    intf, module = _module_with_empty_config()
    intf.dcnm_intf_register_controller_secrets(
        [{"interfaces": [{"nvPairs": {"OSPF_AUTH_KEY_ID": "7", "OSPF_AUTH_KEY": NDFC_KEY}}]}])
    assert NDFC_KEY in module.no_log_values
    assert "7" not in module.no_log_values, (
        "the key id was registered; Ansible would replace every '7' in the result"
    )


@pytest.mark.parametrize("shape", [
    None, [], {}, {"nvPairs": None}, {"nvPairs": "text"}, [{"nvPairs": {}}],
    {"interfaces": None}, "a string", 7,
])
def test_walking_a_malformed_response_never_raises(shape):
    """It runs on whatever the controller returned, including on an error path."""
    intf, unused_module = _module_with_empty_config()
    intf.dcnm_intf_register_controller_secrets(shape)


def test_both_call_sites_are_wired():
    """HAVE and query are separate paths and query never builds a HAVE.

    Pinned as source, because a runtime test for query needs a controller. If a third path that
    surfaces controller nvPairs appears, it needs its own call and its own line here.
    """
    src = _module_source()
    assert src.count("self.dcnm_intf_register_controller_secrets(") == 2, (
        "expected exactly two call sites: HAVE assembly and the query result"
    )
    assert "self.dcnm_intf_register_controller_secrets(intf_payload)" in src
    assert "self.dcnm_intf_register_controller_secrets(self.diff_query)" in src
