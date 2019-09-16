#!/usr/bin/python
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import transform_commands, to_lines

from ansible.module_utils.dmos import run_commands
from ansible.module_utils.dmos import dmos_argument_spec, check_args


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
    )

    argument_spec.update(dmos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    commands = parse_commands(module, warnings)

    responses = run_commands(module, commands)

    result = {'changed': False, 'warnings': warnings}
    result.update({
        'stdout': responses,
        'stdout_lines': list(to_lines(responses)),
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
