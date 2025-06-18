# Topology - replaced state

The topology (fabrics and switches) is not created by the test and must be
created through other means (NDFC GUI, separate Ansible scripts, etc)

[Topology Diagram](replaced.mermaid)

## ISN

- Fabric type is `Multi-Site External Network`
- The fabric is not referenced in the test, but needs to exist

### switch_4

- switch_4 role (NDFC GUI) is `Edge Router`
- switch_4 is not referenced in the test, but needs to exist

## fabric_1

- Fabric type (NDFC GUI) is `Data Center VXLAN EVPN`
- Fabric type (NDFC Template) is `Easy_Fabric`
- Fabric type (dcnm_fabric Playbook) is `VXLAN_EVPN`

### switch_1

- switch_1 role (NDFC GUI) is `Border Spine`
- switch_1 does not require an interface

### switch_2

- switch_2 role (NDFC GUI) is `Border Spine`
- interface_2a is connected to switch_4 and must be up

```mermaid
architecture-beta
    group isn(cloud)[ISN]
      group switch_4g[switch_4 edge_router] in isn
        service interface_4a(internet)[interface_4a] in switch_4g

    group fabric_1(cloud)[fabric_1]
      group switch_1g[switch_1 border_spine] in fabric_1
      group switch_2g[switch_2 border_spine] in fabric_1
        service interface_2a(server)[interface_2a] in switch_2g

    interface_4a:T -- B:interface_2a
```
