#!/usr/bin/python
import json
from ansible.module_utils.basic import AnsibleModule
import os

def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        folder=dict(type='str', required=True),
        state=dict(choises=['present','absent'], default='present'),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    folder = module.params['folder']
    state = module.params['state']

    result = {'changed': False}

    if state == 'present':
        ret = os.system('ls ' + folder)
        if ret == 0:
            module.exit_json(**result)
        else:
            os.system('mkdir ' + folder)
            result['changed'] = True
            module.exit_json(**result)
    elif state == 'absent':
        ret = os.system('ls ' + folder)
        if ret == 0:
            os.system('rm -rf ' + folder)
            result['changed'] = True
            module.exit_json(**result)
        else:
            module.exit_json(**result)

    msg = 'Invalid state value'
    module.fail_json(msg=msg)

if __name__ == '__main__':
    main()
