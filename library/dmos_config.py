#!/usr/bin/python

import json

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig, dumps

from ansible.module_utils.dmos import run_commands, get_config
from ansible.module_utils.dmos import get_defaults_flag, get_connection
from ansible.module_utils.dmos import dmos_argument_spec
from ansible.module_utils.dmos import check_args as dmos_check_args


def check_args(module, warnings):
    dmos_check_args(module, warnings)
    if module.params['multiline_delimiter']:
        if len(module.params['multiline_delimiter']) != 1:
            module.fail_json(msg='multiline_delimiter value can only be a '
                                 'single character')


def get_candidate_config(module):
    candidate = ''
    if module.params['src']:
        candidate = module.params['src']

    elif module.params['lines']:
        candidate_obj = NetworkConfig(indent=1)
        parents = module.params['parents'] or list()
        candidate_obj.add(module.params['lines'], parents=parents)
        candidate = dumps(candidate_obj, 'raw')

    return candidate


def get_running_config(module, current_config=None, flags=None):
    running = module.params['running_config']
    if not running:
        if not module.params['defaults'] and current_config:
            running = current_config
        else:
            running = get_config(module, flags=flags)

    return running


def save_config(module, result):
    result['changed'] = True
    if not module.check_mode:
        pass  # run_commands(module, 'copy running-config startup-config\r')
    else:
        module.warn('Skipping command `copy running-config startup-config` '
                    'due to check_mode.  Configuration not copied to '
                    'non-volatile storage')


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(
        filename=dict(),
        dir_path=dict(type='path')
    )
    argument_spec = dict(
        src=dict(type='path'),

        lines=dict(aliases=['commands'], type='list'),
        parents=dict(type='list'),

        before=dict(type='list'),
        after=dict(type='list'),

        match=dict(default='line', choices=[
                   'line', 'strict', 'exact', 'none']),
        replace=dict(default='line', choices=['line', 'block']),
        multiline_delimiter=dict(default='@'),

        running_config=dict(aliases=['config']),
        intended_config=dict(),

        defaults=dict(type='bool', default=False),
        backup=dict(type='bool', default=False),
        backup_options=dict(type='dict', options=backup_spec),
        save_when=dict(choices=['always', 'never',
                                'modified', 'changed'], default='never'),

        diff_against=dict(choices=['startup', 'intended', 'running']),
        diff_ignore_lines=dict(type='list'),
    )

    argument_spec.update(dmos_argument_spec)

    mutually_exclusive = [('lines', 'src'),
                          ('parents', 'src')]

    required_if = [('match', 'strict', ['lines']),
                   ('match', 'exact', ['lines']),
                   ('replace', 'block', ['lines']),
                   ('diff_against', 'intended', ['intended_config'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    check_args(module, warnings)
    result['warnings'] = warnings

    diff_ignore_lines = module.params['diff_ignore_lines']
    config = None
    contents = None
    flags = get_defaults_flag(module) if module.params['defaults'] else []
    connection = get_connection(module)

    if module.params['backup'] or (module._diff and module.params['diff_against'] == 'running'):
        contents = get_config(module, flags=flags)
        config = NetworkConfig(indent=1, contents=contents)
        if module.params['backup']:
            result['__backup__'] = contents

    if any((module.params['lines'], module.params['src'])):
        match = module.params['match']
        replace = module.params['replace']
        path = module.params['parents']

        candidate = get_candidate_config(module)
        running = get_running_config(module, contents, flags=flags)
        try:
            response = connection.get_diff(candidate=candidate, running=running, diff_match=match, diff_ignore_lines=diff_ignore_lines, path=path,
                                           diff_replace=replace)
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))

        config_diff = response['config_diff']
        banner_diff = response['banner_diff']

        if config_diff or banner_diff:
            commands = config_diff.split('\n')

            if module.params['before']:
                commands[:0] = module.params['before']

            if module.params['after']:
                commands.extend(module.params['after'])

            result['commands'] = commands
            result['updates'] = commands
            result['banners'] = banner_diff

            # send the configuration commands to the device and merge
            # them with the current running config
            if not module.check_mode:
                if commands:
                    connection.edit_config(candidate=commands)
                if banner_diff:
                    connection.edit_banner(candidate=json.dumps(
                        banner_diff), multiline_delimiter=module.params['multiline_delimiter'])

            result['changed'] = True

    running_config = module.params['running_config']
    startup_config = None

    if module.params['save_when'] == 'always':
        save_config(module, result)
    elif module.params['save_when'] == 'modified':
        output = run_commands(module, ['show running-config | nomore'])

        running_config = NetworkConfig(
            indent=1, contents=output[0], ignore_lines=diff_ignore_lines)
        startup_config = NetworkConfig(
            indent=1, contents=output[1], ignore_lines=diff_ignore_lines)

        if running_config.sha1 != startup_config.sha1:
            save_config(module, result)
    elif module.params['save_when'] == 'changed' and result['changed']:
        save_config(module, result)

    if module._diff:
        if not running_config:
            output = run_commands(module, 'show running-config | nomore')
            contents = output[0]
        else:
            contents = running_config

        # recreate the object in order to process diff_ignore_lines
        running_config = NetworkConfig(
            indent=1, contents=contents, ignore_lines=diff_ignore_lines)

        if module.params['diff_against'] == 'running':
            if module.check_mode:
                module.warn(
                    "unable to perform diff against running-config due to check mode")
                contents = None
            else:
                contents = config.config_text

        elif module.params['diff_against'] == 'startup':
            if not startup_config:
                output = run_commands(module, 'show startup-config')
                contents = output[0]
            else:
                contents = startup_config.config_text

        elif module.params['diff_against'] == 'intended':
            contents = module.params['intended_config']

        if contents is not None:
            base_config = NetworkConfig(
                indent=1, contents=contents, ignore_lines=diff_ignore_lines)

            if running_config.sha1 != base_config.sha1:
                if module.params['diff_against'] == 'intended':
                    before = running_config
                    after = base_config
                elif module.params['diff_against'] in ('startup', 'running'):
                    before = base_config
                    after = running_config

                result.update({
                    'changed': True,
                    'diff': {'before': str(before), 'after': str(after)}
                })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
