#!/usr/bin/python

import json

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig, dumps

from ansible.module_utils.dmos import run_commands, get_config
from ansible.module_utils.dmos import get_defaults_flag, get_connection
from ansible.module_utils.dmos import dmos_argument_spec
from ansible.module_utils.dmos import check_args


def get_diff(connection=None, commands=None):
    candidate = []
    if connection:
        for command in commands:
            if not connection.get_config(command=command):
                candidate.append(command)

    return candidate


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = dict(
        src=dict(type='path'),

        lines=dict(aliases=['commands'], type='list')
    )

    argument_spec.update(dmos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    check_args(module, warnings)
    result['warnings'] = warnings

    connection = get_connection(module)

    if module.params['lines']:
        commands = module.params['lines']

        candidate = get_diff(connection=connection, commands=commands)

        if candidate:
            result['changes'] = candidate

            if not module.check_mode:
                connection.edit_config(candidate=candidate)

            result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
