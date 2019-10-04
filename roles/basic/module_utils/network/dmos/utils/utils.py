#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import re
from ansible.module_utils.six import iteritems


def dict_to_set(sample_dict):
    # Generate a set with passed dictionary for comparison
    test_dict = {}
    if isinstance(sample_dict, dict):
        for k, v in iteritems(sample_dict):
            if v is not None:
                if isinstance(v, list):
                    if isinstance(v[0], dict):
                        li = []
                        for each in v:
                            for key, value in iteritems(each):
                                if isinstance(value, list):
                                    each[key] = tuple(value)
                            li.append(tuple(iteritems(each)))
                        v = tuple(li)
                    else:
                        v = tuple(v)
                elif isinstance(v, dict):
                    li = []
                    for key, value in iteritems(v):
                        if isinstance(value, list):
                            v[key] = tuple(value)
                    li.extend(tuple(iteritems(v)))
                    v = tuple(li)
                test_dict.update({k: v})
        return_set = set(tuple(iteritems(test_dict)))
    else:
        return_set = set(sample_dict)
    return return_set


def get_arg_from_cmd_line(line, key):
    if key in line:
        value = line.split(key)[-1]
        return value.split()[0]
    return None


def get_command_list_from_curly_braces(output):
    ret = output.split("\n")

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


def get_command_list_diff(configs, candidates=None):
    out = []
    if candidates:
        for candidate in candidates:
            command = re.sub(' +', ' ', candidate)

            its_no = False
            if command.split()[0] == "no":
                its_no = True
                command = command.replace("no ", "")

            contains = True
            for config in configs:
                contains = True
                for word in command.split():
                    if word not in config:
                        contains = False
                        break
                if contains:
                    break

            if contains:
                if its_no:
                    out.append("no " + command)
            else:
                if not its_no:
                    out.append(command)

    return out
