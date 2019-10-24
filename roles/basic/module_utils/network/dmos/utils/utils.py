#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import re
from ansible.module_utils.six import iteritems


def dict_has_key(dict, key):
    return True if key in dict else False


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
