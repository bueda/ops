"""Utilities to determine the proper identifier for a deploy."""
from fabric.api import cd, require, local, env, prompt, settings, abort
from fabric.contrib.console import confirm
from fabric.decorators import runs_once
from fabric.colors import green, yellow
import os
import re

from buedafab.operations import (run, exists, conditional_mkdir,
        conditional_rm, chmod)
from buedafab import utils

def bootstrap_release_folders():
    """Create the target deploy directories if they don't exist and clone a
    fresh copy of the project's repository into each of the release directories.
    """
    require('path')
    require('deploy_group')
    conditional_mkdir(os.path.join(env.path, env.releases_root),
            env.deploy_group, 'g+w', use_sudo=True)
    with cd(os.path.join(env.path, env.releases_root)):
        first_exists = exists(env.release_paths[0])
        if not first_exists:
            run('git clone %s %s' % (env.scm, env.release_paths[0]),
                    forward_agent=True)
    with cd(os.path.join(env.path, env.releases_root)):
        if not exists(env.release_paths[1]):
            run('cp -R %s %s' % (env.release_paths[0], env.release_paths[1]))
    chmod(os.path.join(env.path, env.releases_root), 'g+w', use_sudo=True)

def make_pretty_release():
    """Assigns env.pretty_release to the commit identifier returned by 'git
    describe'.

    Requires the env keys:
        release -
        unit -
    """
    require('release')
    env.pretty_release = local('git describe %(release)s' % env, capture=True
            ).rstrip('\n')
    env.archive = '%(pretty_release)s-%(unit)s.tar' % env

def make_head_commit():
    """Assigns the commit SHA of the current git HEAD to env.head_commit.

    Requires the env keys:
        default_revision - the commit ref for HEAD
    """
    revision = local('git rev-list %(default_revision)s '
            '-n 1 --abbrev-commit --abbrev=7' % env, capture=True)
    env.head_commit = revision.rstrip('\n')

@runs_once
def make_release(release=None):
    """Based on the deployment type and any arguments from the command line,
    determine the proper identifier for the commit to deploy.

    If a tag is required (e.g. when in the production app environment), the
    deploy must be coming from the master branch, and cannot proceed without
    either creating a new tag or specifing and existing one.

    Requires the env keys:
        allow_no_tag - whether or not to require the release to be tagged in git
        default_revision - the commit ref for HEAD
    """
    require('allow_no_tag')
    require('default_revision')

    env.release = release
    env.tagged = False
    if not env.release or env.release == 'latest_tag':
        if not env.allow_no_tag:
            branch = utils.branch()
            if branch != "master":
                abort("Make sure to checkout the master branch and merge in the"
                        " development branch before deploying to production.")
            local('git checkout master', capture=True)
        description = local('git describe master' % env, capture=True
                ).rstrip('\n')
        if '-' in description:
            env.latest_tag = description[:description.find('-')]
        else:
            env.latest_tag = description
        if not re.match(env.version_pattern, env.latest_tag):
            env.latest_tag = None
        env.release = env.release or env.latest_tag
        env.commit = 'HEAD'
        if not env.allow_no_tag:
            if confirm(yellow("Tag this release?"), default=False):
                require('master_remote')
                from prettyprint import pp
                print(green("The last 5 tags were: "))
                tags = local('git tag | tail -n 20', capture=True)
                pp(sorted(tags.split('\n'), utils.compare_versions,
                        reverse=True))
                prompt("New release tag in the format vX.Y[.Z]?",
                        'tag',
                        validate=env.version_pattern)
                require('commit')
                local('git tag -s %(tag)s %(commit)s' % env)
                local('git push --tags %(master_remote)s' % env, capture=True)
                env.tagged = True
                env.release = env.tag
                local('git fetch --tags %(master_remote)s' % env, capture=True)
            else:
                print(green("Using latest tag %(latest_tag)s" % env))
                env.release = env.latest_tag
        else:
            make_head_commit()
            env.release = env.head_commit
            print(green("Using the HEAD commit %s" % env.head_commit))
    else:
        local('git checkout %s' % env.release, capture=True)
        env.tagged = re.match(env.version_pattern, env.release)
    make_pretty_release()

def conditional_symlink_current_release(deployed=False):
    """Swap the 'current' symlink to point to the new release if it doesn't
    point there already.

    Requires the env keys:
        pretty_release - set by make_pretty_release(), a commit identifier
        release_path - root target directory on the remote server
    """
    current_version = None
    if exists(utils.absolute_release_path()):
        with settings(cd(utils.absolute_release_path()), warn_only=True):
            current_version = run('git describe')
    if (not exists(utils.absolute_release_path())
            or deployed or current_version != env.pretty_release):
        _symlink_current_release(env.release_path)

def alternative_release_path():
    """Determine the release directory that is not currently in use.

    For example if the 'current' symlink points to the 'a' release directory,
    this method returns 'b'.

    Requires the env keys:
        release_paths - a tuple of length 2 with the release directory names
                            (defaults to 'a' and 'b')
    """

    if exists(utils.absolute_release_path()):
        current_release_path = run('readlink %s'
                % utils.absolute_release_path())
        if os.path.basename(current_release_path) == env.release_paths[0]:
            alternative = env.release_paths[1]
        else:
            alternative = env.release_paths[0]
        return alternative
    else:
        return env.release_paths[0]

def _symlink_current_release(next_release_path):
    with cd(os.path.join(env.path, env.releases_root)):
        conditional_rm(env.current_release_symlink)
        run('ln -fs %s %s' % (next_release_path, env.current_release_symlink))
