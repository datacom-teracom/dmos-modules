#!/usr/bin/python

import json

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.common.utils import to_lines

from ansible.module_utils.network.dmos.dmos import run_commands
from ansible.module_utils.network.dmos.dmos import dmos_argument_spec


DOCUMENTATION = """
---
module: dmos_system
version_added: 4.9
short_description: Configure system of dmos devices.
description: Configure system of dmos devices.
author: Ansible Network Engineer
options:
  hour:
    description: DmOS system hour
    required: true
  minute:
    description: DmOS system minute
    required: true
  second:
    description: DmOS system second
    required: false
  year:
    description: DmOS system year
    required: true
  month:
    description: DmOS system month
    required: true
  day:
    description: DmOS system day
    required: true
"""

EXAMPLES = """
# Set DmOS device system time
- dmos_system:
  hour: 19
  minute: 18
  second: 47
  year: 2018
  month: 10
  day: 18
"""

RETURN = """
changed:
  description: If configuration resulted in any change.
  returned: always
  sample: True or False
command:
  description: Executed commands.
  returned: always
  sample: set system clock 19:18:47 20181018
stdout:
  description: Raw output of command.
  returned: always
  sample: ["Clock is set."]
stdout_lines:
  description: Raw output of command splitted in lines.
  returned: always
  sample: ["Clock is set."]
"""


def parse_command(module, warnings):
    command = """set system clock {0:02d}:{1:02d}:{2:02d} """.format(
        module.params['hour'], module.params['minute'], module.params['second'])

    command += """{0:04d}{1:02d}{2:02d}""".format(
        module.params['year'], module.params['month'], module.params['day'])

    return command


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = dict(
        hour=dict(required=True, type='int', choices=range(0, 24)),
        minute=dict(required=True, type='int', choices=range(0, 61)),
        second=dict(type='int', choices=range(0, 61), default=0),
        year=dict(required=True, type='int', choices=range(1970, 2099)),
        month=dict(required=True, type='int', choices=range(1, 13)),
        day=dict(required=True, type='int', choices=range(1, 32))
    )

    argument_spec.update(dmos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': True}

    warnings = list()

    command = parse_command(module, warnings)
    result['command'] = command

    responses = run_commands(module, [command])

    result['warnings'] = warnings
    result.update({
        'stdout': responses,
        'stdout_lines': list(to_lines(responses)),
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
