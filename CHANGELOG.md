# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

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

[1.0.0]: https://github.com/CiscoDevNet/ansible-dcnm/compare/0.9.0...1.0.0
