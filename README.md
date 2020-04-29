Dmos Ansible basic tests

## Install Collection

### Install collection from ansible-galaxy

```bash
ansible-galaxy collection install datacom.dmos
```

### Install collection from source code

```bash
git clone https://github.com/datacom-teracom/ansible_collections.dmos.git
cd ansible_collections.dmos
ansible-galaxy collection build
ansible-galaxy collection install datacom-dmos-*.tar.gz
```

### Verify installation

```bash
ansible-doc datacom.dmos.dmos_vlan
```


## To run tests:

Cofigure switch ip and lag capacity in hosts file

Execute tests:
```bash
User@Host:~/dmos-modules$ ansible-playbook basic_test.yml
```
