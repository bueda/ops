"""Application environments, which determine the servers, database and other
conditions for deployment.
"""
from fabric.api import require, env
import os

from buedafab import aws

def _not_localhost():
    """All non-localhost environments need to install the "production" pip
    requirements, which typically includes the Python database bindings.
    """
    if (hasattr(env, 'pip_requirements')
            and hasattr(env, 'pip_requirements_production')):
        env.pip_requirements += env.pip_requirements_production

def development():
    """[Env] Development server environment

    - Sets the hostname of the development server (using the default ssh port)
    - Sets the app environment to "DEV"
    - Permits developers to deploy without creating a tag in git
    """
    _not_localhost()
    if len(env.hosts) == 0:
        env.hosts = ['dev.bueda.com:%(ssh_port)d' % env]
    env.allow_no_tag = True
    env.deployment_type = "DEV"
    if (hasattr(env, 'pip_requirements')
            and hasattr(env, 'pip_requirements_dev')):
        env.pip_requirements += env.pip_requirements_dev

def staging():
    """[Env] Staging server environment

    - Sets the hostname of the staging server (using the default ssh port)
    - Sets the app environment to "STAGING"
    - Permits developers to deploy without creating a tag in git
    - Appends "-staging" to the target directory to allow development and
        staging servers to be the same machine
    """
    _not_localhost()
    if len(env.hosts) == 0:
        env.hosts = ['dev.bueda.com:%(ssh_port)d' % env]
    env.allow_no_tag = True
    env.deployment_type = "STAGING"
    env.path += '-staging'

def production():
    """[Env] Production servers. Stricter requirements.

    - Collects production servers from the Elastic Load Balancer specified by
        the load_balancer env attribute
    - Sets the app environment to "PRODUCTION"
    - Requires that developers deploy from the 'master' branch in git
    - Requires that developers tag the commit in git before deploying
    """
    _not_localhost()
    env.allow_no_tag = False
    env.deployment_type = "PRODUCTION"
    if hasattr(env, 'load_balancer'):
        if len(env.hosts) == 0:
            env.hosts = aws.collect_load_balanced_instances()
    env.default_revision = '%(master_remote)s/master' % env

def localhost(deployment_type=None):
    """[Env] Bootstrap the localhost - can be either dev, production or staging.

    We don't really use this anymore except for 'fab setup', and even there it
    may not be neccessary. It was originally intended for deploying
    automatically with Chef, but we moved away from that approach.
    """
    require('root_dir')
    if len(env.hosts) == 0:
        env.hosts = ['localhost']
    env.allow_no_tag = True
    env.deployment_type = deployment_type
    env.virtualenv = os.environ.get('VIRTUAL_ENV', 'env')
    if deployment_type is None:
        deployment_type = "SOLO"
    env.deployment_type = deployment_type
    if env.deployment_type == "STAGING":
        env.path += '-staging'
    if (hasattr(env, 'pip_requirements')
            and hasattr(env, 'pip_requirements_dev')):
        env.pip_requirements += env.pip_requirements_dev

def django_development():
    """[Env] Django development server environment

    In addition to everything from the development() task, also:

        - loads any database fixtures named "dev"
        - loads a crontab from the scripts directory (deprecated at Bueda)
    """
    development()
    env.extra_fixtures += ["dev"]
    env.crontab = os.path.join('scripts', 'crontab', 'development')

def django_staging():
    """[Env] Django staging server environment

    In addition to everything from the staging() task, also:

        - loads a production crontab from the scripts directory (deprecated at
                Bueda)
    """
    staging()
    env.crontab = os.path.join('scripts', 'crontab', 'production')

def django_production():
    """[Env] Django production server environment

    In addition to everything from the production() task, also:

        - loads a production crontab from the scripts directory (deprecated at
                Bueda)
    """
    production()
    env.crontab = os.path.join('scripts', 'crontab', 'production')
