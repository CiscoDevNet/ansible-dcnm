===========================================
Cisco NDFC Ansible Collection Release Notes
===========================================

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](http://semver.org/).

.. contents:: Topics

`3.4.1`_ - 2023-08-17
=====================
                                              
There is no functional difference between collection version `3.4.0` and collection version `3.4.1`.  This version is only being published as a hotfix to resolve a problem where the wrong
version was inadvertently published to Ansible galaxy.

`3.4.0`_ - 2023-08-16
=====================

Added
-----

- Support for save and deploy options in `dcnm_inventory` module.
- Support for `discovery_username` and `discovery_password` in `dcnm_inventory` module.
- Support for login domain in connection plugin.

Fixed
-----

- Fix for deploy flag behaviour in inferface module. Config will not be deployed to switches if deploy flag is set to false. When deploy flag is set to true in task and if any of the switch in that task is not manageable or the fabric in task is read-only, then an error is returned without making any changes in the NDFC corresponding to that task.


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
