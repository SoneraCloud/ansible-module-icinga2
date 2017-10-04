#!/usr/bin/env python
# This let's you test the icinga2api library from an interactive shell
# it's helpful for testing what works (not much!).
import icinga2api.client
import bpdb
client = icinga2api.client.Client('https://localhost:5665','director','')
c = client.objects
# Break out to the bpython interpretor
bpdb.set_trace()
