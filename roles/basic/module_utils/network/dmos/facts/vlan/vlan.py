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
import re
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
                'show running-config dot1q | details | nomore')

        keys = re.findall("[^'\"]vlan\s.*[^'\"]\n", data)
        values = re.compile("[^'\"]vlan\s.*[^'\"]\n").split(data)
        values.remove('dot1q\n')

        objs = []
        if len(keys) == len(values):
            for i in range(len(keys)):
                vlan_id = get_arg_from_cmd_line(keys[i], 'vlan')
                vlan_id_list = get_vlan_id_list(vlan_id)
                for id in vlan_id_list:
                    obj = self.render_config(
                        self.generated_spec, str(id) + "\n" + values[i])
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
        got_id = False
        for line in conf.split('\n'):
            if not got_id:
                config['vlan_id'] = int(line)
                got_id = True
            if 'untagged' in line:
                config['interface']['tagged'] = False
                continue
            if 'interface' in line:
                config['interface']['name'] = get_arg_from_cmd_line(
                    line, 'interface')
                continue
            if 'name' in line:
                config['name'] = get_arg_from_cmd_line(line, 'name')
                continue
        if config['interface']['tagged'] == None:
            config['interface']['tagged'] = True

        return utils.remove_empties(config)
