from fabric.api import require, env
import os

from buedafab import aws
from buedafab.operations import put

def _not_localhost():
    if (hasattr(env, 'pip_requirements')
            and hasattr(env, 'pip_requirements_production')):
        env.pip_requirements += env.pip_requirements_production
    put(os.path.join(os.path.abspath(os.path.dirname(__file__)),
            'files', 'ssh_config'), '~/.ssh/config')

def development():
    """
    [Env] Development server environment
    """
    _not_localhost()
    if len(env.hosts) == 0:
        env.hosts = ['dev.bueda.com:%(ssh_port)d' % env]
    env.allow_no_tag = True
    env.deployment_type = "DEV"

def staging():
    """
    [Env] Staging server environment
    """
    _not_localhost()
    if len(env.hosts) == 0:
        env.hosts = ['dev.bueda.com:%(ssh_port)d' % env]
    env.allow_no_tag = True
    env.deployment_type = "STAGING"
    env.path += '-staging'

def production():
    """
    [Env] Production servers. Stricter requirements.
    """
    _not_localhost()
    env.allow_no_tag = False
    env.deployment_type = "PRODUCTION"
    if hasattr(env, 'load_balancer'):
        if len(env.hosts) == 0:
            env.hosts = aws.collect_load_balanced_instances()
    env.default_revision = '%(master_remote)s/master' % env

def localhost(deployment_type=None):
    """
    [Env] Bootstrap the localhost - can be either dev, production or staging.
    """
    require('root_dir')
    if len(env.hosts) == 0:
        env.hosts = ['localhost']
    env.allow_no_tag = True
    env.deployment_type = deployment_type
    if deployment_type is None:
        deployment_type = "SOLO"
    env.deployment_type = deployment_type
    if env.deployment_type == "STAGING":
        env.path += '-staging'
    if (hasattr(env, 'pip_requirements')
            and hasattr(env, 'pip_requirements_dev')):
        env.pip_requirements += env.pip_requirements_dev

def django_development():
    development()
    env.extra_fixtures += ["dev"]
    env.crontab = os.path.join('scripts', 'crontab', 'development')

def django_staging():
    staging()
    env.crontab = os.path.join('scripts', 'crontab', 'production')

def django_production():
    production()
    env.crontab = os.path.join('scripts', 'crontab', 'production')

def django_localhost(deployment_type=None):
    localhost(deployment_type)

