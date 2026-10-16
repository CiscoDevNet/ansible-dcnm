"""WS6 (G6A.3): source-contract for the fabric-loopback OSPF parent/child.

These tests read the SHIPPING template source and the module source and assert
the parent/child selection contract, WITHOUT changing the OSPF architecture. They
exist to correct the overstatement that the parent Boolean alone guarantees the
final child/PTI state, and to lock the Phase-3 invariant: the module manages the
message-digest Boolean and the legacy-key pair (key-ID + key) as parent nvPairs,
while the OSPF keychain field stays fabric-owned and is never a writable
dcnm_interface field.

What is proven here is the STATIC template/module contract only. PTI selection,
the effective NX-OS CLI, OSPF adjacency and keychain behavior are NOT LIVE TESTED
in this offline generation.

Run:
    pytest tests/unit/modules/dcnm/test_dcnm_ospfmd_parent_child_contract.py
"""

import os
import inspect
import re

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

# The shipping templates are reference copies kept next to the investigation.
_TEMPLATE_DIRS = [
    "/Users/dacasti2/NAC_CONTRI/templates",
    os.path.join(os.path.dirname(__file__), "fixtures", "templates"),
]
PARENT = "int_fabric_loopback_11_1.template"
CHILD_MD = "ospf_interface_auth_message_digest_11_1.template"

# The module under test, read as text for the "emits no
# per-interface key/keychain field" invariant.
MODULE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "plugins", "modules", "dcnm_interface.py",
)


def _read_template(name):
    for d in _TEMPLATE_DIRS:
        path = os.path.join(d, name)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                return fh.read()
    pytest.skip("shipping template {0} not available for the source contract".format(name))


@pytest.fixture(scope="module")
def parent_src():
    return _read_template(PARENT)


@pytest.fixture(scope="module")
def child_md_src():
    return _read_template(CHILD_MD)


# --------------------------------------------------------------------------
# 1. the standalone message-digest child supplies ONLY the mode command
# --------------------------------------------------------------------------
def test_child_supplies_the_message_digest_mode_command(child_md_src):
    assert "ip ospf authentication message-digest" in child_md_src
    # It supplies no key material -- it is the mode command only.
    assert "OSPF_AUTH_KEY" not in child_md_src
    assert "key-chain" not in child_md_src.lower()


# --------------------------------------------------------------------------
# 2. the parent creates the standalone child on true and deletes it on false
# --------------------------------------------------------------------------
def test_parent_creates_child_on_true_and_deletes_on_false(parent_src):
    # createOrUpdate(..., "ospf_interface_auth_message_digest_11_1", ...) under
    # the true branch; delete(...) under the else branch.
    assert re.search(
        r'enableOspfAuthMessageDigest\s*==\s*"true"', parent_src
    ), "parent does not gate the message-digest child on the Boolean"
    assert re.search(
        r'createOrUpdate\([^)]*"ospf_interface_auth_message_digest_11_1"',
        parent_src,
        re.DOTALL,
    )
    assert re.search(
        r'PTIWrapper\.delete\([^)]*"ospf_interface_auth_message_digest_11_1"',
        parent_src,
        re.DOTALL,
    )


# --------------------------------------------------------------------------
# 3. the existing legacy-key path supplies key configuration
# --------------------------------------------------------------------------
def test_legacy_key_path_supplies_key_configuration(parent_src):
    # The legacy branch creates ospf_interface_auth with the key id and key.
    assert re.search(
        r'createOrUpdate\([^)]*"ospf_interface_auth"[^)]*OSPF_AUTH_KEY_ID[^)]*OSPF_AUTH_KEY',
        parent_src,
        re.DOTALL,
    ), "parent legacy branch does not carry OSPF_AUTH_KEY_ID/OSPF_AUTH_KEY"


# --------------------------------------------------------------------------
# 4. the keychain branch supersedes the standalone/legacy children
# --------------------------------------------------------------------------
def test_keychain_branch_supersedes_standalone_and_legacy(parent_src):
    # When a keychain is configured, the parent creates the keychain child and
    # DELETES both the legacy key child and the standalone message-digest child --
    # so the Boolean being true does NOT guarantee the message-digest child
    # survives.
    assert re.search(
        r'createOrUpdate\([^)]*"ospf_interface_auth_keychain"', parent_src, re.DOTALL
    )
    keychain_region = parent_src[parent_src.index("ospf_interface_auth_keychain"):]
    assert '"ospf_interface_auth"' in keychain_region
    assert '"ospf_interface_auth_message_digest_11_1"' in keychain_region


# --------------------------------------------------------------------------
# 5. Phase-3 contract: message-digest + legacy-key managed; keychain excluded
# --------------------------------------------------------------------------
def test_the_module_manages_none_of_it_and_the_fabric_owns_all_of_it():
    """INVERTED. It used to assert the module managed the legacy-key pair.

    That was true and is no longer: the capability was withdrawn because the template shows the
    fabric owning the whole feature. The tests above read that from the shipping source -- the
    block is gated on the fabric's link-state protocol, the enable flag and the key defaults come
    from fabricSettings, and a keychain fabric setting deletes the message-digest child outright.
    A per-loopback override on top of that has no use case.

    So the contract now is the simple one: dcnm_interface declares none of the three as a
    writable field, and rejects them by name if a playbook still carries them.
    """
    src = inspect.getsource(dcnm_interface)
    for field in ("enable_ospf_auth_message_digest", "ospf_auth_key_id", "ospf_auth_key"):
        assert "{0}=dict(".format(field) not in src, (
            "{0} is still a writable field; it was withdrawn".format(field)
        )
    assert "RETIRED_LOOPBACK_OSPF_AUTH_KEYS" in src, (
        "the withdrawn keys must be rejected by name, not silently ignored"
    )
    # The keychain was never writable here and still is not -- that invariant predates the
    # retirement and survives it unchanged.
    for keychain in ("ospf_auth_keychain_name", "ospfAuthKeychainName"):
        assert "{0}=dict(".format(keychain) not in src
