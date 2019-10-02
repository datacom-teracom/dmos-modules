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
