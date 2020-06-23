

# Cisco DCNM Collection

The Ansible Cisco Data Center Network Manager (DCNM) collection includes modules to help automate common day 2 operations for VXLAN EVPN fabrics.

Early field trial release for use with `DCNM Release 11.4`.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.9.10,<2.11**.

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
[cisco.dcnm.dcnm](https://github.com/CiscoDevNet/ansible-dcnm/blob/master/docs/cisco.dcnm.dcnm_httpapi.rst)|Send REST api calls to Data Center Network Manager (DCNM) NX-OS Fabric Controller.

### Modules
Name | Description
--- | ---
[cisco.dcnm.dcnm_interface](https://github.com/CiscoDevNet/ansible-dcnm/blob/master/docs/cisco.dcnm.dcnm_interface_module.rst)|DCNM Ansible Module for managing interfaces.
[cisco.dcnm.dcnm_inventory](https://github.com/CiscoDevNet/ansible-dcnm/blob/master/docs/cisco.dcnm.dcnm_inventory_module.rst)|Send REST API requests to DCNM controller for INVENTORY operations
[cisco.dcnm.dcnm_network](https://github.com/CiscoDevNet/ansible-dcnm/blob/master/docs/cisco.dcnm.dcnm_network_module.rst)|Send REST API requests to DCNM controller for network operations
[cisco.dcnm.dcnm_rest](https://github.com/CiscoDevNet/ansible-dcnm/blob/master/docs/cisco.dcnm.dcnm_rest_module.rst)|Send REST API requests to DCNM controller.
[cisco.dcnm.dcnm_vrf](https://github.com/CiscoDevNet/ansible-dcnm/blob/master/docs/cisco.dcnm.dcnm_vrf_module.rst)|Send REST API requests to DCNM controller for vrf operations

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
    version: 0.9.0
```
## Using this collection


### Using modules from the Cisco DCNM collection in your playbooks

You can call modules by their Fully Qualified Collection Namespace (FQCN), such as `cisco.dcnm.dcnm_inventory`.
The following example task adds a switch to an existing fabric, using the FQCN:

```yaml
---
    - name: Merge a Switch
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: merged
        config:
        - seed_ip: 192.168.0.1
          auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
          user_name: admin
          password: password
          max_hops: 0
          role: leaf # default is Leaf - choose from [Leaf, Spine, Border, Border Spine, Border Gateway, Border Gateway Spine
                           # Super Spine, Border Super Spine, Border Gateway Super Spine]
          preserve_config: False # boolean, default is  true
```

Alternately, you can call modules by their short name if you list the `cisco.dcnm` collection in the playbook's `collections`, as follows:

```yaml
---
- hosts: dcnm_hosts
  gather_facts: false
  connection: httpapi

  collections:
    - cisco.dcnm

  tasks:
    - name: Merge a Switch
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: merged
        config:
        - seed_ip: 192.168.0.1
          auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
          user_name: admin
          password: password
          max_hops: 0
          role: leaf # default is Leaf - choose from [Leaf, Spine, Border, Border Spine, Border Gateway, Border Gateway Spine
                           # Super Spine, Border Super Spine, Border Gateway Super Spine]
          preserve_config: False # boolean, default is  true
```


### See Also:

* [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

Ongoing development efforts and contributions to this collection are solely focused on enhancements to current dcnm modules, additional dcnm modules and enhancements to the connection plugin.

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Cisco DCNM collection repository](link_to_repo).

See the [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) for details on contributing to Ansible.


## Changelogs
<!--Add a link to a changelog.md file or an external docsite to cover this information. -->

## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

- [DCNM configuration guide](https://www.cisco.com/c/en/us/td/docs/switches/datacenter/sw/11_3_1/config_guide/lanfabric/b_dcnm_fabric_lan.html)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)

## Licensing

Copyright (c) 2020 Cisco and/or its affiliates.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.