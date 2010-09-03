"""
Definitions of available server environments.
"""
#!/usr/bin/env python
from fabric.api import env

from fab_shared import (development as shared_development,
        production as shared_production)

def development():
    """ Sets roles for development server. """
    shared_development()
    env.security_groups = ["development", "ssh"]
    env.key_name = "development"
    env.chef_roles = ["dev"]

def production():
    """ Sets roles for production servers behind load balancer. """
    shared_production()
    env.security_groups = ["ssh", "database-client"]
    env.key_name = "production"

def lace():
    production()
    env.chef_roles = ["lace"]
    env.security_groups.extend(["lace"])

def web():
    production()
    env.chef_roles = ["company", "five"]
    env.security_groups.extend(["web", "five"])

def api():
    production()
    env.chef_roles = ["api"]
    env.security_groups.extend(["api"])

