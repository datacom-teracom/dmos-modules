from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import time
import json

from itertools import chain

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_config(self, command=None):
        if command:
            cmd = 'show running-config | details | display keypath '

            command = command.replace("-", " ")
            command = command.split(" ")

            its_no = False
            for word in command:
                if word == 'no':
                    its_no = True
                    continue
                cmd += '| include ' + word + ' '

            cmd += '| nomore'

            out = self.send_command(cmd)

            if its_no:
                if out:
                    return None
                else:
                    return command

        return out

    def edit_config(self, candidate=None, commit=True, replace=None, comment=None):
        resp = {}
        operations = self.get_device_operations()
        self.check_edit_config_capability(
            operations, candidate, commit, replace, comment)

        results = []
        requests = []
        if commit:
            self.send_command('config')
            for line in to_list(candidate):
                if not isinstance(line, Mapping):
                    line = {'command': line}

                cmd = line['command']
                if cmd != 'end' and cmd[0] != '!':
                    results.append(self.send_command(**line))
                    requests.append(cmd)

            self.send_command('commit')
            self.send_command('end')
        else:
            raise ValueError('check mode is not supported')

        resp['request'] = requests
        resp['response'] = results
        return resp

    def get(self, command=None, prompt=None, answer=None, sendonly=False, output=None, newline=True, check_all=False):
        if not command:
            raise ValueError('must provide value of command to execute')
        if output:
            raise ValueError(
                "'output' value %s is not supported for get" % output)

        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'dmos'
        reply = self.get(command='show platform')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Version (\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1).strip(',')

        model_search_strs = [
            r'^[Cc]isco (.+) \(revision', r'^[Cc]isco (\S+).+bytes of .*memory']
        for item in model_search_strs:
            match = re.search(item, data, re.M)
            if match:
                version = match.group(1).split(' ')
                device_info['network_os_model'] = version[0]
                break

        match = re.search(r'^(.+) uptime', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        match = re.search(r'image file is "(.+)"', data)
        if match:
            device_info['network_os_image'] = match.group(1)

        return device_info

    def get_device_operations(self):
        return {
            'supports_diff_replace': True,
            'supports_commit': False,
            'supports_rollback': False,
            'supports_defaults': True,
            'supports_onbox_diff': False,
            'supports_commit_comment': False,
            'supports_multiline_delimiter': True,
            'supports_diff_match': True,
            'supports_diff_ignore_lines': True,
            'supports_generate_diff': True,
            'supports_replace': False
        }

    def get_option_values(self):
        return {
            'format': ['text'],
            'diff_match': ['line', 'strict', 'exact', 'none'],
            'diff_replace': ['line', 'block'],
            'output': []
        }

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        result['rpc'] += ['edit_banner', 'get_diff',
                          'run_commands', 'get_defaults_flag']
        result['device_operations'] = self.get_device_operations()
        result.update(self.get_option_values())
        return json.dumps(result)

    def edit_banner(self, candidate=None, multiline_delimiter="@", commit=True):
        """
        Edit banner on remote device
        :param banners: Banners to be loaded in json format
        :param multiline_delimiter: Line delimiter for banner
        :param commit: Boolean value that indicates if the device candidate
               configuration should be  pushed in the running configuration or discarded.
        :param diff: Boolean flag to indicate if configuration that is applied on remote host should
                     generated and returned in response or not
        :return: Returns response of executing the configuration command received
             from remote host
        """
        resp = {}
        banners_obj = json.loads(candidate)
        results = []
        requests = []
        if commit:
            for key, value in iteritems(banners_obj):
                key += ' %s' % multiline_delimiter
                self.send_command('config', sendonly=True)
                for cmd in [key, value, multiline_delimiter]:
                    obj = {'command': cmd, 'sendonly': True}
                    results.append(self.send_command(**obj))
                    requests.append(cmd)

                self.send_command('end', sendonly=True)
                time.sleep(0.1)
                results.append(self.send_command('\n'))
                requests.append('\n')

        resp['request'] = requests
        resp['response'] = results

        return resp

    def run_commands(self, commands=None, check_rc=True):
        if commands is None:
            raise ValueError("'commands' value is required")

        responses = list()
        for cmd in to_list(commands):
            if not isinstance(cmd, Mapping):
                cmd = {'command': cmd}

            output = cmd.pop('output', None)
            if output:
                raise ValueError(
                    "'output' value %s is not supported for run_commands" % output)

            try:
                out = self.send_command(**cmd)
            except AnsibleConnectionFailure as e:
                if check_rc:
                    raise
                out = getattr(e, 'err', to_text(e))

            responses.append(out)

        return responses

    def get_defaults_flag(self):
        """
        The method identifies the filter that should be used to fetch running-configuration
        with defaults.
        :return: valid default filter
        """
        out = self.get('show running-config ? | nomore')
        out = to_text(out, errors='surrogate_then_replace')

        commands = set()
        for line in out.splitlines():
            if line.strip():
                commands.add(line.strip().split()[0])

        if 'all' in commands:
            return 'all'
        else:
            return 'full'

    def _extract_banners(self, config):
        banners = {}
        banner_cmds = re.findall(r'^banner (\w+)', config, re.M)
        for cmd in banner_cmds:
            regex = r'banner %s \^C(.+?)(?=\^C)' % cmd
            match = re.search(regex, config, re.S)
            if match:
                key = 'banner %s' % cmd
                banners[key] = match.group(1).strip()

        for cmd in banner_cmds:
            regex = r'banner %s \^C(.+?)(?=\^C)' % cmd
            match = re.search(regex, config, re.S)
            if match:
                config = config.replace(str(match.group(1)), '')

        config = re.sub(r'banner \w+ \^C\^C', '!! banner removed', config)
        return config, banners

    def _diff_banners(self, want, have):
        candidate = {}
        for key, value in iteritems(want):
            if value != have.get(key):
                candidate[key] = value
        return candidate
