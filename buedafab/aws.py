"""Methods for interacting with Amazon's cloud servers. Uses the boto library to
connect to their API.
"""
from fabric.api import require, env
from fabric.decorators import runs_once

from buedafab.operations import exists
from buedafab.utils import sha_for_file

def collect_load_balanced_instances():
    """Return the fully-qualified domain names of the servers attached to an
    Elastic Load Balancer.

    Requires the env keys:
        
        load_balancer -- the ID of the load balancer, typically a chosen name
        ec2_connection -- an instance of boto.ec2.EC2Connection (set by default
                            if your shell environment has an AWS_ACCESS_KEY_ID
                            and AWS_SECRET_ACCESS_KEY defined
        elb_connection -- an instance of boto.ec2.elb.ELBConnection (again, set
                            by default if you have the right shell variables)
        env.ssh_port -- the SSH port used by the servers (has a default)
    """

    require('load_balancer')
    require('ec2_connection')
    require('elb_connection')
    instance_states = env.elb_connection.describe_instance_health(
            env.load_balancer)
    ids = []
    for instance in instance_states:
        print("Adding instance %s" % instance.instance_id)
        ids.append(instance.instance_id)
    instances = None
    instance_fqdns = []
    if ids:
        instances = env.ec2_connection.get_all_instances(instance_ids=ids)
        for instance in instances:
            if (instance.instances[0].update() == 'running'
                    and instance.instances[0].dns_name):
                instance_fqdns.append(
                    '%s:%d' % (instance.instances[0].dns_name, env.ssh_port))
    print("Found instances %s behind load balancer" % instance_fqdns)
    return instance_fqdns

@runs_once
def elb_add(instance=None):
    """Attach the instance defined by the provided instance ID (e.g. i-34927a9)
    to the application's Elastic Load Balancer.

    Requires the env keys:

        load_balancer -- the ID of the load balancer, typically a chosen name
        elb_connection -- an instance of boto.ec2.elb.ELBConnection (set
                            by default if you have the AWS shell variables)
    """
    require('load_balancer')
    require('elb_connection')
    status = env.elb_connection.register_instances(
            env.load_balancer, [instance])
    print("Status of attaching %s to load balancer %s was %s"
            % (instance, env.load_balancer, status))

@runs_once
def elb_remove(instance=None):
    """Detach the instance defined by the provided instance ID (e.g. i-34927a9)
    to the application's Elastic Load Balancer.

    Requires the env keys:

        load_balancer -- the ID of the load balancer, typically a chosen name
        elb_connection -- an instance of boto.ec2.elb.ELBConnection (set
                            by default if you have the AWS shell variables)
    """
    require('load_balancer')
    require('elb_connection')
    status = env.elb_connection.deregister_instances(
            env.load_balancer, [instance])
    print("Status of detaching %s from load balancer %s was %s"
            % (instance, env.load_balancer, status))

@runs_once
def conditional_s3_get(key, filename, sha=None):
    """Download a file from S3 to the local machine. Don't re-download if the
    sha matches (uses sha256).
    """
    sha_matches = False
    if exists(filename) and sha:
        sha_matches = sha_for_file(filename).startswith(sha)
        
    if not exists(filename) or not sha_matches:
        env.s3_key.key = key
        env.s3_key.get_contents_to_filename(filename)
