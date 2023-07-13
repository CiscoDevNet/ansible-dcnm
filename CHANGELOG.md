# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [3.3.1] - 2023-07-13

### Fixed

* https://github.com/CiscoDevNet/ansible-dcnm/issues/230
* https://github.com/CiscoDevNet/ansible-dcnm/issues/231
* https://github.com/CiscoDevNet/ansible-dcnm/issues/232
* https://github.com/CiscoDevNet/ansible-dcnm/issues/197

## [3.3.0] - 2023-05-23

### Added

* Support to configure muliple interfaces for vrf_lite on a vrf
* Added support for more switch roles in inventory module.

### Fixed

* https://github.com/CiscoDevNet/ansible-dcnm/issues/204
* https://github.com/CiscoDevNet/ansible-dcnm/issues/205
* https://github.com/CiscoDevNet/ansible-dcnm/issues/206
* Removed the restriction on netcommon version supported by DCNM collection. The restriction was introduced as fix for https://github.com/CiscoDevNet/ansible-dcnm/issues/209. Netcommon versions `>=2.6.1` is supported.

## [3.2.0] - 2023-04-20

### Added

* Support for fex interfaces in interface module

### Fixed

* https://github.com/CiscoDevNet/ansible-dcnm/issues/212

## [3.1.1] - 2023-03-17

### Fixed

* Restrict installs of netcommon to versions `>=2.6.1,<=4.1.0` due to issue: https://github.com/CiscoDevNet/ansible-dcnm/issues/209

## [3.1.0] - 2023-03-14

### Added

* Support for all config parameters in network module
* Support for all config parameters in vrf module

### Fixed

* https://github.com/CiscoDevNet/ansible-dcnm/issues/197
* https://github.com/CiscoDevNet/ansible-dcnm/issues/194
* https://github.com/CiscoDevNet/ansible-dcnm/issues/185

## [3.0.0] - 2023-02-22

### Added

* RMA support in `dcnm_inventory` module

### Fixed

* https://github.com/CiscoDevNet/ansible-dcnm/issues/168
* https://github.com/CiscoDevNet/ansible-dcnm/issues/140
* https://github.com/CiscoDevNet/ansible-dcnm/issues/157
* https://github.com/CiscoDevNet/ansible-dcnm/issues/192

## [2.4.0] - 2022-11-17

### Added

* POAP support in `dcnm_inventory` module
* SVI interface support in `dcnm_interface` module

### Fixed

* Fix for a problem where networks cannot be deleted when detach/undeploy fails and network is in an out of sync state.
* Fix default value for `multicast_group_address` property in `dcnm_network`

## [2.3.0] - 2022-10-28

### Added

* Added the ability to configure the `multicast_group_address` to the `dcnm_network` module

## [2.2.0] - 2022-10-14

### Added

* The following new modules are included in this release
    * `dcnm_links` - Module for managing dcnm links

### Fixed

* https://github.com/CiscoDevNet/ansible-dcnm/issues/155
* https://github.com/CiscoDevNet/ansible-dcnm/issues/169

## [2.1.1] - 2022-08-18

### Fixed

* Changed the deploy mechanism of policy module for delete state.

## [2.1.0] - 2022-07-19

### Added

