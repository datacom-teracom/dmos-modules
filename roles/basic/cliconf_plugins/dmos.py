from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import time
import json

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.network.common.config import dumps
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_config(self):
        config_cmd = 'show running-config | details | display curly-braces | nomore'
        out = self.send_command(config_cmd)

        ret = out.split("\n")

        cmds = []
        while(len(ret)):
            cmd = ""
            discart_command = True
            for i, word in enumerate(ret, 0):
                cmd += word
                if word == "":
                    ret.pop(i)
                    break

                if ";" in word:
                    ret.pop(i)
                    discart_command = False
                    break

                if "}" in word:
                    ret.pop(i)
                    for j in range(i - 1, -1, -1):
                        if "{" in ret[j]:
                            ret.pop(j)
                            break
                    break

            if not discart_command:
                cmd = cmd.replace("{", "").replace(";", "").replace("}", "")
                cmd = re.sub(' +', ' ', cmd)
                cmds.append(cmd)

        return cmds

    def get_diff(self, candidates=None):
        out = []
        if candidates:
            configs = self.get_config()

            for candidate in candidates:
                command = re.sub(' +', ' ', candidate)

                its_no = False
                if command.split()[0] == "no":
                    its_no = True
                    command = command.replace("no ", "")

                contains = False
                for config in configs:
                    if command in config:
                        contains = True
                        break

                if contains:
                    if its_no:
                        out.append("no " + command)
                else:
                    if not its_no:
                        out.append(command)

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
        result['rpc'] += ['get_diff', 'run_commands']
        result['device_operations'] = self.get_device_operations()
        result.update(self.get_option_values())
        return json.dumps(result)

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
