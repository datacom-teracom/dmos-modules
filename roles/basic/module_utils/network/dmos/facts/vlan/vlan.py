#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The dmos vlan fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import json
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.dmos.argspec.vlan.vlan import VlanArgs
from ansible.module_utils.network.dmos.utils.utils import get_arg_from_cmd_line
from ansible.module_utils.network.dmos.utils.utils import get_vlan_id_list


class VlanFacts(object):
    """ The dmos vlan fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = VlanArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for vlan
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get(
                'show running-config dot1q | details | nomore | display json')

        objs = []
        try:
            data_dict = json.loads(data)['data']
            data_list = data_dict['vlan-manager:dot1q']['vlan']
        except:
            pass
        else:
            for each in data_list:
                obj = self.render_config(self.generated_spec, each)
                if obj:
                    objs.append(obj)

        facts = {}
        if objs:
            params = utils.validate_config(
                self.argument_spec, {'config': objs})
            facts['vlan'] = params['config']

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        config['vlan_id'] = conf.get('vlan-id')
        config['name'] = conf.get('name')

        interface_value = conf.get('interface')
        if interface_value != None:
            interface = []
            for each in interface_value:
                each_interface = dict()
                each_interface['name'] = each.get('interface-name')
                tagged = each.get('tagged-untagged')
                if tagged != None:
                    each_interface['tagged'] = True if tagged == 'tagged' else False
                interface.append(each_interface)
            config['interface'] = interface

        return utils.remove_empties(config)
