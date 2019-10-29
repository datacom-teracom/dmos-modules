#!/usr/bin/python

import json

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.common.utils import to_lines

from ansible.module_utils.network.dmos.dmos import run_commands
from ansible.module_utils.network.dmos.dmos import dmos_argument_spec


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
