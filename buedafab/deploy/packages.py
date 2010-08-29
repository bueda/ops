from fabric.api import warn, cd, require, local, env, settings
from fabric.contrib.console import confirm
import os

from buedafab.operations import run, exists, put
from buedafab import deploy

def _read_private_requirements():
    for private_requirements in env.private_requirements:
        with open(
                os.path.join(env.scratch_path, private_requirements), 'r') as f:
            for requirement in f:
                yield requirement.strip().split('==')

def _install_private_package(package, scm=None, release=None):
    scratch_path = os.path.join('/tmp', '%s-%s' % (package, env.time_now))
    archive_path = '%s.tar' % scratch_path

    if not scm:
        require('s3_key')
        env.s3_key.key = '%s.tar' % package
        env.s3_key.get_contents_to_filename(archive_path)
    else:
        if 'release' not in env:
            env.release = release
        release = release or 'HEAD'
        if 'pretty_release' in env:
            original_pretty_release = env.pretty_release
        else:
            original_pretty_release = None
        if 'archive' in env:
            original_archive = env.archive
        else:
            original_archive = None
        with settings(unit=package, scm=scm, release=release,
                scratch_path=scratch_path):
            if not os.path.exists(env.scratch_path):
                local('git clone %(scm)s %(scratch_path)s' % env)
            deploy.utils.make_archive()
            local('mv %s %s' % (os.path.join(env.scratch_path, env.archive),
                    archive_path))
        if original_pretty_release:
            env.pretty_release = original_pretty_release
        if original_archive:
            env.archive = original_archive
    put(archive_path, '/tmp')
    if env.virtualenv is not None:
        require('release_path')
        require('path')
        with cd(env.release_path):
            run('%s -E %s -s %s'
                    % (env.pip_install_command, env.virtualenv, archive_path))
    else:
        run('%s -s %s' % (env.pip_install_command, archive_path))


def _install_pip_requirements(path=None):
    if not path:
        require('pretty_release')
        require('virtualenv')
        require('pip_requirements')
        path = env.release_path
    if not env.pip_requirements:
        warn("No pip requirements files found -- %(pip_requirements)s"
                % env)
        return
    with cd(path):
        for requirements_file in env.pip_requirements:
            run('%s -E %s -s -r %s' % (env.pip_install_command,
                    env.virtualenv, requirements_file))

def install_requirements(deployed=False):
    require('path')
    require('release_path')
    require('virtualenv')

    with settings(cd(env.release_path), warn_only=True):
        virtualenv_exists = exists('%(virtualenv)s' % env)
    if (deployed or not virtualenv_exists or
            confirm("Reinstall Python dependencies?", default=True)):
        _install_pip_requirements()
        for package in _read_private_requirements():
            _install_private_package(*package)
        return True
    return False
