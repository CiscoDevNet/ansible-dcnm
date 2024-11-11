===========================================
Cisco NDFC Ansible Collection Release Notes
===========================================

All notable changes to this project will be documented in this file.

This project adheres to `Semantic Versioning <http://semver.org/>`_.

.. contents:: ``Release Versions``

`3.6.0`_
=====================

**Release Date:** ``2024-11-11``

Added
-----

- The following new modules are included in this release
    - ``dcnm_bootflash`` - Module for bootflash management for Nexus switches
    - ``dcnm_maintenance_mode`` - Module for Maintentance Mode Configuration of Nexus switches

- The following new features are added to existing modules in this release
    - ``dcnm_policy`` - Flag to use the description parameter as the unique key for policy management
    - ``dcnm_fabric`` - Added ISN Fabric Type Support

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/128
- https://github.com/CiscoDevNet/ansible-dcnm/issues/229
- https://github.com/CiscoDevNet/ansible-dcnm/issues/305

`3.5.1`_
=====================

**Release Date:** ``2024-06-13``

Fixed
-----

- Fix for ansible-sanity errors in code and documentation
- Updates to supported ansible version

`3.5.0`_
=====================

**Release Date:** ``2024-05-14``

Added
-----

- The following new modules are included in this release
    - ``dcnm_image_upgrade`` - Module for managing NDFC image upgrade
    - ``dcnm_image_upload`` - Module for managing NDFC image upload
    - ``dcnm_image_policy`` - Module for managing NDFC image policy
    - ``dcnm_vpc_pair`` - Module for managing dcnm NDFC vPC switch pairs
    - ``dcnm_fabric`` - Module for managing NDFC fabrics

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/276
- https://github.com/CiscoDevNet/ansible-dcnm/issues/278
- Fix for inventory issue when non-zero max hop value is set.
- Fix for enhanced error reporting in inventory module.
- Fix for config not required for overridden state.
- Fix for switch role based default ethernet interface policy.

`3.4.3`_
=====================

**Release Date:** ``2023-10-26``

Added
-----

- Support to attach network to TOR switches paired with leaf and its interfaces

`3.4.2`_
=====================

**Release Date:** ``2023-09-11``

Added
-----

- Support for following parameters in ``dcnm_links`` module
    - ``mpls_fabric``
    - ``peer1_sr_mpls_index``
    - ``peer2_sr_mpls_index``
    - ``global_block_range``
    - ``dci_routing_proto``
    - ``ospf_area_id``
    - ``dci_routing_tag``
- Support for ``ext_vxlan_mpls_overlay_setup`` and ``ext_vxlan_mpls_underlay_setup`` templates in ``dcnm_links`` module
- Support for ``secondary_ipv4_addr`` for loopback interfaces in ``dcnm_interface`` module
- Support for fabric and mpls loopback interfaces in ``dcnm_interface`` module
- Support for ``import_evpn_rt`` and ``export_evpn_rt`` in ``dcnm_vrf`` module

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/236
- https://github.com/CiscoDevNet/ansible-dcnm/issues/244
- https://github.com/CiscoDevNet/ansible-dcnm/issues/248
- https://github.com/CiscoDevNet/ansible-dcnm/issues/177

`3.4.1`_
=====================

**Release Date:** ``2023-08-17``
                                              
There is no functional difference between collection version ``3.4.0`` and collection version ``3.4.1``.  This version is only being published as a hotfix to resolve a problem where the wrong
version was inadvertently published to Ansible galaxy.

`3.4.0`_
=====================

**Release Date:** ``2023-08-16``

Added
-----

- Support for save and deploy options in ``dcnm_inventory`` module.
- Support for ``discovery_username`` and ``discovery_password`` in ``dcnm_inventory`` module.
- Support for login domain in connection plugin.

Fixed
-----

