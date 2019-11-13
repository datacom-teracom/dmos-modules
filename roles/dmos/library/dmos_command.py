#!/usr/bin/python
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import transform_commands, to_lines

from ansible.module_utils.network.dmos.dmos import dmos_argument_spec
from ansible.module_utils.network.dmos.dmos import run_commands


DOCUMENTATION = """
---
module: dmos_command
version_added: 4.9
short_description: execute show commands on dmos devices.
description: execute show commands on dmos devices.
author: Ansible Network Engineer
options:
  commands:
    description:
      - list of DmOS show command
    required: false
"""

EXAMPLES = """
# Execute show running-config interface l3 command on DmOS device
- dmos_command:
    commands:
      - show running-config interface l3
      - show oam twamp sender
"""

RETURN = """
changed:
  description: Always false.
  returned: always
  sample: True or False
stdout:
  description: Raw output of command.
  returned: always
  sample: ["interface l3 test\n ipv4 address 10.0.0.1/24\n!"]
stdout_lines:
  description: Raw output of command splitted in lines.
  returned: always
  sample: ["interface l3 test", "ipv4 address 10.0.0.1/24", "!"]
"""


def parse_commands(module, warnings):
    commands = transform_commands(module)

    if module.check_mode:
        for item in list(commands):
            if not item['command'].startswith('show'):
                warnings.append(
                    'Only show commands are supported when using check mode, not '
                    'executing %s' % item['command']
                )
                commands.remove(item)

    return commands


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        commands=dict(type='list', required=True),
        match=dict(type='str', choices=['exact']),
        lines=dict(type='list'),
    )

    argument_spec.update(dmos_argument_spec)

    required_if = [('match', 'exact', ['lines'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    commands = parse_commands(module, warnings)

    responses = run_commands(module, commands)

    if module.params['match']:
        for line in module.params['lines']:
            if line not in responses:
                module.fail_json(msg="didn't match the lines")
                return

    result = {'changed': False, 'warnings': warnings}
    result.update({
        'stdout': responses,
        'stdout_lines': list(to_lines(responses)),
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
