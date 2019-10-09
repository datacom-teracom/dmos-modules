#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The dmos_vlan class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.dmos.facts.facts import Facts
from ansible.module_utils.network.dmos.utils.utils import dict_to_set


class Vlan(ConfigBase):
    """
    The dmos_vlan class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'vlan',
    ]

    def __init__(self, module):
        super(Vlan, self).__init__(module)

    def get_vlan_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
        vlan_facts = facts['ansible_network_resources'].get('vlan')
        if not vlan_facts:
            return []
        return vlan_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        existing_vlan_facts = self.get_vlan_facts()
        commands.extend(self.set_config(existing_vlan_facts))
        if commands:
            if not self._module.check_mode:
                response = self._connection.edit_config(commands)
                result['response'] = response['response']
            result['changed'] = True
        result['commands'] = commands

        changed_vlan_facts = self.get_vlan_facts()

        result['before'] = existing_vlan_facts
        if result['changed']:
            result['after'] = changed_vlan_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_vlan_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_vlan_facts
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
                if have:
                    present = False
                    for each in have:
                        if each['vlan_id'] == config['vlan_id']:
                            present = True
                            commands.extend(self._set_config(config, each))
                            break
                    if not present:
                        commands.extend(self._set_config(config, dict()))
                else:
                    commands.extend(self._set_config(config, dict()))
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
                    if each['vlan_id'] == config['vlan_id']:
                        commands.extend(self._delete_config(config, each))
                        break
        else:
            commands.extend(self._delete_config(dict(), dict()))
        return commands

    def _set_config(self, want, have):
        # Set the interface config based on the want and have config
        commands = []

        # Convert the want and have dict to set
        want_set = dict_to_set(want)
        have_set = dict_to_set(have)
        diff = want_set - have_set

        want_dict = dict(want_set)
        have_dict = dict(have_set)
        diff_dict = dict(diff)

        name = diff_dict.get('name')
        if name != None:
            commands.append('dot1q vlan {0} name {1}'.format(
                want.get('vlan_id'), name))

        if want.get('interface') != None:
            if have.get('interface') != None:
                interface = tuple(set(want_dict.get('interface')) -
                                 set(have_dict.get('interface')))
            else:
                interface = diff_dict.get('interface')

            if interface != None:
                for each in interface:
                    each = dict(each)
                    intf_name = each.get('name')
                    if intf_name != None:
                        cmd = 'dot1q vlan {0} interface {1}'.format(want.get('vlan_id'), intf_name)
                        tagged = each.get('tagged')
                        if tagged != None:
                            cmd += ' tagged' if tagged else ' untagged'
                        commands.append(cmd)

        return commands

    def _delete_config(self, want, have):
        # Set the interface config based on the want and have config
        commands = []

        if want.get('vlan_id') != None:
            if have.get('vlan_id'):
                count = 0

                if want.get('name') != None:
                    count += 1
                    if have.get('name'):
                        commands.append(
                            'no dot1q vlan {0} name'.format(want.get('vlan_id')))

                if want.get('interface') != None:
                    count += 1
                    if have.get('interface'):
                        if want.get('interface')['name'] != None:
                            cmd = 'no dot1q vlan {0} interface {1}'.format(
                                want.get('vlan_id'), want.get('interface')['name'])

                            if want.get('interface')['tagged'] != None:
                                cmd += ' tagged'
                            commands.append(cmd)

                if count == 0:
                    commands.append(
                        'no dot1q vlan {0}'.format(want.get('vlan_id')))
        else:
            commands.append('no dot1q')

        return commands
