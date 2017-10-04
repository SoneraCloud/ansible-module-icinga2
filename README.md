# ansible-module-icinga2

Prototype ansible module for icinga2. Supports adding zones, endpoints, hosts and services ... you know so you can actually monitor something.

This was the result of a fustrating experience to automate adding hosts to icinga2 using Ansible. If I had to do this again I wouldn't use Icinga2, or I would use the Icinga2 Director API. In either case this code will be mostly useless!

The code relies on a branch of our fork of `python-icinga2api`: https://github.com/SoneraCloud/python-icinga2api/tree/config-mode

See the role `icinga2-client` role in this repo for an example of how to use this module.

We use the following icinga2 roles (`requirements.yml` syntax), only the client one is required for this code, but maybe this helps others.

```
# Icinga role for clients
- src: https://github.com/SoneraCloud/ansible-icinga2-client.git

# Icinga roles for server
- src: https://github.com/SoneraCloud/ansible-role-icinga2-no-ui.git
- src: https://github.com/SoneraCloud/ansible-role-icinga2-web2-ui.git
# MariaDB for Icingaweb2
- src: https://github.com/SoneraCloud/ansible-role-mariadb.git
  version: MDEV-11789 # Fix for selinux bug
```
