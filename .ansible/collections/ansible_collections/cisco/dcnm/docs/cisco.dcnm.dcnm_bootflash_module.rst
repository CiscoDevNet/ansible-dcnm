.. _cisco.dcnm.dcnm_bootflash_module:


*************************
cisco.dcnm.dcnm_bootflash
*************************

**Bootflash management for Nexus switches.**


Version added: 3.6.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Delete, query bootflash files.




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="4">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>config</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Configuration parameters for the module.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>switches</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>List of dictionaries containing switches on which query or delete operations are executed.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ip_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The ip address of a switch.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>targets</b>
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
                        <div>List of dictionaries containing options for files to be deleted or queried.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>filepath</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The path to the file to be deleted or queried.  Only files in the root directory of the partition are currently supported.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>supervisor</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>active</b>&nbsp;&larr;</div></li>
                                    <li>standby</li>
                        </ul>
                </td>
                <td>
                        <div>Either active or standby. The supervisor containing the filepath.</div>
                </td>
            </tr>


            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>targets</b>
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
                        <div>List of dictionaries containing options for files to be deleted or queried.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>filepath</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The path to the file to be deleted or queried.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>supervisor</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>active</b>&nbsp;&larr;</div></li>
                                    <li>standby</li>
                        </ul>
                </td>
                <td>
                        <div>Either active or standby. The supervisor containing the filepath.</div>
                </td>
            </tr>


            <tr>
                <td colspan="4">
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
                                    <li><div style="color: blue"><b>query</b>&nbsp;&larr;</div></li>
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
    #   Delete files from the bootflash of one or more switches.
    #
    #   If an image is in use by a device, the module will fail.  Use
    #   dcnm_image_upgrade module, state deleted, to detach image policies
    #   containing images to be deleted.
    #
    # query:
    #
    #   Return information for one or more files.
    #
    # Delete two files from each of three switches.

    - name: Delete two files from each of two switches
      cisco.dcnm.dcnm_bootflash:
        state: deleted
        config:
          targets:
            - filepath: bootflash:/foo.txt
              supervisor: active
            - filepath: bootflash:/bar.txt
              supervisor: standby
          switches:
            - ip_address: 192.168.1.1
            - ip_address: 192.168.1.2
            - ip_address: 192.168.1.3

    # Delete two files from switch 192.168.1.1 and switch 192.168.1.2:
    #   - foo.txt on the active supervisor's bootflash: device.
    #   - bar.txt on the standby supervisor's bootflash: device.
    # Delete potentially multiple files from switch 192.168.1.3:
    #   - All txt files on the standby supervisor's bootflash: device
    #     that match the pattern 202401??.txt, e.g. 20240123.txt.
    # Delete potentially multiple files from switch 192.168.1.4:
    #   - All txt files on all flash devices on active supervisor.

    - name: Delete files
      cisco.dcnm.dcnm_bootflash:
        state: deleted
        config:
          targets:
            - filepath: bootflash:/foo.txt
              supervisor: active
            - filepath: bootflash:/bar.txt
              supervisor: standby
          switches:
            - ip_address: 192.168.1.1
            - ip_address: 192.168.1.2
            - ip_address: 192.168.1.3
              targets:
                - filepath: bootflash:/202401??.txt
                  supervisor: standby
            - ip_address: 192.168.1.4
              targets:
                - filepath: "*:/*.txt"
                  supervisor: active
      register: result
    - name: print result
      ansible.builtin.debug:
        var: result

    # Query the controller for information about one file on three switches.
    # Since the default for supervisor is "active", the module will query the
    # active supervisor's bootflash: device.

    - name: Query file on three switches
      cisco.dcnm.dcnm_bootflash:
        state: query
        config:
          targets:
            - filepath: bootflash:/foo.txt
        switches:
          - ip_address: 192.168.1.1
          - ip_address: 192.168.1.2
          - ip_address: 192.168.1.3
      register: result
    - name: print result
      ansible.builtin.debug:
        var: result




Status
------


Authors
~~~~~~~

- Allen Robel (@quantumonion)
