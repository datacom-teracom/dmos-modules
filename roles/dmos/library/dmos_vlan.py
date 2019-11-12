#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The module file for dmos_vlan
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': '<support_group>'
}

DOCUMENTATION = """
---
module: dmos_vlan
version_added: 4.9
short_description: 'Manages <xxxx> attributes of <network_os> <resource>.'
description: 'Manages <xxxx> attributes of <network_os> <resource>'
author: Ansible Network Engineer
notes:
  - 'Tested against <network_os> <version>'
options:
  config:
    description: The provided configuration
    type: list
    elements: dict
    suboptions:
      vlan_id:
        description: <1-4094> VLAN ID
        type: int
        required: true
      name:
        description: Text name identifying the VLAN (max 32 chars).
        type: str
      interface:
        description: Statically add interfaces to VLANs and remove interfaces from VLANs
        type: list
        elements: dict
        suboptions:
          name:
            description: Interface name
            type: str
            required: true
          tagged:
            description: Set this interface as an tagged member
            type: bool
  state:
    description:
    - The state the configuration should be left in
    type: str
    choices:
    - merged
    - replaced
    - overridden
    - deleted
    default: merged
"""
EXAMPLES = """
### Using Merged ###

dmos_vlan:
  config:
    - vlan_id: 2019
      interface:
        - name: gigabit-ethernet-1/1/1
          tagged: true
      name: null
    - vlan_id: 2020
      name: dmos_vlan
      interface:
        - name: gigabit-ethernet-1/1/2
          tagged: false
    - vlan_id: 2021
  state: merged

# This configuration will result in the following commands:

# - dot1q vlan 2019 interface gigabit-ethernet-1/1/1 tagged
# - dot1q vlan 2020 name dmos_vlan
# - dot1q vlan 2020 interface gigabit-ethernet-1/1/2 untagged
# - dot1q vlan 2021

### Using Deleted ###

dmos_vlan:
  config:
    - vlan_id: 2019
      interface:
        - name: gigabit-ethernet-1/1/1
    - vlan_id: 2020
      name: dmos_vlan
    - vlan_id: 2021
  state: deleted

# This configuration will result in the following commands:

# - no dot1q vlan 2019 interface gigabit-ethernet-1/1/1
# - no dot1q vlan 2020 name
# - no dot1q vlan 2021
"""
RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample: ['command 1', 'command 2', 'command 3']
changed:
  description: If configuration resulted in any change
  returned: always
  type: bool
  sample: True or False
response:
  description: The response of executed commands
  returned: always
  type: list
  sample: ['Aborted: reason']
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.dmos.argspec.vlan.vlan import VlanArgs
from ansible.module_utils.network.dmos.config.vlan.vlan import Vlan


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=VlanArgs.argument_spec,
                           supports_check_mode=True)

    result = Vlan(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
