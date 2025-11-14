.. _cisco.dcnm.dcnm_image_policy_module:


****************************
cisco.dcnm.dcnm_image_policy
****************************

**Image policy management for Nexus Dashboard Fabric Controller**


Version added: 3.5.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Create, delete, modify image policies.




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="3">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>config</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>List of dictionaries containing image policy parameters</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>agnostic</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>The agnostic flag.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>The image policy description.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>epld_image</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>The epld image name.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The image policy name.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>packages</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A dictionary containing two keys, install and uninstall.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>install</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A list of packages to install.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>uninstall</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A list of packages to uninstall.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>platform</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The platform to which the image policy applies e.g. N9K.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>release</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The release associated with the image policy.</div>
                        <div>This is derived from the image name as follows.</div>
                        <div>From image name nxos64-cs.10.2.5.M.bin</div>
                        <div>we need to extract version (10.2.5), platform (nxos64-cs), and bits (64bit).</div>
                        <div>The release string conforms to format (version)_(platform)_(bits)</div>
                        <div>so the resulting release string will be 10.2.5_nxos64-cs_64bit</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"PLATFORM"</div>
                </td>
                <td>
                        <div>The type of the image policy e.g. PLATFORM.</div>
                </td>
            </tr>

            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>state</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>deleted</li>
                                    <li><div style="color: blue"><b>merged</b>&nbsp;&larr;</div></li>
                                    <li>overridden</li>
                                    <li>query</li>
                                    <li>replaced</li>
                        </ul>
                </td>
                <td>
                        <div>The state of the feature or object after module completion</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    # This module supports the following states:
    #
    # deleted:
    #   Delete image policies from the controller.
    #
    #   If an image policy has references (i.e. it is attached to a device),
    #   the module will fail.  Use dcnm_image_upgrade module, state deleted,
    #    to detach the image policy from all devices before deleting it.
    #
    # merged:
    #   Create (or update) one or more image policies.
    #
    #   If an image policy does not exist on the controller, create it.
    #   If an image policy already exists on the controller, edit it.
    #
    # overridden:
    #   Create/delete one or more image policies.
    #
    #   If an image policy already exists on the controller, delete it and update
    #   it with the configuration in the playbook task.
    #
    #   Remove any image policies from the controller that are not in the
    #   playbook task.
    #
    # query:
    #
    #   Return the configuration for one or more image policies.
    #
    # replaced:
    #
    #   Replace image policies on the controller with policies in the playbook task.
    #
    #   If an image policy exists on the controller, but not in the playbook task,
    #   do not delete it or modify it.
    #
    # Delete two image policies from the controller.

        -   name: Delete Image policies
            cisco.dcnm.dcnm_image_policy:
                state: deleted
                config:
                -   name: KR5M
                -   name: NR3F
            register: result
        -   name: print result
            ansible.builtin.debug:
                var: result

    # Merge two image policies into the controller.

        -   name: Merge Image policies
            cisco.dcnm.dcnm_image_policy:
                state: merged
                config:
                -   name: KR5M
                    agnostic: false
                    description: KR5M
                    epld_image: n9000-epld.10.2.5.M.img
                    packages:
                       install:
                       - mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm
                       uninstall:
                       - mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000
                    platform: N9K
                    release: 10.2.5_nxos64-cs_64bit
                    type: PLATFORM
                -   name: NR3F
                    description: NR3F
                    platform: N9K
                    epld_image: n9000-epld.10.3.1.F.img
                    release: 10.3.1_nxos64-cs_64bit
            register: result
        -   name: print result
            ansible.builtin.debug:
                var: result

    # Override all policies on the controller and replace them with
    # the policies in the playbook task.  Any policies other than
    # KR5M and NR3F are deleted from the controller.

        -   name: Override Image policies
            cisco.dcnm.dcnm_image_policy:
                state: overridden
                config:
                -   name: KR5M
                    agnostic: false
                    description: KR5M
                    epld_image: n9000-epld.10.2.5.M.img
                    platform: N9K
                    release: 10.2.5_nxos64-cs_64bit
                    type: PLATFORM
                -   name: NR3F
                    description: NR3F
                    platform: N9K
                    epld_image: n9000-epld.10.2.5.M.img
                    release: 10.3.1_nxos64-cs_64bit
            register: result
        -   name: print result
            ansible.builtin.debug:
                var: result

    # Query the controller for the policies in the playbook task.

        -   name: Query Image policies
            cisco.dcnm.dcnm_image_policy:
                state: query
                config:
                -   name: NR3F
                -   name: KR5M
            register: result
        -   name: print result
            ansible.builtin.debug:
                var: result

    # Replace any policies on the controller that are in the playbook task with
    # the configuration given in the playbook task.  Policies not listed in the
    # playbook task are not modified and are not deleted.

        -   name: Replace Image policies
            cisco.dcnm.dcnm_image_policy:
                state: replaced
                config:
                -   name: KR5M
                    agnostic: false
                    description: KR5M
                    epld_image: n9000-epld.10.2.5.M.img
                    platform: N9K
                    release: 10.2.5_nxos64-cs_64bit
                    type: PLATFORM
                -   name: NR3F
                    description: Replaced NR3F
                    platform: N9K
                    epld_image: n9000-epld.10.3.1.F.img
                    release: 10.3.1_nxos64-cs_64bit
            register: result
        -   name: print result
            ansible.builtin.debug:
                var: result




Status
------


Authors
~~~~~~~

- Allen Robel (@quantumonion)