* The following new modules are included in this release
    * `dcnm_resource_manager` - Module for managing dcnm resources.
      [Reference Info](https://www.cisco.com/c/en/us/td/docs/dcn/ndfc/121x/configuration/fabric-controller/cisco-ndfc-fabric-controller-configuration-guide-121x/lan-fabrics.html#task_fsg_sn4_zqb)

### Fixed

* https://github.com/CiscoDevNet/ansible-dcnm/issues/151
* https://github.com/CiscoDevNet/ansible-dcnm/issues/143
* https://github.com/CiscoDevNet/ansible-dcnm/issues/141
* https://github.com/CiscoDevNet/ansible-dcnm/issues/139
* https://github.com/CiscoDevNet/ansible-dcnm/issues/137
* https://github.com/CiscoDevNet/ansible-dcnm/issues/134
* https://github.com/CiscoDevNet/ansible-dcnm/issues/112
* Fixed Restapi used in version detection mechanism in module utils.
* Fixed Restapi used in various modules to support the latest api's.
* Fixed deploy knob behavior for vrf and network module to align with GUI functionality.
* Fixed idempotence issue in interface module.
* Fixed diff generation issue for network deletion with NDFC.

### Deprecated

* Deploy knob for individual attachments in vrf and network modules has been marked for deprecation.

## [2.0.1] - 2022-01-28

Fixed httpapi plugin issue preventing connections to latest version of NDFC (Version: `12.0.2f`)

## [2.0.0] - 2021-12-13

### Added

* Nexus Dashboard Fabric Controller (NDFC) support for all collection modules
* The following new modules are included in this release
    * `dcnm_service_route_peering` - Module for managing dcnm service route peering
    * `dcnm_service_policy` - Module for managing dcnm service policy
    * `dcnm_service_node` - Module for managing dcnm service nodes
* New parameter `check_deploy` in `dcnm_interface`
* [Performance improvement of `dcnm_inventory` module](https://github.com/CiscoDevNet/ansible-dcnm/pull/98)

### Fixed

* https://github.com/CiscoDevNet/ansible-dcnm/issues/101
* https://github.com/CiscoDevNet/ansible-dcnm/issues/87
* https://github.com/CiscoDevNet/ansible-dcnm/issues/86
* Fix `dcnm_policy` module configuration deploy issues

## [1.2.4] - 2021-12-03

### Added

* Added support for configuring the loopback ID for DHCP Relay interface.
* The feature is configured using the `dhcp_loopback_id` parameter in the `dcnm_network` module

## [1.2.3] - 2021-11-16

### Fixed

Fixed a problem with `dcnm_interface` module where VPCID resource was not being created and then reserved properly

## [1.2.2] - 2021-10-21

### Fixed

Fixed error code handling that was causing an error during authentication

## [1.2.1] - 2021-10

### Added

Added support for plain text payloads to `dcnm_rest` module

## [1.2.0] - 2021-07

### Added

* cisco.dcnm.dcnm_network:
  * New parameter `is_l2only:`
  * New parameter `vlan_name:`
  * New parameter `int_desc:`
  * New parameter `mtu_l3intf:`
  * New parameter `arp_suppress:`
  * New parameter `dhcp_srvr1_ip:`
  * New parameter `dhcp_srvr1_vrf:`
  * New parameter `dhcp_srvr2_ip:`
  * New parameter `dhcp_srvr2_vrf:`
  * New parameter `dhcp_srvr3_ip:`
  * New parameter `dhcp_srvr3_vrf:`

## [1.1.1] - 2021-05

### Fixed

* https://github.com/CiscoDevNet/ansible-dcnm/issues/66
* https://github.com/CiscoDevNet/ansible-dcnm/issues/65
* https://github.com/CiscoDevNet/ansible-dcnm/issues/63
* https://github.com/CiscoDevNet/ansible-dcnm/issues/62
* https://github.com/CiscoDevNet/ansible-dcnm/issues/60
* https://github.com/CiscoDevNet/ansible-dcnm/issues/57

## [1.1.0] - 2021-04

### Added

* The following new modules are included in this release
    * `dcnm_policy` - Module for managing dcnm policies
    * `dcnm_template` - Module for managing dcnm templates

* The `dcnm_vrf` and `dcnm_network` modules have been extended to support multisite fabrics

### Fixed

* Bug fixes
* Support for DCNM `11.5(1)` release

## [1.0.0] - 2020-09

### Added

* cisco.dcnm.dcnm_network:
  * New parameter `routing_tag:`

### Changed

* cisco.dcnm.dcnm_network:
  * The `vlan_id:` parameter must be configured under the `config:` block instead of the `attach:` block.
    * A warning will be generated informing the user to move the `vlan_id:` under the `config:` block.
    * If the user does not specify the `vlan_id` it will be auto generated by DCNM.
* cisco.dcnm_dcnm_interface:
  * The various `profile_*:` parameters have now been modified to just `profile:`.
    * The playbook with the old `profile_*:` names will still be accepted but a warning message will be generated to change the playbook.
    * When specifying switches for a `vpc` interface type the switches should be a flat yaml list instead of a nested yaml list.  Both formats will still be accepted.

      Proper Format:
      ```
            switch:                           # provide switches of vPC pair
              - "{{ ansible_switch1 }}"
              - "{{ ansible_switch2 }}"
      ```
      Incorrect Format:
      ```
            switch:                           # provide switches of vPC pair
              - ["{{ ansible_switch1 }}",
                 "{{ ansible_switch2 }}"]
      ```

### Fixed

* cisco.dcnm.dcnm_rest:
  * Module will return a failure now if the return code from DCNM is `400` or greater.

## 0.9.0 - 2020-07

- Initial release of the Ansible DCNM collection, supporting DCNM release 11.4

### Added

The Ansible Cisco Data Center Network Manager (DCNM) collection includes modules to help automate common day 2 operations for VXLAN EVPN fabrics.

* cisco.dcnm.dcnm_rest - Send REST API requests to DCNM controller.
* cisco.dcnm.dcnm_inventory - Add and remove Switches from a DCNM managed VXLAN fabric.
* cisco.dcnm.dcnm_vrf - Add and remove VRFs from a DCNM managed VXLAN fabric.
* cisco.dcnm.dcnm_network	 - Add and remove Networks from a DCNM managed VXLAN fabric.
* cisco.dcnm.dcnm_interface - DCNM Ansible Module for managing interfaces.

[3.3.1]: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.3.0...3.3.1
[3.3.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.2.0...3.3.0
[3.2.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.1.1...3.2.0
[3.1.1]: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.1.0...3.1.1
[3.1.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.0.0...3.1.0
[3.0.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.4.0...3.0.0
[2.4.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.3.0...2.4.0
[2.3.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.2.0...2.3.0
[2.2.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.1.1...2.2.0
[2.1.1]: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.1.0...2.1.1
[2.1.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.0.1...2.1.0
[2.0.1]: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.0.0...2.0.1
[2.0.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.2.4...2.0.0
[1.2.4]: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.2.3...1.2.4
[1.2.3]: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.2.2...1.2.3
[1.2.2]: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.2.1...1.2.2
[1.2.1]: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.2.0...1.2.1
[1.2.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.1.1...1.2.0
[1.1.1]: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.1.0...1.1.1
[1.1.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/0.9.0...1.0.0
