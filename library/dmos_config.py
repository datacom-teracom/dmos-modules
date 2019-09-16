#!/usr/bin/python

import json

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.dmos import dmos_argument_spec
from ansible.module_utils.dmos import check_args
from ansible.module_utils.dmos import get_diff, edit_config


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
    check_args(module, warnings)

    if module.params['lines']:
        candidates = get_diff(module=module, candidates=module.params['lines'])

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
