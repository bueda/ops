"""Relatively self-contained, simple Fabric commands."""
from fabric.api import require, env, local, warn, settings, cd
import os

from buedafab.operations import run, exists, conditional_rm, sed, sudo
from buedafab import environments, deploy, utils

def setup():
    """A shortcut to bootstrap or update a virtualenv with the dependencies for
    this project. Installs the `common.txt` and `dev.txt` pip requirements and
    initializes/updates any git submodules.

    setup() also supports the concept of "private packages" - i.e. Python
    packages that are not available on PyPi but require some local compilation
    and thus don't work well as git submodules. It can either download a tar
    file of the package from S3 or clone a git repository, build and install the
    package.

    Any arbitrary functions in env.extra_setup_tasks will also be run from
    env.root_dir.
    """

    environments.localhost()
    with settings(virtualenv=None):
        for package in deploy.packages._read_private_requirements():
            deploy.packages._install_private_package(*package)
    deploy.packages._install_manual_packages(env.root_dir)
    deploy.packages._install_pip_requirements(env.root_dir)

    with cd(env.root_dir):
        local('git submodule update --init --recursive')
        for task in env.extra_setup_tasks:
            task()


def enable():
    """Toggles a value True. Used in 'toggle' commands such as
    maintenancemode().
    """
    env.toggle = True

def disable():
    """Toggles a value False. Used in 'toggle' commands such as
    maintenancemode().
    """
    env.toggle = False

def maintenancemode():
    """If using the maintenancemode app
    (https://github.com/jezdez/django-maintenancemode), this command will toggle
    it on and off. It finds the `MAINTENANCE_MODE` variable in your
    `settings.py` on the remote server, toggles its value and restarts the web
    server.

    Requires the env keys:

        toggle - set by enable() or disable(), indicates whether we should turn
                    maintenance mode on or off.
        settings - relative path from the project root to the settings.py file
        current_release_path - path to the current release on the remote server
    """
    require('toggle', provided_by=[enable, disable])
    require('settings')
    require('current_release_path')

    settings_file = os.path.join(utils.absolute_release_path(), env.settings)
    if exists(settings_file):
        sed(settings_file, '(MAINTENANCE_MODE = )(False|True)',
                '\\1%(toggle)s' % env)
        restart_webserver()
    else:
        warn('Settings file %s could not be found' % settings_file)

def rollback():
    """Swaps the deployed version of the app to the previous version.

    Requires the env keys:

        path - root deploy target for this app
        releases_root - subdirectory that stores the releases
        current_release_symlink - name of the symlink pointing to the currently
                                    deployed version
        Optional:

        crontab - relative path from the project root to a crontab to install
        deploy_user - user that should run the crontab
    """
    require('path')
    require('releases_root')
    require('current_release_symlink')
    require('crontab')
    require('deploy_user')
    with cd(os.path.join(env.path, env.releases_root)):
        previous_link = deploy.release.alternative_release_path()
        conditional_rm(env.current_release_symlink)
        run('ln -fs %s %s' % (previous_link, env.current_release_symlink))
    deploy.cron.conditional_install_crontab(utils.absolute_release_path(),
            env.crontab, env.deploy_user)
    restart_webserver()

def restart_webserver(hard_reset=False):
    """Restart the Gunicorn application webserver.

    Requires the env keys:

        unit - short name of the app, assuming /etc/init.d/%(unit)s is the
                server process init.d script
    """
    require('unit')
    with settings(warn_only=True):
        sudo('/etc/init.d/%(unit)s restart' % env)

def rechef():
    """Run the latest Chef cookbooks on all servers."""
    sudo('chef-client')
