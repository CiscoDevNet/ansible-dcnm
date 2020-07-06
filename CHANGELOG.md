# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## 0.9.0 - 2020-07

- Initial release of the Ansible DCNM collection, supporting DCNM release 11.4

### Added

The Ansible Cisco Data Center Network Manager (DCNM) collection includes modules to help automate common day 2 operations for VXLAN EVPN fabrics.

* cisco.dcnm.dcnm_rest - Send REST API requests to DCNM controller.
* cisco.dcnm.dcnm_inventory - Add and remove Switches from a DCNM managed VXLAN fabric.
* cisco.dcnm.dcnm_vrf - Add and remove VRFs from a DCNM managed VXLAN fabric.
* cisco.dcnm.dcnm_network	 - Add and remove Networks from a DCNM managed VXLAN fabric.
* cisco.dcnm.dcnm_interface - DCNM Ansible Module for managing interfaces.

