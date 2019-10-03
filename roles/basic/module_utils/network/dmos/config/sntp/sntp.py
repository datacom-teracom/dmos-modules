#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The dmos_sntp class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.dmos.facts.facts import Facts
from ansible.module_utils.network.dmos.utils.utils import dict_to_set


class Sntp(ConfigBase):
    """
    The dmos_sntp class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'sntp',
    ]

    def __init__(self, module):
        super(Sntp, self).__init__(module)

    def get_sntp_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
        sntp_facts = facts['ansible_network_resources'].get('sntp')
        if not sntp_facts:
            return []
        return sntp_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        existing_sntp_facts = self.get_sntp_facts()
        commands.extend(self.set_config(existing_sntp_facts))
        if commands:
            if not self._module.check_mode:
                response = self._connection.edit_config(commands)
                result['response'] = response['response']
            result['changed'] = True
        result['commands'] = commands

        changed_sntp_facts = self.get_sntp_facts()

        result['before'] = existing_sntp_facts
        if result['changed']:
            result['after'] = changed_sntp_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_sntp_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_sntp_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)
        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        if want:
            for config in want:
                for each in have:
                    commands.extend(self._set_config(config, each))
        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if want:
            for config in want:
                for each in have:
                    commands.extend(self._delete_config(config, each))
        else:
            want = dict()
            for each in have:
                commands.extend(self._delete_config(want, each))
        return commands

    def _set_config(self, want, have):
        # Set the interface config based on the want and have config
        commands = []

        # Convert the want and have dict to set
        want_dict = dict_to_set(want)
        have_dict = dict_to_set(have)

        diff = want_dict - have_dict

        auth = dict(diff).get('auth')
        if auth != None:
            commands.append(
                '{0} sntp authenticate'.format('' if auth else 'no'))

        auth_key = dict(diff).get('auth_key')
        if auth_key != None:
            for each in auth_key:
                auth_key_dict = dict(each)
                if auth_key_dict.get('id'):
                    cmd = 'sntp authentication-key {0}'.format(auth_key_dict['id'])
                    if auth_key_dict.get('pass'):
                        cmd += ' md5 {0}'.format(auth_key_dict['pass'])
                    commands.append(cmd)

        client = dict(diff).get('client')
        if client != None:
            commands.append('{0} sntp client'.format('' if client else 'no'))

        max_poll = dict(diff).get('max_poll')
        if max_poll != None:
            commands.append('sntp max-poll {0}'.format(max_poll))

        min_poll = dict(diff).get('min_poll')
        if min_poll != None:
            commands.append('sntp min-poll {0}'.format(min_poll))

        server = dict(diff).get('server')
        if server != None:
            for each in server:
                server_dict = dict(each)
                if server_dict.get('address'):
                    cmd = 'sntp server {0}'.format(server_dict['address'])
                    if server_dict.get('key_id'):
                        cmd += ' key {0}'.format(server_dict['key_id'])
                    commands.append(cmd)

        source = dict(diff).get('source')
        if source != None:
            for each in source:
                source_dict = dict([each])
                if source_dict.get('ipv4'):
                    commands.append(
                        'sntp source ipv4 address {0}'.format(source_dict['ipv4']))
                if source_dict.get('ipv6'):
                    commands.append(
                        'sntp source ipv6 address {0}'.format(source_dict['ipv6']))

        return commands

    def _delete_config(self, want, have):
        commands = []
        count = 0

        if want.get('auth') != None:
            count += 1
            if have.get('auth'):
                commands.append('no sntp authenticate')

        if want.get('auth_key') != None:
            for auth_key in want.get('auth_key'):
                count += 1
                for each in have.get('auth_key'):
                    if each.get('id') and each.get('id') == auth_key.get('id'):
                        commands.append(
                            'no sntp authentication-key {0}'.format(auth_key.get('id')))

        if want.get('client') != None:
            count += 1
            if have.get('client'):
                commands.append('no sntp client')

        if want.get('max_poll') != None:
            count += 1
            if have.get('max_poll'):
                commands.append('no sntp max-poll')

        if want.get('min_poll') != None:
            count += 1
            if have.get('min_poll'):
                commands.append('no sntp min-poll')

        if want.get('server') != None:
            for server in want.get('server'):
                count += 1
                for each in have.get('server'):
                    if each.get('address') and each.get('address') == server.get('address'):
                        cmd = 'no sntp server {0}'.format(
                            server.get('address'))
                        if each.get('key_id') and server.get('key_id'):
                            cmd += ' key'
                        commands.append(cmd)

        if want.get('source') != None:
            for source in want.get('source'):
                count += 1
                if 'ipv4' in source:
                    commands.append('no sntp server ipv4')
                if 'ipv6' in source:
                    commands.append('no sntp server ipv6')

        if count == 0:
            commands.append('no sntp')

        return commands
