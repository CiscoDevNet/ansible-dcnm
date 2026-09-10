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

These are static source contracts. The runtime behaviour (registration in
``no_log_values`` and the raise-without-module contract) is covered by
``test_dcnm_intf_ospf_legacy_key.py``.

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

    assert 'ospf_auth_key=dict(type="str", no_log=True)' in src, (
        "ospf_auth_key carries the OSPF authentication key and must stay no_log"
    )
    # A key-id is not a secret. Marking it no_log would make Ansible scrub the bare
    # integer from unrelated output, corrupting logs that merely contain that number.
    assert 'ospf_auth_key_id=dict(type="int")' in src, (
        "ospf_auth_key_id must NOT be no_log: it is an identifier, not a secret"
    )
