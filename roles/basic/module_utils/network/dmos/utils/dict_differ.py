from ansible.module_utils.six import iteritems
from ansible.module_utils.common.network import utils
from copy import deepcopy

class DictDiffer():
    def __init__(base, comparable, config_keys):
        self._base = deepcopy(base)
        self._comparable = deepcopy(comparable)
        self._config_keys = config_keys
        
    def _transform(self, config, level=0):
        if not isinstance(config, dict):
            raise AssertionError("`config` must be of type <dict>")
        if isinstance(config, dict):
            for key, value in iteritems(config):
                aux = {}
                if isinstance(value, list):
                    for i in range(len(value)):
                        common_keys = set(self._config_keys) & set(value[i])
                        for k in common_keys:
                            if self._config_keys[k] == level:
                                aux['id__{}__{}'.format(k, value[i][k])] = value[i]
                    value = aux
                    config[key] = value
                if isinstance(value, dict):
                    for sub_key in value:
                        transform(value[sub_key], level=level+1)
                        
    def _untransform(self, config):
        if isinstance(config, dict):
            for key, value in iteritems(config):
                if isinstance(value, dict):
                    splitted_key = next(iter(value)).split('__', 2)
                    if len(splitted_key) == 3 and splitted_key[0] == 'id':
                        for v in value.values():
                            if v.get(splitted_key[1]) is None:
                                v.update({splitted_key[1]:splitted_key[2]})
                        value = value.values()
                        config[key] = value
                        for i in range(len(value)):
                            untransform(value[i])
                    untransform(value)
    
    def deepdiff(self):
        self._transform(self._base)
        self._transform(self._comparable)
        diff = utils.dict_diff(self._base, self._comparable)
        self._untransform(diff)
        return diff