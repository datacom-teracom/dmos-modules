#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The dmos linkagg fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import json
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.dmos.argspec.linkagg.linkagg import LinkaggArgs
from ansible.module_utils.network.dmos.utils.utils import get_arg_from_cmd_line

class LinkaggFacts(object):
    """ The dmos linkagg fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = LinkaggArgs.argument_spec
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
        """ Populate the facts for linkagg
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = connection.get(
                'show running-config link-aggregation | details | nomore | display json')

        objs = []
        try:
            data_dict = json.loads(data)['data']
            data_list = [data_dict['lacp:link-aggregation']]
        except:
            pass
        else:
            for each in data_list:
                obj = self.render_config(self.generated_spec, each)
                if obj:
                    objs.append(obj)

        facts = {}
        if objs:
            params = utils.validate_config(self.argument_spec, {'config': objs})
            facts['linkagg'] = params['config']

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

        system = conf.get('system')
        if system != None:
            config['sys_prio'] = system.get('priority')

        interface = conf.get('interface')
        if interface != None:
            lag = interface.get('lag')
            if lag != None:
                lag_list = []
                for each in lag:
                    each_lag = dict()
                    each_lag['lag_id'] = each.get('lag-id')
                    each_lag['admin_status'] = each.get('administrative-status')

                    lag_config = each.get('interface-lag-config')
                    if lag_config != None:
                        each_lag['description'] = lag_config.get('description')
                        each_lag['load_balance'] = lag_config.get('load-balance')
                        each_lag['mode'] = lag_config.get('mode')
                        each_lag['period'] = lag_config.get('period')

                    lag_link = each.get('lag')
                    if lag_link != None:
                        max_active = lag_link.get('maximum-active')
                        if max_active != None:
                            each_lag['max_active'] = max_active.get('links')
                        min_active = lag_link.get('minimum-active')
                        if min_active != None:
                            each_lag['min_active'] = min_active.get('links')

                    intf_config = each.get('interface-config')
                    if intf_config != None:
                        intf_config_list = []
                        for each_intf_config in intf_config:
                            intf_config_dict = dict()
                            intf_config_dict['name'] = each_intf_config.get('interface-name')
                            intf_config_dict['port_prio'] = each_intf_config.get('port-priority')
                            intf_config_list.append(intf_config_dict)
                        each_lag['interface'] = intf_config_list

                    lag_list.append(each_lag)
                config['lag'] = lag_list

        return utils.remove_empties(config)
