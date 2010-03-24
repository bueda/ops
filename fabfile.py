#!/usr/bin/env python
import os
import boto
from fabric.api import *
from fab_shared import (_find_unit_root, _development, _production, _clone,
        _make_release, _upload_to_s3, restart_webserver, rollback)

env.unit = "chef"
env.user_data = "deployment/chef.user-data"
env.root_dir = _find_unit_root(os.path.abspath(os.path.dirname(__file__)))

def development():
    """
    [Env] Sets environment for development server.
    """
    _development()
    env.security_groups = ["development", "ssh", "database-client"]
    env.key_name = "development"
    env.chef_configs = ["common.json", "common-web.json", "dev.json",
            "lda.json", "solr.json"]

def production():
    """
    [Env] Sets environment for production servers behind load balancer.
    """
    _production()
    env.security_groups = ["production", "ssh", "database-client"]
    env.key_name = "production"
    env.chef_configs = ["common.json", "common-web.json", "production.json"]

def deploy(commit=None, release=None):
    """
    Deploy a specific commit, tag or HEAD to all servers and/or S3.
    """
    require('hosts', provided_by = [development, production])
    require('unit')

    env.scratch_path = '/tmp/%(unit)s' % env
    _clone()
    if test():
        abort("Tests did not pass")
    _make_release(commit, release)
    if confirm("Upload to S3?", default=env.upload_to_s3):
        _upload_to_s3()
    if confirm("Re-Chef?", default=True):
        rechef(release=env.release)

def rechef(release=None):
    """
    Run the latest commit of the Chef cookbook on all servers.
    """
    require('chef_configs', provided_by=[development, production])
    require('unit')
    if (not release
            and confirm("Re-chef with production cookbook?", default=True)):
        S3_KEY.key = '%(unit)s.tar.gz' % env
        S3_KEY.get_contents_to_filename('/tmp/%(unit)s.tar.gz' % env)
    else:
        if not release:
            env.release = prompt("Chef commit or tag?", default='HEAD')
        _clone()
        _make_archive()
        local('mv /tmp/%(release)s-%(unit)s.tar.gz /tmp/%(unit)s.tar.gz' % env)
    put('/tmp/%(unit)s.tar.gz' % env, '/tmp/', mode=0777)
    run('rm -rf %(scratch_path)s*' % env)
    run('tar -xzf /tmp/%(unit)s.tar.gz -C /tmp' % env)
    _run_chef_solo('base')
    for config in env.chef_configs:
        _run_chef_solo(config)
    local('rm -rf %(scratch_path)s*' % env)

def _run_chef_solo(config):
    with settings(config=config, warn_only=True):
        result = sudo("""
            cd %(scratch_path)s;
            /var/lib/gems/1.8/bin/chef-solo \
                -j %(scratch_path)s/config/%(config)s \
                -c %(scratch_path)s/config/solo.rb
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

    image = ec2_connection.get_image(env.ami)
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
    #TODO this may be too long now that the base config is much smaller
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
        status = elb_connection.register_instances(env.load_balancer,
                [instance.id])
        print("Status of attaching %s to load balancer %s was %s" 
                % (instance.id, env.load_balancer, status))

def test():
    require('scratch_path')
    require('cloned')
    with cd(env.scratch_path):
        return local('rake' % env, capture=False).return_code
