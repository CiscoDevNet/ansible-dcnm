"""The readback checker for typed list fields (vlan_mapping_entries, dhcp_servers), through the real ActionModule.run()."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from .test_dcnm_interface_validator import r2_back, r2_cfg, r2_run

VM_PARENTS = ("int_trunk_host", "int_port_channel_trunk_host", "int_vpc_trunk_host")
ROWS = [{"customer_vlan": "10-20", "dot1q_tunnel": True, "provider_vlan": 300},
        {"customer_vlan": 40, "dot1q_tunnel": True, "provider_vlan": 301}]
ROW_A = '{"customerVlan":"10-20","dot1qTunnel":"true","customerInnerVlan":"","providerVlan":"300"}'
ROW_B = '{"customerVlan":"40","dot1qTunnel":"true","customerInnerVlan":"","providerVlan":"301"}'


@pytest.mark.parametrize("parent", VM_PARENTS)
@pytest.mark.parametrize("back", [
    '{"vlanMappingEntries":[%s,%s]}' % (ROW_A, ROW_B),
    '{"vlanMappingEntries":[%s,%s]}' % (ROW_B, ROW_A),                    # any order
    str({"vlanMappingEntries": [{"customerVlan": "40", "dot1qTunnel": "true", "customerInnerVlan": "",
                                 "providerVlan": "301"},
                                {"customerVlan": "10-20", "dot1qTunnel": "true", "customerInnerVlan": "",
                                 "providerVlan": "300"}]}),               # Python literal, as the vPC child reads it
], ids=["stored", "reordered", "literal"])
def test_the_same_rows_pass(tmp_path, parent, back):
    cfg = [r2_cfg(parent, enable_vlan_mapping=True, vlan_mapping_entries=ROWS)]
    res = r2_run(tmp_path, cfg, r2_back(parent, {"enableVlanMapping": "true", "vlanMappingEntries": back}))
    assert res["failed"] is False, res["msg"]


@pytest.mark.parametrize("parent", VM_PARENTS)
@pytest.mark.parametrize("back", [
    '{"vlanMappingEntries":[%s]}' % ROW_A,                                   # a row missing
    '{"vlanMappingEntries":[%s,%s,%s]}' % (ROW_A, ROW_B, ROW_B),             # a row repeated
    '{"vlanMappingEntries":[%s,%s]}' % (ROW_A, ROW_B.replace('"true"', '"false"')),
    '{"vlanMappingEntries":[%s,%s]}' % (ROW_A, ROW_B.replace('"301"', '301')),  # a native integer
    '{"vlanMappingEntries":[%s]}' % ROW_A.replace(',"customerInnerVlan":""', ""),
    "",
], ids=["missing-row", "repeated-row", "tunnel-off", "native-int", "missing-key", "empty"])
def test_different_rows_fail(tmp_path, parent, back):
    cfg = [r2_cfg(parent, vlan_mapping_entries=ROWS)]
    assert r2_run(tmp_path, cfg, r2_back(parent, {"vlanMappingEntries": back}))["failed"] is True


@pytest.mark.parametrize("parent", VM_PARENTS)
def test_an_empty_request_expects_the_empty_value(tmp_path, parent):
    cfg = [r2_cfg(parent, enable_vlan_mapping=False, vlan_mapping_entries=[])]
    back = {"enableVlanMapping": "false", "vlanMappingEntries": ""}
    assert r2_run(tmp_path, cfg, r2_back(parent, back))["failed"] is False
    back["vlanMappingEntries"] = '{"vlanMappingEntries":[%s]}' % ROW_A
    assert r2_run(tmp_path, cfg, r2_back(parent, back))["failed"] is True


def test_an_unreadable_requested_row_is_diagnosed(tmp_path):
    cfg = [r2_cfg("int_trunk_host", vlan_mapping_entries=[{"provider_vlan": 300}])]
    res = r2_run(tmp_path, cfg, r2_back("int_trunk_host", {"vlanMappingEntries": ""}))
    assert res["failed"] is True and "a list row is not readable" in res["msg"]


DR_PARENTS = ("int_routed_host", "int_l3_port_channel", "int_subif")
SERVERS = [{"srvr_ip": "192.0.2.10"}, {"srvr_ip": "2001:db8::10", "srvr_vrf": "Mgmt-1"}]
SRV_A = '{"srvrAddr":"192.0.2.10","srvrVrf":""}'
SRV_B = '{"srvrAddr":"2001:db8::10","srvrVrf":"Mgmt-1"}'


@pytest.mark.parametrize("parent", DR_PARENTS)
@pytest.mark.parametrize("back", [
    '{"dhcpServers":[%s,%s]}' % (SRV_A, SRV_B),
    '{"dhcpServers":[%s,%s]}' % (SRV_B, SRV_A),
    str({"dhcpServers": [{"srvrAddr": "2001:db8::10", "srvrVrf": "Mgmt-1"}, {"srvrAddr": "192.0.2.10", "srvrVrf": ""}]}),
], ids=["stored", "reordered", "literal"])
def test_the_same_servers_pass(tmp_path, parent, back):
    cfg = [r2_cfg(parent, dhcp_servers=SERVERS)]
    res = r2_run(tmp_path, cfg, r2_back(parent, {"dhcpServers": back}))
    assert res["failed"] is False, res["msg"]


@pytest.mark.parametrize("parent", DR_PARENTS)
@pytest.mark.parametrize("back", [
    '{"dhcpServers":[%s]}' % SRV_A,
    '{"dhcpServers":[%s,%s]}' % (SRV_A, SRV_B.replace("Mgmt-1", "mgmt-1")),   # the VRF case is part of the value
    '[%s,%s]' % (SRV_A, SRV_B),                                              # a bare list
    "",
], ids=["missing-row", "vrf-case", "bare-list", "empty"])
def test_different_servers_fail(tmp_path, parent, back):
    cfg = [r2_cfg(parent, dhcp_servers=SERVERS)]
    assert r2_run(tmp_path, cfg, r2_back(parent, {"dhcpServers": back}))["failed"] is True
