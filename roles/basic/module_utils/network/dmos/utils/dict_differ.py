from ansible.module_utils.six import iteritems
from copy import deepcopy


class DictDiffer():
    _AUXILIARY_KEY = 'AUXILIARY_KEY'

    def __init__(self, base, comparable, config_keys={}):
        if isinstance(base, list) and isinstance(comparable, list):
            self._is_list = True
            self._base = deepcopy(self._add_aux_key(base))
            self._comparable = deepcopy(self._add_aux_key(comparable))
        elif isinstance(base, dict) and isinstance(comparable, dict):
            self._is_list = False
            self._base = deepcopy(base)
            self._comparable = deepcopy(comparable)
        else:
            raise AssertionError(
                "invalid or incompatible types of base and comparable")

        self._config_keys = config_keys

    def _add_aux_key(self, raw_list):
        list_dict = dict()
        list_dict[self._AUXILIARY_KEY] = raw_list if raw_list != None else []
        return list_dict

    def _del_aux_key(self, raw_dict):
        aux_key = raw_dict.get(self._AUXILIARY_KEY)
        return aux_key if aux_key != None else []

    def _transform(self, config, level=0):
        if isinstance(config, dict):
            for key, value in iteritems(config):
                aux = {}
                if isinstance(value, list):
                    if len(value) and not isinstance(value[0], dict):
                        aux = value
                    else:
                        for i in range(len(value)):
                            common_keys = set(
                                self._config_keys) & set(value[i])
                            for k in common_keys:
                                if self._config_keys[k] == level:
                                    aux['id__{}__{}'.format(
                                        k, value[i][k])] = value[i]
                    value = aux
                    config[key] = value
                if isinstance(value, dict):
                    for sub_key in value:
                        self._transform(value[sub_key], level=level+1)

    def _dict_diff(self, base, comparable):
        if not isinstance(base, dict):
            raise AssertionError("`base` must be of type <dict>")
        if not isinstance(comparable, dict):
            raise AssertionError("`comparable` must be of type <dict>")

        updates = dict()

        for key, value in iteritems(base):
            if isinstance(value, dict):
                item = comparable.get(key)
                if item is not None:
                    sub_diff = self._dict_diff(value, comparable[key])
                    if sub_diff:
                        updates[key] = sub_diff
            elif isinstance(value, list):
                updates[key] = list(
                    set(comparable.get(key)) - set(base.get(key)))
            else:
                comparable_value = comparable.get(key)
                if comparable_value is not None:
                    if base[key] != comparable_value:
                        updates[key] = comparable_value

        for key in set(comparable.keys()).difference(base.keys()):
            updates[key] = comparable.get(key)

        return updates

    def _untransform(self, config):
        if isinstance(config, dict):
            for key, value in iteritems(config):
                if isinstance(value, dict):
                    splitted_key = next(iter(value)).split('__', 2)
                    if len(splitted_key) == 3 and splitted_key[0] == 'id':
                        aux = []
                        for k, v in iteritems(value):
                            splitted_key = k.split('__', 2)
                            if v.get(splitted_key[1]) is None:
                                v.update({splitted_key[1]: splitted_key[2]})
                            aux.append(v)
                        value = aux
                        config[key] = value
                        for i in range(len(value)):
                            self._untransform(value[i])
                    self._untransform(value)

    def deepdiff(self):
        if not self._comparable:
            return {}
        if not self._base:
            return self._comparable
        self._transform(self._base)
        self._transform(self._comparable)
        diff = self._dict_diff(self._base, self._comparable)
        self._untransform(diff)
        if self._is_list:
            return self._del_aux_key(diff)
        return diff
