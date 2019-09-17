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

    config = module.params['config']
    if config:
        config = config[0]
        if config['source'] != None:
            if validate_ip(config['source']):
                v_type = 'ipv6'
                if is_v4(config['source']):
                    v_type = 'ipv4'
                commands.append('{0}sntp source {1} address {2}'.format(
                    state_prefix, v_type, config['source']))
            else:
                warnings.append('Invalid ip format')

        if config['min_poll'] != None:
            commands.append(
                '{0}sntp min-poll {1}'.format(state_prefix, config['min_poll']))

        if config['max_poll'] != None:
            commands.append(
                '{0}sntp max-poll {1}'.format(state_prefix, config['max_poll']))

        for auth_key in config['auth_key']:
            command = '{0}sntp authentication-key {1}'.format(
                state_prefix, auth_key['id'])
            if auth_key['pass'] != None:
                command += ' md5 {0}'.format(auth_key['pass'])
            commands.append(command)

        for server in config['server']:
            if validate_ip(server['address']):
                command = '{0}sntp server {1}'.format(
                    state_prefix, server['address'])
                if server['key_id'] != None:
                    command += ' key {0}'.format(server['key_id'])
                commands.append(command)
            else:
                warnings.append('Invalid ip format')

        if config['client'] != None:
            prefix = '' if config['client'] is True else 'no '
            commands.append('{0}sntp client'.format(prefix))

        if config['auth'] != None:
            prefix = '' if config['auth'] is True else 'no '
            commands.append('{0}sntp authenticate'.format(prefix))

    return commands


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = {'config': {'type': 'list',
                                'elements': 'dict',
                                'options': {'auth': {'type': 'bool'},
                                            'auth_key': {'element': 'dict',
                                                         'type': 'list',
                                                         'options': {'id': {'type': 'int', 'required': True},
                                                                     'pass': {'type': 'str'}
                                                                     }
                                                         },
                                            'client': {'type': 'bool'},
                                            'max_poll': {'type': 'int', 'choices': range(3, 18)},
                                            'min_poll': {'type': 'int', 'choices': range(3, 18)},
                                            'server': {'element': 'dict',
                                                       'type': 'list',
                                                       'options': {'address': {'type': 'str', 'required': True},
                                                                   'key_id': {'type': 'int'}
                                                                   }
                                                       },
                                            'source': {'type': 'str'}
                                            }
                                },
                     'state': {'choices': ['absent', 'present'],
                               'default': 'present',
                               'type': 'str'}
                     }

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
