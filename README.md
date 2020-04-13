Dmos Ansible basic tests

To run:

- Setup env, using Datacom repo, original ansible doc: https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#environment-setup
  1 - Clone ansible https://github.com/datacom-teracom/ansible.git
  2 - Change directory into the repository root dir: $ cd ansible
  3 - Create a virtual environment: $ python3 -m venv venv (or for Python 2 $ virtualenv venv. Note, this requires you to install the virtualenv package: $ pip install virtualenv)
  4 - Activate the virtual environment: $ . venv/bin/activate
  5 - Install development requirements: $ pip install -r requirements.txt
  6 - Run the environment setup script for each new dev shell process: $ . hacking/env-setup

- Clone https://github.com/datacom-teracom/dmos-modules.git
- Change directory into the repository root dir: $ cd dmos-modules
- At the setup env, run ansible:
 (venv) User@Host:~/ansible/dmos-modules$ ansible-playbook basic_test.yml