- Fix for deploy flag behaviour in inferface module. Config will not be deployed to switches if deploy flag is set to false. When deploy flag is set to true in task and if any of the switch in that task is not manageable or the fabric in task is read-only, then an error is returned without making any changes in the NDFC corresponding to that task.

`3.3.1`_
=====================

**Release Date:** ``2023-07-13``

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/230
- https://github.com/CiscoDevNet/ansible-dcnm/issues/231
- https://github.com/CiscoDevNet/ansible-dcnm/issues/232
- https://github.com/CiscoDevNet/ansible-dcnm/issues/197

`3.3.0`_
=====================

**Release Date:** ``2023-05-23``

Added
-----

- Support to configure multiple interfaces for vrf_lite on a vrf
- Added support for more switch roles in inventory module.

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/204
- https://github.com/CiscoDevNet/ansible-dcnm/issues/205
- https://github.com/CiscoDevNet/ansible-dcnm/issues/206
- Removed the restriction on netcommon version supported by DCNM collection. The restriction was introduced as fix for https://github.com/CiscoDevNet/ansible-dcnm/issues/209. Netcommon versions ``>=2.6.1`` is supported.

`3.2.0`_
=====================

**Release Date:** ``2023-04-20``

Added
-----

- Support for fex interfaces in interface module

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/212

`3.1.1`_
=====================

**Release Date:** ``2023-03-17``

Fixed
-----

- Restrict installs of netcommon to versions ``>=2.6.1,<=4.1.0`` due to issue: https://github.com/CiscoDevNet/ansible-dcnm/issues/209

`3.1.0`_
=====================

**Release Date:** ``2023-03-14``

Added
-----

- Support for all config parameters in network module
- Support for all config parameters in vrf module

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/197
- https://github.com/CiscoDevNet/ansible-dcnm/issues/194
- https://github.com/CiscoDevNet/ansible-dcnm/issues/185

`3.0.0`_
=====================

**Release Date:** ``2023-02-22``

Added
-----

- RMA support in ``dcnm_inventory`` module

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/168
- https://github.com/CiscoDevNet/ansible-dcnm/issues/140
- https://github.com/CiscoDevNet/ansible-dcnm/issues/157
- https://github.com/CiscoDevNet/ansible-dcnm/issues/192

`2.4.0`_
=====================

**Release Date:** ``2022-11-17``

Added
-----

- POAP support in ``dcnm_inventory`` module
- SVI interface support in ``dcnm_interface`` module

Fixed
-----

- Fix for a problem where networks cannot be deleted when detach/undeploy fails and network is in an out of sync state.
- Fix default value for ``multicast_group_address`` property in ``dcnm_network``

`2.3.0`_
=====================

**Release Date:** ``2022-10-28``

Added
-----

- Added the ability to configure the ``multicast_group_address`` to the ``dcnm_network`` module

`2.2.0`_
=====================

**Release Date:** ``2022-10-14``

Added
-----

- The following new modules are included in this release
    - ``dcnm_links`` - Module for managing dcnm links

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/155
- https://github.com/CiscoDevNet/ansible-dcnm/issues/169

`2.1.1`_
=====================

**Release Date:** ``2022-08-18``

Fixed
-----

- Changed the deploy mechanism of policy module for delete state.

`2.1.0`_
=====================

**Release Date:** ``2022-07-19``

Added
-----

- The following new modules are included in this release
    - ``dcnm_resource_manager`` - Module for managing dcnm resources.
      `Reference Info <https://www.cisco.com/c/en/us/td/docs/dcn/ndfc/121x/configuration/fabric-controller/cisco-ndfc-fabric-controller-configuration-guide-121x/lan-fabrics.html#task_fsg_sn4_zqb>`_

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/151
- https://github.com/CiscoDevNet/ansible-dcnm/issues/143
- https://github.com/CiscoDevNet/ansible-dcnm/issues/141
- https://github.com/CiscoDevNet/ansible-dcnm/issues/139
- https://github.com/CiscoDevNet/ansible-dcnm/issues/137
- https://github.com/CiscoDevNet/ansible-dcnm/issues/134
- https://github.com/CiscoDevNet/ansible-dcnm/issues/112
- Fixed Restapi used in version detection mechanism in module utils.
- Fixed Restapi used in various modules to support the latest api's.
- Fixed deploy knob behavior for vrf and network module to align with GUI functionality.
- Fixed idempotence issue in interface module.
- Fixed diff generation issue for network deletion with NDFC.

