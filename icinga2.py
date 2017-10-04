#!/usr/bin/env python

# Prototype ansible module for making changes to Icinga2 config using the API
# This code relies on a branch of our fork of icinga2api which can be found here:
#   https://github.com/SoneraCloud/python-icinga2api/tree/config-mode

# TODO: If we take this into use ansible documentation would be needed.

from ansible.module_utils.basic import AnsibleModule
import icinga2api.client
import inspect
import re
import json
import os
from jinja2 import Template

def connect_icinga2(params):
    return icinga2api.client.Client(params['server_url'],
                                    params['api_user'],
                                    params['api_password'])

# Call a python function with a dict of arguments
# The dict can contain excess values. This function only picks the supported ones
def call_python_function(module, function_name, argument_dictionary):
    funcpointer = getattr(module, function_name)
    # Find what arguments the module's function takes
    argspec = inspect.getargspec(funcpointer)
    # Remove the self that is a python self-reference
    argspec.args.remove('self')
    # argspec.args is now an empty list if the func doesn't take any arguments
    # Create a dictionary with the arguments taken from the passed data (if the key exists)
    args = {argname: argument_dictionary[argname] for argname in argspec.args if argname in argument_dictionary.keys()}
    # Call the command with the dictionary passed as arguments
    return funcpointer(**args)

def main():

    ansibleModule = AnsibleModule(
        argument_spec = dict(
            server_url      = dict(required=False,type='str'),
            api_user        = dict(required=False,type='str'),
            api_password    = dict(required=False,type='str'),
            objects         = dict(required=False,type='str'),
            actions         = dict(required=False,type='str'),
            events          = dict(required=False,type='str'),
            status          = dict(required=False,type='str'),
            args            = dict(required=False,type='dict'),
            add_host_zone_endpoint
                            = dict(required=False,type='dict')
        )
    )

    icinga2 = connect_icinga2(ansibleModule.params)

    changed = False
    failed = False
    result = {}

    # We either add host
    if ansibleModule.params['add_host_zone_endpoint']:
        changed, failed, result = add_host_zone_endpoint(icinga2, ansibleModule.params['add_host_zone_endpoint'])
    # Or pass arguments through to the api
    else:
        pkeys = ansibleModule.params.keys()
        args = ansibleModule.params['args'] if 'args' in pkeys and type(ansibleModule.params['args']) is dict else {}

        for command in ['objects', 'actions', 'events', 'status']:
            # Check if object/actions/events/status are given as args and check they are actually set
            # since when you set the argument_spec above unused keys are defined!
            if command in pkeys and ansibleModule.params[command]:
                commandObject = getattr(icinga2, command)
                try:
                    result = call_python_function(commandObject, ansibleModule.params[command], args)
                except icinga2api.client.Icinga2ApiException as e:
                    errorJSON = re.match('Request .* failed with status [0-9]+: ({.*})', e.message)
                    #errorJSON = re.match('.*({.*})', e.message)
                    error = json.loads(errorJSON.groups()[0])
                    # The API kind of sucks, so lets handle the common create vs update case
                    if command == 'objects' and ansibleModule.params[command] == 'update':
                        if error['status'] == "No objects found.":
                            result = call_python_function(commandObject, 'create', args)
                    elif command == 'objects' and ansibleModule.params[command] == 'create':
                        if error['results'][0]['status'] == "Object could not be created.":
                            result = call_python_function(commandObject, 'update', args)
                    else:
                        result = error
                        failed = True

                if command != 'status':
                    changed = True
    ansibleModule.exit_json(changed=changed, failed=failed, result=result)

def add_host_zone_endpoint(icinga2, args):
    '''
    Add zone and endpoint using config files since the API doesn't support this
    '''
    icinga2.config.create_package(args['fqdn'])
    files = {}
    zone_template = Template('''\
        object Zone "{{ fqdn }}" {
            parent = "{{ parent }}"
            endpoints = [ "{{ fqdn }}" ]
        }''')

    zone_file_name = 'zones.d/' + args['parent'] + '/zones.conf'
    files[zone_file_name] = zone_template.render(**args)

    endpoint_template = Template('''\
        object Endpoint "{{ fqdn }}" {
            host = "{{ host }}"
            port = "5665"
        }''')
    
    endpoints_file_name = 'zones.d/' + args['fqdn'] + '/endpoints.conf'
    files[endpoints_file_name] = endpoint_template.render(**args)
    
    # changed, failed, result
    return (True, False,
            icinga2.config.upload_package(args['fqdn'], files))

if __name__ == '__main__':
    main()
