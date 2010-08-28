from fabric.api import require, env
import os

from buedafab import environments, aws

def _not_production():
    env.scratch_path = env.root_dir

def _not_localhost():
    if (hasattr(env, 'pip_requirements')
            and hasattr(env, 'pip_requirements_production')):
        env.pip_requirements += env.pip_requirements_production

def development():
    """
    [Env] Development server environment
    """
    _not_production()
    _not_localhost()
    if len(env.hosts) == 0:
        env.hosts = ['dev.bueda.com:%(ssh_port)d' % env]
    env.allow_no_tag = True
    env.deployment_type = "DEV"

def staging():
    """
    [Env] Staging server environment
    """
    _not_production()
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
    env.scratch_path = os.path.join('/tmp','%s-%s' % (env.unit, env.time_now))
    env.default_revision = '%(master_remote)s/master' % env

def localhost(deployment_type=None):
    """
    [Env] Bootstrap the localhost - can be either dev, production or staging.
    """
    require('root_dir')
    _not_production()
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
    environments.development()
    env.extra_fixtures += ["dev"]
    env.crontab = os.path.join('scripts', 'crontab', 'development')

def django_staging():
    environments.staging()
    env.crontab = os.path.join('scripts', 'crontab', 'production')

def django_production():
    environments.production()
    env.crontab = os.path.join('scripts', 'crontab', 'production')

def django_localhost(deployment_type=None):
    environments.localhost(deployment_type)

