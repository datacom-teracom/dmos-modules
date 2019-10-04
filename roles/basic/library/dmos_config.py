#!/usr/bin/python

import json

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.dmos.dmos import dmos_argument_spec
from ansible.module_utils.network.dmos.dmos import get_config, edit_config
from ansible.module_utils.network.dmos.utils.utils import get_command_list_from_curly_braces, get_command_list_diff


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = dict(
        lines=dict(aliases=['commands'], type='list')
    )

    argument_spec.update(dmos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()

    if module.params['lines']:
        config = get_config(module=module)
        command_list = get_command_list_from_curly_braces(output=config)
        candidates = get_command_list_diff(
            configs=command_list, candidates=module.params['lines'])

        if candidates:
            result['changes'] = candidates

            if not module.check_mode:
                response = edit_config(module=module, candidates=candidates)
                result['response'] = response['response']

            result['changed'] = True

    result['warnings'] = warnings
    module.exit_json(**result)


if __name__ == '__main__':
    main()
