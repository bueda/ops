"""
Fabfile for deploying instances with Chef to EC2.
"""
#!/usr/bin/env python
import os
import time
from fabric.api import env, require, runs_once

import opsfab.defaults
from opsfab.types import *
from opsfab.environments import *
from fab_shared import local, put, sudo, rechef, setup

env.root_dir = os.path.abspath(os.path.dirname(__file__))
env.pip_requirements = ["pip-requirements.txt",]

@runs_once
def spawn(ami=None, region=None, chef_roles=None):
    """ Create a new server instance, which will bootstrap itself with Chef. """
    require('ami', provided_by=[small, large, extra_large, extra_large_mem,
            double_extra_large_mem, quadruple_extra_large_mem, medium_cpu,
            extra_large_cpu])
    require('instance_type')
    require('region')
    require('security_groups')
    require('key_name')
    require('ec2_connection')

    env.ami = ami or env.ami
    env.region = region or env.region

    role_string = ""
    if chef_roles:
        env.chef_roles.extend(chef_roles.split('-'))
    for role in env.chef_roles:
        role_string += "role[%s] " % role

    local('ssh-add ~/.ssh/%(key_name)s.pem' % env)

    command = 'knife ec2 server create %s ' % role_string
    command += '-Z %(region)s ' % env
    command += '-f %(instance_type)s -i %(ami)s ' % env
    command += '-G %s ' % ','.join(env.security_groups)
    command += '-S %(key_name)s ' % env
    command += '-x ubuntu '

    print "Run this command to spawn the server:\n"
    print command
