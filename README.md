[![Actions Status](https://github.com/CiscoDevNet/ansible-dcnm/workflows/CI/badge.svg)](https://github.com/CiscoDevNet/ansible-dcnm/actions?branch=develop)


# Cisco DCNM Collection

The Ansible Cisco Nexus® Dashboard Fabric Controller (NDFC) (formerly Cisco Data Center Network Manager (DCNM)) collection includes modules to help automate common day 2 operations for VXLAN EVPN fabrics.

This collection is intended for use with the following release versions:
  * `DCNM Release 11.4(1)` or later
  * `NDFC Release 12.0` or later.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.15.0**.

For collections that support Ansible 2.9, please ensure you update your `network_os` to use the
fully qualified collection name (for example, `cisco.ios.ios`).
Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.
<!--end requires_ansible-->

### Supported connections
The Cisco DCNM collection supports ``httpapi`` connections.

## Included content
<!--start collection content-->
### Httpapi plugins
Name | Description
--- | ---
[cisco.dcnm.dcnm](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_httpapi.rst)|Ansible DCNM HTTPAPI Plugin.

### Modules
Name | Description
--- | ---
[cisco.dcnm.dcnm_bootflash](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_bootflash_module.rst)|Bootflash management for Nexus switches.
[cisco.dcnm.dcnm_fabric](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_fabric_module.rst)|Manage creation and configuration of NDFC fabrics.
[cisco.dcnm.dcnm_image_policy](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_image_policy_module.rst)|Image policy management for Nexus Dashboard Fabric Controller
[cisco.dcnm.dcnm_image_upgrade](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_image_upgrade_module.rst)|Image management for Nexus switches
[cisco.dcnm.dcnm_image_upload](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_image_upload_module.rst)|DCNM Ansible Module for managing images.
[cisco.dcnm.dcnm_interface](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_interface_module.rst)|DCNM Ansible Module for managing interfaces.
[cisco.dcnm.dcnm_inventory](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_inventory_module.rst)|Add and remove Switches from a DCNM managed VXLAN fabric.
[cisco.dcnm.dcnm_links](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_links_module.rst)|DCNM ansible module for managing Links.
[cisco.dcnm.dcnm_log](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_log_module.rst)|Log messages according to the configuration pointed to by the environment variable NDFC_LOGGING_CONFIG.
[cisco.dcnm.dcnm_maintenance_mode](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_maintenance_mode_module.rst)|Manage Maintenance Mode Configuration of NX-OS Switches.
[cisco.dcnm.dcnm_network](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_network_module.rst)|Add and remove Networks from a DCNM managed VXLAN fabric.
[cisco.dcnm.dcnm_policy](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_policy_module.rst)|DCNM Ansible Module for managing policies.
[cisco.dcnm.dcnm_resource_manager](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_resource_manager_module.rst)|DCNM ansible module for managing resources.
[cisco.dcnm.dcnm_rest](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_rest_module.rst)|Send REST API requests to DCNM controller.
[cisco.dcnm.dcnm_service_node](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_service_node_module.rst)|Create/Modify/Delete service node based on type and attached interfaces from a DCNM managed VXLAN fabric.
[cisco.dcnm.dcnm_service_policy](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_service_policy_module.rst)|DCNM ansible module for managing service policies.
[cisco.dcnm.dcnm_service_route_peering](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_service_route_peering_module.rst)|DCNM Ansible Module for managing Service Route Peerings.
[cisco.dcnm.dcnm_template](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_template_module.rst)|DCNM Ansible Module for managing templates.
[cisco.dcnm.dcnm_vpc_pair](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_vpc_pair_module.rst)|DCNM Ansible Module for managing VPC switch pairs required for VPC interfaces.
[cisco.dcnm.dcnm_vrf](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/docs/cisco.dcnm.dcnm_vrf_module.rst)|Add and remove VRFs from a DCNM managed VXLAN fabric.

<!--end collection content-->

Click the ``Content`` button to see the list of content included in this collection.

## Installing this collection

You can install the Cisco DCNM collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install cisco.dcnm

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: cisco.dcnm
    version: 3.7.0
```
## Using this collection


### Using modules from the Cisco DCNM collection in your playbooks

You can call modules by their Fully Qualified Collection Namespace (FQCN), such as `cisco.dcnm.dcnm_inventory`.
The following example task adds a switch to an existing fabric, using the FQCN:

```yaml
---

- hosts: dcnm_controllers
  gather_facts: false
  connection: ansible.netcommon.httpapi

  vars:
    password: !vault |
        $ANSIBLE_VAULT;1.1;AES256
        32393431346235343736383635656339363132666463316231653862373335356366663561316665
        3730346133626437383337366664616264656534313536640a303639313666373261633064343361
        33396463306231313937303766343165333332613636393263343734613136636232636162363639
        3233353437366362330a623962613031626633396630653530626636383333633065653965383864
        3165

  tasks:
    - name: Add switch n9kv-spine1 to fabric vxlan-fabric.
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: overridden
        config:
        - seed_ip: n9kv-spine1
          auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
          user_name: admin
          password: "{{ password }}"
          max_hops: 0
          role: spine # default is Leaf - choose from [leaf, spine, border, border_spine, border_gateway, border_gateway_spine
                           # super_spine, border_super_spine, border_gateway_super_spine]
          preserve_config: false # boolean, default is  true
      vars:
          ansible_command_timeout: 1000
          ansible_connect_timeout: 1000
      no_log: true
```

Alternately, you can call modules by their short name if you list the `cisco.dcnm` collection in the playbook's `collections`, as follows:

```yaml
---
- hosts: dcnm_controllers
  gather_facts: false
  connection: httpapi

  collections:
    - cisco.dcnm

  tasks:
    - name: Merge a Switch
      dcnm_inventory:
        ...parameters...
```

Sample hosts file using the dcnm httpapi connection plugin in either the INI or YAML format.

* Ansible INI Format

```ini
[dcnm_controllers]
192.168.2.10

[dcnm_controllers:vars]
ansible_user=dcnm_username
ansible_ssh_pass=dcnm_password
ansible_network_os=cisco.dcnm.dcnm
ansible_httpapi_validate_certs=False
ansible_httpapi_use_ssl=True
ansible_httpapi_login_domain=local
```

* Ansible YAML Format

```yaml
all:
  vars:
    ansible_user: "dcnm_username"
    ansible_password: "dcnm_password"
    ansible_python_interpreter: python
    ansible_httpapi_validate_certs: False
    ansible_httpapi_use_ssl: True
    ansible_httpapi_login_domain: local
  children:
    dcnm_controllers:
      hosts:
        192.168.2.10:
           ansible_network_os: cisco.dcnm.dcnm
```

### See Also:

* [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

Ongoing development efforts and contributions to this collection are solely focused on enhancements to current dcnm modules, additional dcnm modules and enhancements to the connection plugin.

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Cisco DCNM collection repository](https://github.com/CiscoDevNet/ansible-dcnm/issues).

## Changelogs

* [Changelog](https://github.com/CiscoDevNet/ansible-dcnm/blob/main/CHANGELOG.rst)

## More information

- [DCNM installation and configuration guides](https://www.cisco.com/c/en/us/support/cloud-systems-management/prime-data-center-network-manager/products-installation-and-configuration-guides-list.html)
- [NDFC installation and configuration guides](https://www.cisco.com/c/en/us/td/docs/dcn/ndfc/1201/installation/cisco-ndfc-install-and-upgrade-guide-1201.html)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)

## Licensing

Copyright (c) 2020-2025 Cisco and/or its affiliates.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
