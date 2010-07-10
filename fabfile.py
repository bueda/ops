"""
Fabfile for deploying instances with Chef to EC2.
"""
#!/usr/bin/env python
import os
from fabric.api import env, require, runs_once
from fab_shared import (_development, _production, TIME_NOW,
        _upload_to_s3, local, put, sudo, elb_add, elb_remove)
import time

env.region = 'us-east-1b'
env.user_data = "/tmp/chef.user-data-%s" % TIME_NOW

env.unit = "chef"
env.scm = "git@github.com:bueda/chef"
env.root_dir = os.path.abspath(os.path.dirname(__file__))

env.security_groups = ["temporary", "ssh"]
env.chef_roles = ["base"]
env.key_name = "temporary"

def _32bit():
    """ Ubuntu Lucid 10.04 32-bit, Opscode Chef AMI for Chef 0.8.x """
    env.ami = "ami-2d4aa444"

def _64bit():
    """ Ubuntu Lucid 10.04 64-bit, Opscode Chef AMI for Chef 0.8.x """
    env.ami = "ami-fd4aa494"

def small():
    """ Small Instance, 1.7GB, 1 CPU (32-bit) """
    _32bit()
    env.instance_type = 'm1.small'

def large():
    """ Large Instance, 7.5GB, 4 CPU (64-bit) """
    _64bit()
    env.instance_type = 'm1.large'

def extra_large():
    """ Extra Large Instance, 16GB, 8 CPU (64-bit) """
    _64bit()
    env.instance_type = 'm1.xlarge'

def extra_large_mem():
    """ High-Memory Extra Large Instance, 17.1GB, 6.5 CPU (64-bit) """
    _64bit()
    env.instance_type = 'm2.xlarge'

def double_extra_large_mem():
    """ High-Memory Double Extra Large Instance, 34.2GB, 13 CPU (64-bit) """
    _64bit()
    env.instance_type = 'm2.2xlarge'

def quadruple_extra_large_mem():
    """ High-Memory Quadruple Extra Large Instance, 68.4GB, 26 CPU (64-bit) """
    _64bit()
    env.instance_type = 'm2.4xlarge'

def medium_cpu():
    """ High-CPU Medium Instance, 1.7GB, 5 CPU (32-bit) """
    _32bit()
    env.instance_type = 'c1.medium'

def extra_large_cpu():
    """ High-CPU Extra Large Instance, 7GB, 20 CPU (64-bit) """
    _64bit()
    env.instance_type = 'c1.xlarge'

def development():
    """ Sets roles for development server. """
    _development()
    env.security_groups = ["development", "ssh"]
    env.key_name = "development"
    env.chef_roles.extend(["web", "dev"])

def production():
    """ Sets roles for production servers behind load balancer. """
    _production()
    env.security_groups = ["production", "ssh", "database-client"]
    env.key_name = "production"
    env.chef_roles.extend(["web", "production"])

def deploy():
    """ Deploy the shared fabfile. """
    if len(env.hosts) > 0:
        print "Deploying shared fabfile..."
        put('fab_shared.py', '/tmp', mode=0755)
        sudo('mv /tmp/fab_shared.py /root')
        print "Deploying git-archive-all.sh..."
        put('git-archive-all.sh', '/tmp', mode=0755)
        sudo('mv /tmp/git-archive-all.sh /root')
    _upload_to_s3('fab_shared.py')

def rechef():
    """ Run the latest Chef cookbooks on all servers. """
    sudo('chef-client')

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

    _upload_to_s3('fab_shared.py')
    env.ami = ami or env.ami
    env.region = region or env.region

    role_string = ""
    if chef_roles:
        env.chef_roles.extend(chef_roles.split(','))
    for role in env.chef_roles:
        role_string += "role[%s] " % role

    local('ssh-add ~/.ssh/%(key_name)s.pem' % env)

    command = 'knife ec2 server create %s ' % role_string
    command += '-Z %(region)s ' % env
    command += '-A %(aws_access_key)s -K %(aws_secret_key)s ' % env
    command += '-f %(instance_type)s -i %(ami)s ' % env
    command += '-G %s ' % ','.join(env.security_groups)
    command += '-S %(key_name)s ' % env
    command += '-x ubuntu '

    print "Run this command to spawn the server:\n"
    print command
