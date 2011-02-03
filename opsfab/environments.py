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
    env.chef_roles = ["production"]

def web():
    production()
    env.chef_roles.append("app_server")
    env.security_groups.extend(["web"])

def support():
    production()
    env.chef_roles.append("support_server")
    env.security_groups.extend(["support"])
