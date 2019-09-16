import json
import ipaddress

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.connection import Connection, ConnectionError

_DEVICE_CONFIGS = {}

dmos_provider_spec = {
    'host': dict(),
    'port': dict(type='int'),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
    'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    'auth_pass': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS']), no_log=True),
    'timeout': dict(type='int')
}
dmos_argument_spec = {
    'provider': dict(type='dict', options=dmos_provider_spec),
}

dmos_top_spec = {
    'host': dict(removed_in_version=2.9),
    'port': dict(removed_in_version=2.9, type='int'),
    'username': dict(removed_in_version=2.9),
    'password': dict(removed_in_version=2.9, no_log=True),
    'ssh_keyfile': dict(removed_in_version=2.9, type='path'),
    'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    'auth_pass': dict(removed_in_version=2.9, no_log=True),
    'timeout': dict(removed_in_version=2.9, type='int')
}
dmos_argument_spec.update(dmos_top_spec)


def get_provider_argspec():
    return dmos_provider_spec


def get_connection(module):
    if hasattr(module, '_dmos_connection'):
        return module._dmos_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module._dmos_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._dmos_connection


def get_capabilities(module):
    if hasattr(module, '_dmos_capabilities'):
        return module._dmos_capabilities
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module._dmos_capabilities = json.loads(capabilities)
    return module._dmos_capabilities


def check_args(module, warnings):
    pass


def edit_config(module, candidates):
    connection = get_connection(module)
    try:
        return connection.edit_config(candidates=candidates)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def get_diff(module, candidates):
    connection = get_connection(module)
    try:
        return connection.get_diff(candidates=candidates)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)
    try:
        return connection.run_commands(commands=commands, check_rc=check_rc)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def validate_ip(address):
    try:
        ipaddress.ip_address(unicode(address))
        return True
    except:
        return False


def is_v4(address):
    return type(ipaddress.ip_address(unicode(address))) is ipaddress.IPv4Address
