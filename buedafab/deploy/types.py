"""Deploy commands for applications following Bueda's boilerplate layouts."""
from fabric.api import warn, cd, require, local, env, settings, abort
from fabric.colors import green, red
import os

from buedafab.operations import run, put, chmod
from buedafab import celery, db, tasks, notify, testing, utils
from buedafab import deploy

def _git_deploy(release, skip_tests):
    starting_branch = utils.branch()
    print(green("Deploying from git branch '%s'" % starting_branch))
    # Ideally, tests would run on the version you are deploying exactly.
    # There is no easy way to require that without allowing users to go
    # through the entire tagging process before failing tests.
    if not skip_tests and testing.test():
        abort(red("Unit tests did not pass -- must fix before deploying"))

    local('git push %(master_remote)s' % env, capture=True)
    deploy.release.make_release(release)

    require('pretty_release')
    require('path')
    require('hosts')

    print(green("Deploying version %s" % env.pretty_release))
    put(os.path.join(os.path.abspath(os.path.dirname(__file__)),
            '..', 'files', 'ssh_config'), '.ssh/config')

    deployed = False
    hard_reset = False
    deployed_versions = {}
    deploy.release.bootstrap_release_folders()
    for release_path in env.release_paths:
        with cd(os.path.join(env.path, env.releases_root, release_path)):
            deployed_versions[run('git describe')] = release_path
    print(green("The host '%s' currently has the revisions: %s"
        % (env.host, deployed_versions)))
    if env.pretty_release not in deployed_versions:
        env.release_path = os.path.join(env.path, env.releases_root,
                deploy.release.alternative_release_path())
        with cd(env.release_path):
            run('git fetch %(master_remote)s' % env, forward_agent=True)
            run('git reset --hard %(release)s' % env)
        deploy.cron.conditional_install_crontab(env.release_path, env.crontab,
                env.deploy_user)
        deployed = True
    else:
        warn(red("%(pretty_release)s is already deployed" % env))
        env.release_path = os.path.join(env.path, env.releases_root,
                deployed_versions[env.pretty_release])
    with cd(env.release_path):
        run('git submodule update --init --recursive', forward_agent=True)
    hard_reset = deploy.packages.install_requirements(deployed)
    deploy.utils.run_extra_deploy_tasks(deployed)
    local('git checkout %s' % starting_branch, capture=True)
    chmod(os.path.join(env.path, env.releases_root), 'g+w', use_sudo=True)
    return deployed, hard_reset

def default_deploy(release=None, skip_tests=None):
    """Deploy a project according to the methodology defined in the README."""
    require('hosts')
    require('path')
    require('unit')

    env.test_runner = testing.webpy_test_runner

    utils.store_deployed_version()
    deployed, hard_reset = _git_deploy(release, skip_tests)
    deploy.release.conditional_symlink_current_release(deployed)
    tasks.restart_webserver(hard_reset)
    with settings(warn_only=True):
        notify.hoptoad_deploy(deployed)
        notify.campfire_notify(deployed)

webpy_deploy = default_deploy
tornado_deploy = default_deploy

def django_deploy(release=None, skip_tests=None):
    """Deploy a Django project according to the methodology defined in the
    README.

    Beyond the default_deploy(), this also updates and migrates the database,
    loads extra database fixtures, installs an optional crontab as well as
    celeryd.
    """
    require('hosts')
    require('path')
    require('unit')
    require('migrate')
    require('root_dir')

    env.test_runner = testing.django_test_runner

    utils.store_deployed_version()
    deployed, hard_reset = _git_deploy(release, skip_tests)
    db.update_db(deployed)
    db.migrate(deployed)
    db.load_data()
    deploy.release.conditional_symlink_current_release(deployed)
    celery.update_and_restart_celery()
    tasks.restart_webserver(hard_reset)
    notify.hoptoad_deploy(deployed)
    notify.campfire_notify(deployed)
    print(green("%(pretty_release)s is now deployed to %(deployment_type)s"
        % env))
