#!/usr/bin/env python
import os
from fabric.api import env, abort, require, settings, runs_once, prompt, get
from fabric.contrib.console import confirm
from fab_shared import (_find_unit_root, _development, _production, _localhost,
        _clone, _make_release, TIME_NOW, _make_archive,
        _conditional_upload_to_s3, S3_KEY, local, put, run, sudo,
        EC2_CONNECTION, ELB_CONNECTION)
import time

env.unit = "chef"
env.user_data = "deployment/chef.user-data"
env.scm = "git@github.com:bueda/chef"
env.root_dir = _find_unit_root(os.path.abspath(os.path.dirname(__file__)))

env.scratch_path = '/tmp/%s-%s' % (env.unit, TIME_NOW)

def development():
    """
    [Env] Sets environment for development server.
    """
    _development()
    env.tagged = False
    env.security_groups = ["development", "ssh", "database-client"]
    env.key_name = "development"
    env.chef_configs = ["common", "common-web", "dev", "lda", "solr"]

def production():
    """
    [Env] Sets environment for production servers behind load balancer.
    """
    _production()
    env.tagged = False
    env.security_groups = ["production", "ssh", "database-client"]
    env.key_name = "production"
    env.chef_configs = ["common", "common-web", "production"]

def localhost():
    """
    [Env] Sets environment for this machine, without using SSH.
    """
    _localhost()
    env.tagged = False
    env.chef_configs = ["common", "common-web", "dev", "lda", "solr"]

def deploy(release=None):
    """
    Deploy a specific commit, tag or HEAD to all servers and/or S3.
    """
    require('hosts', provided_by = [development, production])
    require('unit')

    deploy_fabfile()

    _clone(release)
    _make_release(release)
    require('pretty_release')
    require('archive')
    if test(env.scratch_path):
        abort("Unit tests did not pass")
    require('pretty_release')

    _conditional_upload_to_s3()
    if confirm("Re-Chef?", default=True):
        rechef(release=env.release)

def deploy_fabfile():
    require('hosts', provided_by = [development, production])
    print "Deploying shared fabfile..."
    put('fab_shared.py', '/tmp', mode=0755)
    sudo('mv /tmp/fab_shared.py /root')
    _conditional_upload_to_s3('fab_shared.py')


def rechef(release=None):
    """
    Run the latest commit of the Chef cookbook on all servers.
    """
    require('chef_configs', provided_by=[development, production])
    require('tagged')
    archive_path = '/tmp/chef-%s.tar.gz' % TIME_NOW
    if (not env.tagged and
            confirm("Re-chef with production cookbook?", default=True)):
        S3_KEY.key = '%(unit)s.tar.gz' % env
        S3_KEY.get_contents_to_filename('/tmp/%(unit)s.tar.gz' % env)
    else:
        if not release:
            env.release = prompt("Chef commit or tag?", default='HEAD')
        _clone()
        _make_archive()
        require('scratch_path')
        require('archive')
        local('mv %s/%s %s' % (env.scratch_path, env.archive, archive_path))
    put(archive_path, '/tmp', mode=0777)
    run('tar -xzf %s -C /tmp' % archive_path)
    _run_chef_solo('base')
    for config in env.chef_configs:
        _run_chef_solo(config)
    run('rm -rf /tmp/%(unit)s' % env)

def _run_chef_solo(config):
    env.config = config
    with settings(warn_only=True):
        result = sudo("""
            cd /tmp/%(unit)s;
            /var/lib/gems/1.8/bin/chef-solo \
                -j /tmp/%(unit)s/config/%(config)s.json \
                -c /tmp/%(unit)s/config/solo.rb
            """ % env)
    if result.failed:
        abort("Chef run failed, %s" % result)

@runs_once
def spawn_ec2_instance():
    """
    Create a new server instance, different for each environment.
    """
    require('ami', provided_by=[production, development])
    require('region', provided_by=[production, development])
    require('user_data', provided_by=[production, development])
    require('security_groups', provided_by=[production, development])
    require('key_name', provided_by=[production, development])
    print "Launching instance with image %s" % env.ami

    image = EC2_CONNECTION.get_image(env.ami)
    print "Found AMI image image %s" % image

    user_data_file = open(env.user_data, "rb").read()
    instance = image.run(security_groups=env.security_groups,
            user_data=user_data_file,
            key_name=env.key_name).instances[0]
    print "%s created" % instance
    time.sleep(5)

    while instance.update() != 'running':
        time.sleep(20)
        print "%s is %s" % (instance, instance.state)
    print "Public DNS: %s" % instance.dns_name
    instance.monitor()

    print "Waiting for Chef to finish bootstrapping the instance..."
    time.sleep(350)
    with settings(hosts=["%s:%d" % (instance.dns_name, env.ssh_port)]):
        get('/tmp/CHEF-STATUS', '/tmp/CHEF-STATUS')
    status = open("/tmp/CHEF-STATUS", "rb").read()
    if status[0] != "0":
        abort("Chef exited with non-zero status %s" % status)
    print("Chef bootstrapping completed successfully")

    with settings(hosts=["%s:%d" % (instance.dns_name, env.ssh_port)]):
        rechef()

    if (env.key_name == "production"
            and confirm("Attach to load balancer? Test before saying yes!",
            default=False)):
        status = ELB_CONNECTION.register_instances(env.load_balancer,
                [instance.id])
        print("Status of attaching %s to load balancer %s was %s" 
                % (instance.id, env.load_balancer, status))

def test(dir=None):
    if not dir:
        dir = env.root_dir
    with settings(root_dir=dir):
        return local('rake' % env, capture=False).return_code
