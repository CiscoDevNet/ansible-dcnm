

# Cisco DCNM Collection

The Ansible Cisco Data Center Network Manager (DCNM) collection includes modules to help automate common day 2 operations for VXLAN EVPN fabrics.

Early field trial release for use with `DCNM Release 11.4(1)`.

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
[cisco.dcnm.dcnm](docs/cisco.dcnm.dcnm_httpapi.rst)|Ansible DCNM HTTPAPI Plugin.

### Modules
Name | Description
--- | ---
[cisco.dcnm.dcnm_interface](docs/cisco.dcnm.dcnm_interface_module.rst)|DCNM Ansible Module for managing interfaces.
[cisco.dcnm.dcnm_inventory](docs/cisco.dcnm.dcnm_inventory_module.rst)|Add and remove Switches from a DCNM managed VXLAN fabric.
[cisco.dcnm.dcnm_network](docs/cisco.dcnm.dcnm_network_module.rst)|Add and remove Networks from a DCNM managed VXLAN fabric.
[cisco.dcnm.dcnm_rest](docs/cisco.dcnm.dcnm_rest_module.rst)|Send REST API requests to DCNM controller.
[cisco.dcnm.dcnm_vrf](docs/cisco.dcnm.dcnm_vrf_module.rst)|Add and remove VRFs from a DCNM managed VXLAN fabric.

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

- hosts: dcnm
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
- hosts: dcnm_hosts
  gather_facts: false
  connection: httpapi

  collections:
    - cisco.dcnm

  tasks:
    - name: Merge a Switch
      dcnm_inventory:
        ...parameters...
```


### See Also:

* [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

Ongoing development efforts and contributions to this collection are solely focused on enhancements to current dcnm modules, additional dcnm modules and enhancements to the connection plugin.

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Cisco DCNM collection repository](https://github.com/CiscoDevNet/ansible-dcnm/issues).

## Changelogs

* [Changelog](CHANGELOG.md)

## More information

- [DCNM installation and configuration guides](https://www.cisco.com/c/en/us/support/cloud-systems-management/prime-data-center-network-manager/products-installation-and-configuration-guides-list.html)
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
