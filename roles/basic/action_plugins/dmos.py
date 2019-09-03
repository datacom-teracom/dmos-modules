from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import sys
import copy

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.plugins.action.network import ActionModule as ActionNetworkModule
from ansible.module_utils.network.common.utils import load_provider
from ansible.utils.display import Display

from ansible.module_utils.dmos import dmos_argument_spec, check_args

display = Display()


class ActionModule(ActionNetworkModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        self._config_module = True if self._task.action == 'dmos_config' else False
        socket_path = None

        if self._play_context.connection == 'network_cli':
            provider = self._task.args.get('provider', {})
            if any(provider.values()):
                display.warning('provider is unnecessary when using network_cli and will be ignored')
                del self._task.args['provider']
        elif self._play_context.connection == 'local':
            provider = load_provider(dmos_provider_spec, self._task.args)
            pc = copy.deepcopy(self._play_context)
            pc.connection = 'network_cli'
            pc.network_os = 'dmos'
            pc.remote_addr = provider['host'] or self._play_context.remote_addr
            pc.port = int(provider['port'] or self._play_context.port or 22)
            pc.remote_user = provider['username'] or self._play_context.connection_user
            pc.password = provider['password'] or self._play_context.password
            pc.private_key_file = provider['ssh_keyfile'] or self._play_context.private_key_file
            pc.become = provider['authorize'] or False
            if pc.become:
                pc.become_method = 'enable'
            pc.become_pass = provider['auth_pass']

            display.vvv('using connection plugin %s (was local)' % pc.connection, pc.remote_addr)
            connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin)

            command_timeout = int(provider['timeout']) if provider['timeout'] else connection.get_option('persistent_command_timeout')
            connection.set_options(direct={'persistent_command_timeout': command_timeout})

            socket_path = connection.run()
            display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
            if not socket_path:
                return {'failed': True,
                        'msg': 'unable to open shell. Please see: ' +
                               'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

            task_vars['ansible_socket'] = socket_path
        else:
            return {'failed': True, 'msg': 'Connection type %s is not valid for this module' % self._play_context.connection}

        # make sure we are in the right cli context which should be
        # enable mode and not config module
        if socket_path is None:
            socket_path = self._connection.socket_path

        conn = Connection(socket_path)
        try:
            out = conn.get_prompt()
            if re.search(r'config.*\)#', to_text(out, errors='surrogate_then_replace').strip()):
                display.vvvv('wrong context, sending end to device', self._play_context.remote_addr)
                conn.send_command('end')
        except ConnectionError as exc:
            return {'failed': True, 'msg': to_text(exc)}

        result = super(ActionModule, self).run(task_vars=task_vars)
        return result
