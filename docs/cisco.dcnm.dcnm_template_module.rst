.. _cisco.dcnm.dcnm_template_module:


************************
cisco.dcnm.dcnm_template
************************

**DCNM Ansible Module for managing templates.**


Version added: 1.1.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- DCNM Ansible Module for creating, deleting and modifying template service
- operations




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="2">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>config</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A dictionary of template operations</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>content</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Multiple line configuration snip that can be used to associate to devices as policy</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
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
                        <div>Description of the template. The description may include the details regarding the content</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the template.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>tags</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>User defined labels for identifying the templates</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>cli</b>&nbsp;&larr;</div></li>
                                    <li>python</li>
                        </ul>
                </td>
                <td>
                        <div>Type of the template content either CLI or Python</div>
                </td>
            </tr>

            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>state</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>merged</b>&nbsp;&larr;</div></li>
                                    <li>deleted</li>
                                    <li>query</li>
                        </ul>
                </td>
                <td>
                        <div>The required state of the configuration after module completion.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    # States:
    # This module supports the following states:
    #
    # Merged:
    #   Templates defined in the playbook will be merged into the target.
    #
    #   The templates listed in the playbook will be created if not already present on the DCNM
    #   server. If the template is already present and the configuration information included
    #   in the playbook is either different or not present in DCNM, then the corresponding
    #   information is added to the template on DCNM. If a template mentioned in playbook
    #   is already present on DCNM and there is no difference in configuration, no operation
    #   will be performed for such a template.
    #
    # Deleted:
    #   Templates defined in the playbook will be deleted from the target.
    #
    #   Deletes the list of templates specified in the playbook.
    #
    # Query:
    #   Returns the current DCNM state for the templates listed in the playbook.


    # To create or modify templates

    - name: Create or modify templates
      cisco.dcnm.dcnm_template:
        state: merged        # only choose form [merged, deleted, query]
        config:
          - name: template_101
            description: "Template_101"
            tags: "internal policy 101"
            content: |
              telemetry
                certificate /bootflash/telegraf.crt telegraf
                destination-profile
                  use-vrf management
                destination-group 101
                  ip address 10.195.225.176 port 57101 protocol gRPC encoding GPB
                sensor-group 101
                  data-source DME
                  path sys/ch depth unbounded
                subscription 101
                  dst-grp 101
                  snsr-grp 101 sample-interval 10101

          - name: template_102
            description: "Template_102"
            tags: "internal policy 102"
            content: |
              telemetry
                certificate /bootflash/telegraf.crt telegraf
                destination-profile
                  use-vrf management
                destination-group 1
                  ip address 10.195.225.102 port 57102 protocol gRPC encoding GPB
                sensor-group 102
                  data-source DME
                  path sys/ch depth unbounded
                subscription 102
                  dst-grp 102
                  snsr-grp 102 sample-interval 10102

    # To delete templates

    - name: Delete templates
      cisco.dcnm.dcnm_template:
        state: deleted       # only choose form [merged, deleted, query]
        config:
          - name: template_101

          - name: template_102

          - name: template_103

          - name: template_104

    # To query templates

    - name: Query templates
      cisco.dcnm.dcnm_template:
        state: query       # only choose form [merged, deleted, query]
        config:
          - name: template_101

          - name: template_102

          - name: template_103

          - name: template_104




Status
------


Authors
~~~~~~~

- Mallik Mudigonda(@mmudigon)
