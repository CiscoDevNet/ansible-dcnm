"""Load the dcnm_interface unit-test fixtures by their original capture name.

Captures are grouped into bundles under ``dcnm_interface/fixtures``. A JSON bundle has this shape::

    {
      "_bundle": "what the captures have in common",
      "sources": {"<capture>": {"file": "<original file name>", "sha256": "<sha256 of the original file>"}},
      "baselines": {"<capture>.<path>": {...}},
      "cases": {"<capture>": <the capture document>}
    }

A capture that sits alone keeps its own file and is read whole. A text bundle (YAML) keeps each text
verbatim under ``text`` with the sha256 of that text.

Inside ``cases``, a mapping with a ``$baseline`` key stands for a repeated snapshot:

* ``{"$baseline": "<id>"}`` is a fresh copy of ``baselines[<id>]``;
* ``"$set": {...}`` replaces the value of an existing key in place, or appends a new key;
  a null value sets null, it never deletes;
* ``"$unset": [...]`` deletes keys; deleting a key the baseline does not have is an error.

Baselines are one level deep: a baseline never refers to another one. Every call returns a fresh copy,
so a test may change what it receives.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import yaml

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")

# capture name -> (file under FIXTURE_DIR, key in the bundle; None when the file is the capture itself)
SOURCES = {
    "dcnm_intf_binding_configs": ("binding_cases.json", None),
    "dcnm_intf_loopback_ospf_have": ("routing_have_cases.json", "dcnm_intf_loopback_ospf_have"),
    "dcnm_intf_routed_ospf_have": ("routing_have_cases.json", "dcnm_intf_routed_ospf_have"),
    "int_vlan_0efb09af_dhcp_excerpt": ("dhcp_template_excerpts.yaml", "int_vlan_0efb09af_dhcp_excerpt"),
    "int_vlan_4d043f65_dhcp_excerpt": ("dhcp_template_excerpts.yaml", "int_vlan_4d043f65_dhcp_excerpt"),
    "int_vlan_f32ef586_dhcp_excerpt": ("dhcp_template_excerpts.yaml", "int_vlan_f32ef586_dhcp_excerpt"),
    "dcnm_intf_pvlan_measured": ("pvlan_ethernet_cases.json", "dcnm_intf_pvlan_measured"),
    "dcnm_intf_pvlan_device_measured": ("pvlan_ethernet_cases.json", "dcnm_intf_pvlan_device_measured"),
    "dcnm_intf_pvlan_summary_measured": ("pvlan_ethernet_inventory.json", None),
    "nac_pr895_pvlan_args": ("nac_case_models.yaml", "nac_pr895_pvlan_args"),
    "M1_po_host_create": ("nac_case_models.yaml", "M1_po_host_create"),
    "M2_po_host_repeat": ("nac_case_models.yaml", "M2_po_host_repeat"),
    "vars_po_host_e1": ("nac_case_models.yaml", "vars_po_host_e1"),
    "pvlan_admin_up_join_measured": ("pvlan_admin_state.json", None),
    "pvlan_po_duplex_measured": ("pvlan_po_link_settings.json", "pvlan_po_duplex_measured"),
    "pvlan_po_speed_diag_measured": ("pvlan_po_link_settings.json", "pvlan_po_speed_diag_measured"),
    "pvlan_po_speed_s1_measured": ("pvlan_po_link_settings.json", "pvlan_po_speed_s1_measured"),
    "pvlan_po_h1_measured": ("pvlan_po_create_update.json", "pvlan_po_h1_measured"),
    "pvlan_po_g4r1_host_measured": ("pvlan_po_create_update.json", "pvlan_po_g4r1_host_measured"),
    "pvlan_po_t2_measured": ("pvlan_po_delete_saved.json", "pvlan_po_t2_measured"),
    "pvlan_po_ts_exp1_measured": ("pvlan_po_delete_saved.json", "pvlan_po_ts_exp1_measured"),
    "pvlan_po_m1_measured": ("pvlan_po_member_mtu.json", "pvlan_po_m1_measured"),
    "pvlan_po_mr_measured": ("pvlan_po_member_mtu.json", "pvlan_po_mr_measured"),
    "pvlan_release_routed_cdp_measured": ("pvlan_routed_release.json", "pvlan_release_routed_cdp_measured"),
    "pvlan_release_routed_q56_measured": ("pvlan_routed_release.json", "pvlan_release_routed_q56_measured"),
    "pvlan_vpc_duplex_measured": ("pvlan_vpc_link_settings.json", "pvlan_vpc_duplex_measured"),
    "pvlan_vpc_speed_diag_measured": ("pvlan_vpc_link_settings.json", "pvlan_vpc_speed_diag_measured"),
    "pvlan_vpc_l1e4_measured": ("pvlan_vpc_lifecycle.json", None),
}

_FILES = {}


def _read(filename):
    if filename not in _FILES:
        with open(os.path.join(FIXTURE_DIR, filename), encoding="utf-8") as handle:
            text = handle.read()
        data = yaml.safe_load(text) if filename.endswith(".yaml") else json.loads(text)
        for name, base in (data.get("baselines") or {}).items() if isinstance(data, dict) else ():
            if '"$baseline"' in json.dumps(base):
                raise ValueError("baseline %r refers to another baseline; baselines are one level deep" % name)
        _FILES[filename] = data
    return _FILES[filename]


def _expand(node, baselines):
    if isinstance(node, list):
        return [_expand(item, baselines) for item in node]
    if not isinstance(node, dict):
        return node
    if "$baseline" not in node:
        return dict((key, _expand(value, baselines)) for key, value in node.items())
    unknown = set(node) - {"$baseline", "$set", "$unset"}
    if unknown:
        raise ValueError("baseline reference with unexpected keys: %s" % sorted(unknown))
    name = node["$baseline"]
    if name not in baselines:
        raise KeyError("unknown fixture baseline %r" % name)
    out = copy.deepcopy(baselines[name])
    for key, value in node.get("$set", {}).items():
        out[key] = _expand(value, baselines)
    for key in node.get("$unset", []):
        if key not in out:
            raise KeyError("baseline %r has no key %r to unset" % (name, key))
        del out[key]
    return out


def load_case(name):
    """A fresh copy of the capture called `name` (its original file name without the extension)."""
    filename, key = SOURCES[name]
    data = _read(filename)
    if key is None:
        return copy.deepcopy(data)
    case = data["cases"][key]
    if isinstance(case, dict) and set(case) == {"text", "sha256"}:
        raise TypeError("%s is a text capture; use load_text()" % name)
    return _expand(case, data.get("baselines", {}))


def load_text(name):
    """The exact text of the capture called `name`."""
    filename, key = SOURCES[name]
    return _read(filename)["cases"][key]["text"]