Deprecated
----------

- Deploy knob for individual attachments in vrf and network modules has been marked for deprecation.

`2.0.1`_
=====================

**Release Date:** ``2022-01-28``

Fixed httpapi plugin issue preventing connections to latest version of NDFC (Version: ``12.0.2f``)

`2.0.0`_
=====================

**Release Date:** ``2021-12-13``

Added
-----

- Nexus Dashboard Fabric Controller (NDFC) support for all collection modules
- The following new modules are included in this release
    - ``dcnm_service_route_peering`` - Module for managing dcnm service route peering
    - ``dcnm_service_policy`` - Module for managing dcnm service policy
    - ``dcnm_service_node`` - Module for managing dcnm service nodes
- New parameter ``check_deploy`` in ``dcnm_interface``
- `Performance improvement of dcnm_inventory module <https://github.com/CiscoDevNet/ansible-dcnm/pull/98>`_.


Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/101
- https://github.com/CiscoDevNet/ansible-dcnm/issues/87
- https://github.com/CiscoDevNet/ansible-dcnm/issues/86
- Fix ``dcnm_policy`` module configuration deploy issues

`1.2.4`_
=====================

**Release Date:** ``2021-12-03``

Added
-----

- Added support for configuring the loopback ID for DHCP Relay interface.
- The feature is configured using the ``dhcp_loopback_id`` parameter in the ``dcnm_network`` module

`1.2.3`_
=====================

**Release Date:** ``2021-11-16``

Fixed
-----

Fixed a problem with ``dcnm_interface`` module where VPCID resource was not being created and then reserved properly

`1.2.2`_
=====================

**Release Date:** ``2021-10-21``

Fixed
-----

Fixed error code handling that was causing an error during authentication

`1.2.1`_
=====================

**Release Date:** ``2021-10``

Added
-----

Added support for plain text payloads to ``dcnm_rest`` module

`1.2.0`_
=====================

**Release Date:** ``2021-07``

Added
-----

