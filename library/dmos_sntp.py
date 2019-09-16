#!/usr/bin/python

import json

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.dmos import dmos_argument_spec
from ansible.module_utils.dmos import check_args
from ansible.module_utils.dmos import get_diff, edit_config
from ansible.module_utils.dmos import validate_ip, is_v4


def parse_commands(module, warnings):
    commands = []
    state_prefix = '' if module.params['state'] == 'present' else 'no '

    if module.params['source'] != None:
        if validate_ip(module.params['source']):
            v_type = 'ipv6'
            if is_v4(module.params['source']):
                v_type = 'ipv4'
            commands.append('{0}sntp source {1} address {2}'.format(
                state_prefix, v_type, module.params['source']))
        else:
            warnings.append('Invalid ip format')

    if module.params['min_poll'] != None:
        commands.append(
            '{0}sntp min-poll {1}'.format(state_prefix, module.params['min_poll']))

    if module.params['max_poll'] != None:
        commands.append(
            '{0}sntp max-poll {1}'.format(state_prefix, module.params['max_poll']))

    if module.params['key_id'] != None and module.params['auth_key'] != None:
        commands.append('{0}sntp authentication-key {1} md5 {2}'.format(
            state_prefix, module.params['key_id'], module.params['auth_key']))
    elif module.params['auth_key'] != None:
        warnings.append(
            'To configure authentication key its necessary to provide key id')

    if module.params['server'] != None:
        if validate_ip(module.params['server']):
            command = '{0}sntp server {1}'.format(
                state_prefix, module.params['server'])
            if module.params['key_id'] != None:
                command += ' key {0}'.format(module.params['key_id'])
            commands.append(command)
        else:
            warnings.append('Invalid ip format')

    if module.params['client'] != None:
        prefix = '' if module.params['client'] is True else 'no '
        commands.append('{0}sntp client'.format(prefix))

    if module.params['auth'] != None:
        prefix = '' if module.params['auth'] is True else 'no '
        commands.append('{0}sntp authenticate'.format(prefix))

    return commands


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = dict(
        server=dict(type='str'),
        source=dict(type='str'),
        min_poll=dict(type='int', choices=range(3, 18)),
        max_poll=dict(type='int', choices=range(3, 18)),
        client=dict(type='bool'),
        auth=dict(type='bool'),
        auth_key=dict(type='str'),
        key_id=dict(type='int'),
        state=dict(choices=['absent', 'present'], default='present')
    )

    argument_spec.update(dmos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    check_args(module, warnings)

    commands = parse_commands(module, warnings)

    if commands:
        candidates = get_diff(module=module, candidates=commands)

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
