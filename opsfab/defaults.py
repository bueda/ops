"""
Environment defaults for ops deployment fabfile.
"""
#!/usr/bin/env python
from fabric.api import env

env.unit = "chef"
env.scm = "git@github.com:bueda/chef"

env.security_groups = ["temporary", "ssh"]
env.key_name = "temporary"
env.region = 'us-east-1b'
env.chef_roles = ["base"]