The following parameters were added to the ``cisco.dcnm.dcnm_network`` module:

  - New parameter ``is_l2only:``
  - New parameter ``vlan_name:``
  - New parameter ``int_desc:``
  - New parameter ``mtu_l3intf:```
  - New parameter ``arp_suppress:``
  - New parameter ``dhcp_srvr1_ip:``
  - New parameter ``dhcp_srvr1_vrf:``
  - New parameter ``dhcp_srvr2_ip:``
  - New parameter ``dhcp_srvr2_vrf:``
  - New parameter ``dhcp_srvr3_ip:``
  - New parameter ``dhcp_srvr3_vrf:``

`1.1.1`_ 
=====================

**Release Date:** ``2021-05``

Fixed
-----

- https://github.com/CiscoDevNet/ansible-dcnm/issues/66
- https://github.com/CiscoDevNet/ansible-dcnm/issues/65
- https://github.com/CiscoDevNet/ansible-dcnm/issues/63
- https://github.com/CiscoDevNet/ansible-dcnm/issues/62
- https://github.com/CiscoDevNet/ansible-dcnm/issues/60
- https://github.com/CiscoDevNet/ansible-dcnm/issues/57

`1.1.0`_
=====================

**Release Date:** ``2021-04``

Added
-----

- The following new modules are included in this release
    - ``dcnm_policy`` - Module for managing dcnm policies
    - ``dcnm_template`` - Module for managing dcnm templates

- The ``dcnm_vrf`` and ``dcnm_network`` modules have been extended to support multisite fabrics

Fixed
-----

- Bug fixes
- Support for DCNM ``11.5(1)`` release

`1.0.0`_
=====================

**Release Date:** ``2020-09``

Added
-----

- cisco.dcnm.dcnm_network:
  - New parameter ``routing_tag:``

Changed
-------

- cisco.dcnm.dcnm_network:
    - The ``vlan_id:`` parameter must be configured under the ``config:`` block instead of the ``attach:`` block.
    - A warning will be generated informing the user to move the ``vlan_id:`` under the ``config:`` block.
    - If the user does not specify the ``vlan_id`` it will be auto generated by DCNM.
- cisco.dcnm_dcnm_interface:
    - The various ``profile_*:`` parameters have now been modified to just ``profile:``.
    - The playbook with the old ``profile_*:`` names will still be accepted but a warning message will be generated to change the playbook.
    - When specifying switches for a ``vpc`` interface type the switches should be a flat yaml list instead of a nested yaml list.  Both formats will still be accepted.

      Proper Format:

      .. code-block:: yaml
      
          switch:                           # provide switches of vPC pair
            - "{{ ansible_switch1 }}"
            - "{{ ansible_switch2 }}"

      Incorrect Format:

      .. code-block:: yaml

            switch:                           # provide switches of vPC pair
              - ["{{ ansible_switch1 }}",
                 "{{ ansible_switch2 }}"]


Fixed
-----

- cisco.dcnm.dcnm_rest:
  - Module will return a failure now if the return code from DCNM is ``400`` or greater.

0.9.0
=====================

**Release Date:** ``2020-07``

- Initial release of the Ansible DCNM collection, supporting DCNM release 11.4

Added
-----

The Ansible Cisco Data Center Network Manager (DCNM) collection includes modules to help automate common day 2 operations for VXLAN EVPN fabrics.

- cisco.dcnm.dcnm_rest - Send REST API requests to DCNM controller.
- cisco.dcnm.dcnm_inventory - Add and remove Switches from a DCNM managed VXLAN fabric.
- cisco.dcnm.dcnm_vrf - Add and remove VRFs from a DCNM managed VXLAN fabric.
- cisco.dcnm.dcnm_network	 - Add and remove Networks from a DCNM managed VXLAN fabric.
- cisco.dcnm.dcnm_interface - DCNM Ansible Module for managing interfaces.

.. _3.6.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.5.1...3.6.0
.. _3.5.1: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.5.0...3.5.1
.. _3.5.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.4.3...3.5.0
.. _3.4.3: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.4.2...3.4.3
.. _3.4.2: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.4.1...3.4.2
.. _3.4.1: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.4.0...3.4.1
.. _3.4.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.3.1...3.4.0
.. _3.3.1: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.3.0...3.3.1
.. _3.3.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.2.0...3.3.0
.. _3.2.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.1.1...3.2.0
.. _3.1.1: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.1.0...3.1.1
.. _3.1.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/3.0.0...3.1.0
.. _3.0.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.4.0...3.0.0
.. _2.4.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.3.0...2.4.0
.. _2.3.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.2.0...2.3.0
.. _2.2.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.1.1...2.2.0
.. _2.1.1: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.1.0...2.1.1
.. _2.1.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.0.1...2.1.0
.. _2.0.1: https://github.com/CiscoDevNet/ansible-dcnm/compare/2.0.0...2.0.1
.. _2.0.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.2.4...2.0.0
.. _1.2.4: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.2.3...1.2.4
.. _1.2.3: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.2.2...1.2.3
.. _1.2.2: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.2.1...1.2.2
.. _1.2.1: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.2.0...1.2.1
.. _1.2.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.1.1...1.2.0
.. _1.1.1: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.1.0...1.1.1
.. _1.1.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/1.0.0...1.1.0
.. _1.0.0: https://github.com/CiscoDevNet/ansible-dcnm/compare/0.9.0...1.0.0
