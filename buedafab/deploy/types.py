from fabric.api import warn, cd, require, local, env
import os

from buedafab.operations import run, sed
from buedafab import celery, db, commands, notify, testing, utils
from buedafab import deploy

# TODO why isn't skip tests used? where did test running go?
def _git_deploy(release, skip_tests):
    starting_branch = local("git symbolic-ref HEAD 2>/dev/null "
            "| awk -F/ {'print $NF'}")
    local('git push %(master_remote)s' % env)
    deploy.release.make_release(release)

    require('pretty_release')
    require('path')
    require('wsgi')
    require('hosts')

    deployed = False
    hard_reset = False
    deployed_versions = {}
    deploy.release.bootstrap_release_folders()
    for release_path in env.release_paths:
        with cd(os.path.join(env.path, release_path)):
            deployed_versions[run('git describe')] = release_path
    if env.pretty_release not in deployed_versions:
        env.release_path = deploy.release.alternative_release_path()
        with cd(os.path.join(env.path, env.release_path)):
            run('git fetch %(master_remote)s' % env, forward_agent=True)
            run('git reset --hard %(release)s' % env)
            run('git submodule init')
            run('git submodule update', forward_agent=True)
        sed(os.path.join(env.path, env.release_path, env.wsgi),
                'PRODUCTION', env.deployment_type)
        deploy.cron.conditional_install_crontab(
                os.path.join(env.path, env.release_path), env.crontab,
                env.deploy_user)
        deployed = True
    else:
        warn("%(pretty_release)s is already deployed" % env)
        env.release_path = deployed_versions[env.pretty_release]
        with cd(os.path.join(env.path, env.release_path)):
            run('git submodule init')
            run('git submodule update', forward_agent=True)
    hard_reset = deploy.packages.install_requirements(deployed)
    local('git checkout %s' % starting_branch)
    return deployed, hard_reset

def _webpy_deploy(release=None, skip_tests=None):
    require('hosts')
    require('path')
    require('unit')
    require('wsgi')

    env.test_runner = testing.webpy_test_runner

    deployed, hard_reset = _git_deploy(release, skip_tests)
    deploy.release.conditional_symlink_current_release(deployed)
    commands.restart_webserver(hard_reset)
    notify.hoptoad_deploy(deployed)

def _django_deploy(release=None, skip_tests=None):
    require('hosts')
    require('path')
    require('unit')
    require('migrate')
    require('wsgi')
    require('root_dir')

    env.test_runner = testing.django_test_runner

    utils.store_deployed_version()
    deployed, hard_reset = _git_deploy(release, skip_tests)
    db.update_db(deployed)
    db.migrate(deployed)
    db.load_data()
    deploy.release.conditional_symlink_current_release(deployed)
    celery.update_and_restart_celery()
    commands.restart_webserver(hard_reset)
    notify.hoptoad_deploy(deployed)
    notify.campfire_notify(deployed)
