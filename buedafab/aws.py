from fabric.api import require, env
from fabric.decorators import runs_once

def collect_load_balanced_instances():
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
    require('load_balancer')
    require('elb_connection')
    status = env.elb_connection.register_instances(
            env.load_balancer, [instance])
    print("Status of attaching %s to load balancer %s was %s"
            % (instance, env.load_balancer, status))

@runs_once
def elb_remove(instance=None):
    require('load_balancer')
    require('elb_connection')
    status = env.elb_connection.deregister_instances(
            env.load_balancer, [instance])
    print("Status of detaching %s from load balancer %s was %s"
            % (instance, env.load_balancer, status))
