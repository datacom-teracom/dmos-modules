#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The dmos_linkagg class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.dmos.facts.facts import Facts
from ansible.module_utils.network.dmos.utils.utils import dict_to_set
from ansible.module_utils.network.dmos.utils.dict_differ import DictDiffer


class Linkagg(ConfigBase):
    """
    The dmos_linkagg class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'linkagg',
    ]

    def __init__(self, module):
        super(Linkagg, self).__init__(module)

    def get_linkagg_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
        linkagg_facts = facts['ansible_network_resources'].get('linkagg')
        if not linkagg_facts:
            return []
        return linkagg_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        existing_linkagg_facts = self.get_linkagg_facts()
        commands.extend(self.set_config(existing_linkagg_facts))
        if commands:
            if not self._module.check_mode:
                response = self._connection.edit_config(commands)
                result['response'] = response['response']
                if response.get('error'):
                    self._module.fail_json(msg=response['error'])
            result['changed'] = True
        result['commands'] = commands

        changed_linkagg_facts = self.get_linkagg_facts()

        result['before'] = existing_linkagg_facts
        if result['changed']:
            result['after'] = changed_linkagg_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_linkagg_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_linkagg_facts
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
            if have:
                commands.extend(self._set_config(want[0], have[0]))
            else:
                commands.extend(self._set_config(want[0], dict()))
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
                if have:
                    for each in have:
                        commands.extend(self._delete_config(config, each))
        else:
            commands.extend(self._delete_config(dict(), dict()))
        return commands

    def _set_config(self, want, have):
        # Set the interface config based on the want and have config
        commands = []

        differ = DictDiffer(have, want, {'lag_id': 0, 'name': 1})
        dict_diff = differ.deepdiff()

        sys_prio = dict_diff.get('sys_prio')
        if sys_prio != None:
            commands.append(
                'link-aggregation system-priority {0}'.format(sys_prio))

        lag = dict_diff.get('lag')
        if lag != None:
            for each_lag in lag:
                commands.extend(self._get_lag_commands(each_lag))

        return commands

    def _get_lag_commands(self, diff_dict):
        commands = []

        lag_id = diff_dict.get('lag_id')

        admin_status = diff_dict.get('admin_status')
        if admin_status != None:
            commands.append(
                'link-aggregation interface lag {0} administrative-status {1}'.format(lag_id, admin_status))

        description = diff_dict.get('description')
        if description != None:
            commands.append(
                'link-aggregation interface lag {0} description {1}'.format(lag_id, description))

        interface = diff_dict.get('interface')
        if interface != None:
            for each_interface in interface:
                commands.extend(self._get_interface_commands(
                    each_interface, lag_id))

        load_balance = diff_dict.get('load_balance')
        if load_balance != None:
            commands.append(
                'link-aggregation interface lag {0} load-balance {1}'.format(lag_id, load_balance))

        max_active = diff_dict.get('max_active')
        if max_active != None:
            commands.append(
                'link-aggregation interface lag {0} maximum-active links {1}'.format(lag_id, max_active))

        min_active = diff_dict.get('min_active')
        if min_active != None:
            commands.append(
                'link-aggregation interface lag {0} minimum-active links {1}'.format(lag_id, min_active))

        mode = diff_dict.get('mode')
        if mode != None:
            commands.append(
                'link-aggregation interface lag {0} mode {1}'.format(lag_id, mode))

        period = diff_dict.get('period')
        if period != None:
            commands.append(
                'link-aggregation interface lag {0} period {1}'.format(lag_id, period))

        return commands

    def _get_interface_commands(self, diff_dict, lag_id):
        intf_name = diff_dict.get('name')
        cmd = 'link-aggregation interface lag {0} interface {1}'.format(
            lag_id, intf_name)

        port_prio = diff_dict.get('port_prio')
        if port_prio != None:
            cmd += ' port-priority {0}'.format(port_prio)

        return [cmd]

    def _delete_config(self, want, have):
        commands = []
        count = 0

        if want.get('sys_prio') != None:
            count += 1
            if have.get('sys_prio') != None:
                commands.append('no link-aggregation system-priority')

        if want.get('lag') != None:
            for each_want_lag in want.get('lag'):
                count += 1
                if have.get('lag') != None:
                    for each_have_lag in have.get('lag'):
                        if each_want_lag.get('lag_id') and each_want_lag.get('lag_id') == each_have_lag.get('lag_id'):
                            commands.extend(self._delete_lag_config(
                                each_want_lag, each_have_lag))

        if count == 0:
            commands.append('no link-aggregation')

        return commands

    def _delete_lag_config(self, want, have):
        commands = []
        count = 0

        if want.get('lag_id') != None:
            lag_id = want.get('lag_id')
        else:
            return commands

        if want.get('admin_status') != None:
            count += 1
            if have.get('admin_status') != None:
                commands.append(
                    'no link-aggregation interface lag {0} administrative-status'.format(lag_id))

        if want.get('description') != None:
            count += 1
            if have.get('description') != None:
                commands.append(
                    'no link-aggregation interface lag {0} description'.format(lag_id))

        if want.get('interface') != None:
            count += 1
            for each_want_interface in want.get('interface'):
                if have.get('interface') != None:
                    for each_have_interface in have.get('interface'):
                        if each_want_interface.get('name') and each_want_interface.get('name') == each_have_interface.get('name'):
                            commands.extend(self._delete_interface_config(
                                each_want_interface, each_have_lag, lag_id))

        if want.get('load_balance') != None:
            count += 1
            if have.get('load_balance') != None:
                commands.append(
                    'no link-aggregation interface lag {0} load-balance'.format(lag_id))

        if want.get('max_active') != None:
            count += 1
            if have.get('max_active') != None:
                commands.append(
                    'no link-aggregation interface lag {0} maximum-active'.format(lag_id))

        if want.get('min_active') != None:
            count += 1
            if have.get('min_active') != None:
                commands.append(
                    'no link-aggregation interface lag {0} minimum-active'.format(lag_id))

        if want.get('mode') != None:
            count += 1
            if have.get('mode') != None:
                commands.append(
                    'no link-aggregation interface lag {0} mode'.format(lag_id))

        if want.get('period') != None:
            count += 1
            if have.get('period') != None:
                commands.append(
                    'no link-aggregation interface lag {0} period'.format(lag_id))

        if count == 0:
            commands.append(
                'no link-aggregation interface lag {0}'.format(lag_id))

        return commands

    def _delete_interface_config(self, want, have, lag_id):
        commands = []

        if want.get('name') != None:
            cmd = 'no link-aggregation interface lag {0} interface {1}'.format(
                lag_id, want.get('name'))
        else:
            return commands

        if want.get('port_prio') != None:
            if have.get('port_prio') != None:
                cmd += ' port-priority {0}'.format(want.get('port_prio'))
                commands.append(cmd)

        return commands
